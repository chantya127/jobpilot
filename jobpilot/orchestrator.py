"""Runs the queue: N browser workers, one headless `claude -p` job-applier session per job.

Replaces the old /research coordinator skill: queue filtering, one job per worker, never two jobs on the same portal
tenant at once, parsing the worker's one-line result, NEEDS (-> dashboard inbox) and LEARNED (-> portals-local.md).
"""
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.parse

from . import browser, config, db, profile

# Worker sessions must not load the user's personal Claude Code setup (hooks that rewrite every Bash command, MCP
# servers that may hang on connect, skills/plugins): it slows every step and bloats the context.
ISOLATION = ["--setting-sources", "project,local", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
             "--disable-slash-commands"]

RESULT_RE = re.compile(r"^\s*`?(applied|ready-for-review|pending-user|blocked|skipped)\s*\|", re.I | re.M)


def tenant(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    host = p.netloc.lower()
    # greenhouse/lever/ashby boards host many companies: the tenant is the first path segment / ?for=
    q = urllib.parse.parse_qs(p.query)
    if "for" in q:
        return host + "/" + q["for"][0]
    if any(h in host for h in ("greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com")):
        return host + "/" + (p.path.strip("/").split("/") or [""])[0]
    return host


def prefilter(job, s) -> tuple[str, str] | None:
    """Cheap checks before spending an agent session. Returns (status, note) to log instead of dispatching."""
    url = job["url"]
    low = url.lower()
    for name in s.get("avoid_companies", []):
        n = re.sub(r"[^a-z0-9]", "", name.lower())
        if n and n in re.sub(r"[^a-z0-9]", "", urllib.parse.urlsplit(low).netloc + urllib.parse.urlsplit(low).path):
            return "skipped", f"Avoided company: {name}"
    if s.get("skip_easy_apply", True) and re.search(r"linkedin\.com/jobs/view/", low):
        return "pending-user", "LinkedIn job page: open it and use the company's own Apply link (Easy Apply is never automated)"
    if s.get("stack_accept"):
        for lang in s.get("stack_skip", []):
            token = re.escape(lang.lower()).replace(r"\#", "#")
            if re.search(rf"(?<![a-z]){token}(?![a-z])", urllib.parse.unquote(low).replace("-", " ")):
                return "skipped", f"Stack mismatch: {lang}"
    return None


def render_prompt(job, worker: int, s: dict) -> str:
    tpl = (config.engine_dir() / "agents" / "job-applier.md").read_text()
    if s.get("auto_submit"):
        mode = ("AUTO-SUBMIT is ON. The user has pre-approved submitting, creating portal accounts with their "
                "secrets.env credentials, and ticking required consent/terms boxes. Do not ask before submitting.")
        finish = ('Confirm success from the URL or page text ("Thank you", /confirmation, "submitted successfully"). '
                  "If you can't confirm it, use pending-user with what you saw.")
    else:
        mode = ("REVIEW mode. Create a portal account if the form needs one and tick required consents, fill and verify "
                "every field, but do NOT click the final Submit button. The user will review and submit it themselves. "
                "A review lock in the page blocks final submits (you'll see a '🔒 JobPilot review lock' banner): never "
                "click that banner or try to get around it. Don't press Enter inside text fields of the final form "
                "(Enter can submit it); use Tab to move on. If `$AB eval 'window.__jp_blocked||0'` is above 0, a "
                "submit was blocked: stop, it's ready for review.")
        finish = (f"Stop on the page with the final Submit button, with every required field filled and no errors. "
                  f"Use status ready-for-review with `NEEDS: review and submit in worker {worker} tab <id>`.")
    otp_line = ("enabled: use `otp` as described in portals.md." if s.get("otp_enabled")
                else "disabled: when a portal emails a code, stop at the code prompt and return pending-user.")
    if s.get("stack_accept"):
        accept = ", ".join(s["stack_accept"])
        stack_line = f"Applicant's stack: {accept}."
        check = (f"Read the title + JD. If the role's primary/required language is one the applicant doesn't use "
                 f"(e.g. {', '.join(s.get('stack_skip', []))}) and {accept} is not an accepted alternative, don't apply: "
                 'jlog ... skipped "Stack mismatch: <lang>", close the tab, report skipped. Language-agnostic roles are fine.')
    else:
        stack_line, check = "", "No stack filter is set: skip this step."
    if s.get("avoid_companies"):
        check += (" Also, if the hiring company is one of: " + ", ".join(s["avoid_companies"])
                  + ' → jlog ... skipped "Avoided company", close the tab, report skipped.')
    vals = {
        "JP_HOME": str(config.HOME), "JP_ENGINE": str(config.engine_dir()), "WORKER": str(worker),
        "URL": job["url"], "MODE_LINE": mode, "OTP_LINE": otp_line, "STACK_LINE": stack_line,
        "STACK_CHECK": check, "FINISH_STEP": finish,
        "GUIDANCE": (f"User's instructions for this run (follow them; they override the defaults below except the "
                     f"hand-back rules): {s['guidance']}") if s.get("guidance") else "",
    }
    for k, v in vals.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def parse_result(text: str) -> dict:
    """`<status> | <Company> | <Role> | <note> [| NEEDS: ...] [| LEARNED: ...]` -> dict."""
    lines = [l for l in (text or "").splitlines() if RESULT_RE.match(l)]
    if not lines:
        return {"status": "pending-user", "company": "", "role": "", "note": "Worker ended without a result line",
                "needs": (text or "")[-300:], "learned": ""}
    parts = [p.strip().strip("`") for p in lines[-1].split("|")]
    out = {"status": parts[0].lower(), "company": parts[1] if len(parts) > 1 else "",
           "role": parts[2] if len(parts) > 2 else "", "note": "", "needs": "", "learned": ""}
    rest = []
    for p in parts[3:]:
        if p.upper().startswith("NEEDS:"):
            out["needs"] = p[6:].strip()
        elif p.upper().startswith("LEARNED:"):
            out["learned"] = p[8:].strip()
        else:
            rest.append(p)
    out["note"] = " | ".join(rest)
    return out


def summarize_event(ev: dict) -> list[tuple[str, str]]:
    """stream-json event -> [(kind, text)] for the live panel."""
    out = []
    if ev.get("type") == "assistant":
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") == "tool_use":
                inp = c.get("input", {})
                desc = inp.get("description") or inp.get("command") or inp.get("file_path") or inp.get("pattern") or ""
                desc = re.sub(r'^cd "?[^&]*"? && source "?[^&]*jobkit\.sh"? \d+ && ', "", str(desc))
                out.append(("tool", f"{c.get('name')}: {desc[:300]}"))
            elif c.get("type") == "text" and c.get("text", "").strip():
                out.append(("text", c["text"].strip()[:600]))
    elif ev.get("type") == "result":
        cost = ev.get("total_cost_usd")
        out.append(("result", (ev.get("result") or "")[:1500] + (f"  (${cost:.2f})" if cost else "")))
    return out


class Worker:
    def __init__(self, n):
        self.n = n
        self.proc = None
        self.job_id = None
        self.started = None
        self.step = ""
        self.killed = False
        self.last_job = None      # id of the job this worker finished most recently (its log stays visible)
        self.agent = None         # number of the agent session currently using this window (1, 2, 3… per run)


class Orchestrator:
    def __init__(self):
        self.lock = threading.Lock()
        self.workers: dict[int, Worker] = {}
        self.running = False
        self.thread = None
        self.caffeinate = None
        self.message = ""
        self.run = None            # {"started", "jobs": {job_id: status}} while a run is active
        self.end_reason = ""
        try:
            self.last_run = json.loads((config.HOME / "last_run.json").read_text())
        except Exception:
            self.last_run = None

    # ---------------------------------------------------------------- run summary
    def _record(self, job_id, status):
        if self.run is not None:
            self.run["jobs"][job_id] = status

    def _maybe_finalize(self):
        """When a run is over (not running, no worker busy): save its summary and reset to the initial state."""
        with self.lock:
            if self.run is None or self.running or any(w.proc for w in self.workers.values()):
                return
            jobs = self.run["jobs"]
            counts = {}
            for st in jobs.values():
                counts[st] = counts.get(st, 0) + 1
            rows, tot = [], {"tokens": 0, "cost": 0.0, "seconds": 0}
            agent_of = {o["id"]: o.get("agent") for o in self.run.get("order", [])}
            for jid, st in jobs.items():
                j = db.get(jid)
                if j:
                    s = db.stats_of(j)
                    tot["tokens"] += sum(s.get(k, 0) or 0 for k in ("input", "output", "cache_read", "cache_write"))
                    tot["cost"] += s.get("cost") or 0
                    tot["seconds"] += s.get("seconds") or 0
                    rows.append({"id": jid, "status": st, "agent": agent_of.get(jid), "stats": s, "role": j["role"],
                                 "company": j["company"] or urllib.parse.urlsplit(j["url"]).netloc})
            started = self.run["started"]
            self.last_run = {"started": time.strftime("%d %b, %H:%M", time.localtime(started)),
                             "duration": int(time.time() - started), "reason": self.end_reason or "Run ended",
                             "counts": counts, "total": len(jobs), "jobs": rows[-50:], "totals": tot,
                             "agents": self.run.get("agents", 0)}
            try:
                (config.HOME / "last_run.json").write_text(json.dumps(self.last_run))
            except OSError:
                pass
            self.run = None
            for w in self.workers.values():
                w.last_job = None
        self._stop_caffeinate_if_idle()

    # ---------------------------------------------------------------- control
    def start(self):
        with self.lock:
            if self.running:
                return
            s = config.load_settings()
            problems = preflight(s)
            if problems:
                self.message = "Can't start: " + "; ".join(problems)
                return
            n = max(1, min(int(s.get("workers", 2)), 4))
            browser.write_wrappers(n)
            profile.render()
            self.workers = {i: self.workers.get(i) or Worker(i) for i in range(1, n + 1)}
            self.running = True
            self.message = ""
            self.end_reason = ""
            # Every Start is a fresh run with new agents (one new Claude session per job).
            self.run = {"started": time.time(), "jobs": {}, "order": [], "agents": 0}
            self.last_run = None
            for w in self.workers.values():
                w.last_job = None
            if platform.system() == "Darwin" and shutil.which("caffeinate"):
                self.caffeinate = subprocess.Popen(["caffeinate", "-dims"])
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def pause(self, reason: str = "Paused by you"):
        """Stop handing out new jobs; running workers finish their current job, then the run summary is saved."""
        with self.lock:
            if self.running:
                self.end_reason = reason
            self.running = False
        self._maybe_finalize()

    def stop(self):
        """Stop everything now; interrupted jobs go back to the queue."""
        self.pause("Stopped by you")
        self.end_reason = "Stopped by you"
        for w in list(self.workers.values()):
            self.kill(w.n)
        self._maybe_finalize()

    def kill(self, n: int, requeue: bool = True):
        """Stop one worker. requeue=False parks the job as pending-user so a running loop doesn't pick it again."""
        w = self.workers.get(n)
        if not w or not w.proc:
            return
        job_id = w.job_id
        w.killed = True
        try:
            os.killpg(w.proc.pid, signal.SIGTERM)
        except Exception:
            w.proc.terminate()
        if job_id:
            self._record(job_id, "stopped")
            if requeue:
                db.set_status(job_id, "queued", worker=None)
                db.add_event(job_id, n, "info", "Stopped by user; back in the queue")
            else:
                db.set_status(job_id, "pending-user", notes="Stopped by user", needs="Stopped by user: retry when ready")
                db.add_event(job_id, n, "info", "Stopped by user")

    def _stop_caffeinate_if_idle(self):
        if self.caffeinate and not any(w.proc for w in self.workers.values()) and not self.running:
            self.caffeinate.terminate()
            self.caffeinate = None

    # ---------------------------------------------------------------- loop
    def _loop(self):
        while self.running:
            s = config.load_settings()
            busy_tenants = {tenant(db.get(w.job_id)["url"]) for w in self.workers.values() if w.job_id and db.get(w.job_id)}
            for w in self.workers.values():
                if not self.running or w.proc:
                    continue
                job = self._next_job(s, busy_tenants)
                if not job:
                    break
                busy_tenants.add(tenant(job["url"]))
                self._spawn(w, job, s)
            if not db.queued() and not any(w.proc for w in self.workers.values()):
                self.end_reason = "Queue finished"
                self.running = False
                break
            time.sleep(2)
        self._maybe_finalize()

    def _next_job(self, s, busy_tenants):
        for job in db.queued():
            pre = prefilter(job, s)
            if pre:
                db.set_status(job["id"], pre[0], notes=pre[1])
                continue
            if tenant(job["url"]) in busy_tenants:
                continue
            return job
        return None

    def _spawn(self, w: Worker, job, s):
        prompt = render_prompt(job, w.n, s)
        env = dict(os.environ, JP_HOME=str(config.HOME), JP_ENGINE=str(config.engine_dir()), JP_PY=sys.executable,
                   JP_REVIEW="0" if s.get("auto_submit") else "1")
        cmd = ["claude", "-p", prompt, "--model", s.get("model") or "sonnet",
               "--output-format", "stream-json", "--verbose",
               "--tools", "Bash", "Read", "Grep", "Glob",          # the only tools that exist for the worker
               "--allowedTools", "Bash", "Read", "Grep", "Glob",   # ...and they run without permission prompts
               *ISOLATION]
        if self.run is not None:
            self.run["agents"] = self.run.get("agents", 0) + 1
            w.agent = self.run["agents"]
            self.run.setdefault("order", []).append({"id": job["id"], "worker": w.n, "agent": w.agent,
                                                     "started": time.time()})
        db.set_status(job["id"], "running", worker=w.n, needs="")
        db.add_event(job["id"], w.n, "info", f"Agent #{w.agent or '?'} started in window {w.n}")
        log = open(config.LOGS / f"job-{job['id']}.jsonl", "a")
        w.proc = subprocess.Popen(cmd, cwd=config.HOME, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1, start_new_session=True)
        w.job_id, w.started, w.step = job["id"], time.time(), "Starting"
        threading.Thread(target=self._read, args=(w, job, log), daemon=True).start()

    def _read(self, w: Worker, job, log):
        result_text, result_ev = "", {}
        proc = w.proc
        seen_msgs, partial = set(), {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
                                     "cache_creation_input_tokens": 0}   # summed per message, for stopped jobs
        for line in proc.stdout:
            log.write(line)
            try:
                ev = json.loads(line)
            except ValueError:
                if line.strip():
                    db.add_event(job["id"], w.n, "text", line.strip())
                continue
            msg = ev.get("message") or {}
            if ev.get("type") == "assistant" and msg.get("id") and msg["id"] not in seen_msgs:
                seen_msgs.add(msg["id"])
                for k in partial:
                    partial[k] += (msg.get("usage") or {}).get(k, 0) or 0
            for kind, text in summarize_event(ev):
                db.add_event(job["id"], w.n, kind, text)
                if kind == "tool":
                    w.step = text
            if ev.get("type") == "result":
                result_text = ev.get("result") or ""
                result_ev = ev
                break                     # job done: don't wait for the session to wind down
        self._terminate(proc)             # kill the agent (and anything it started) after every job
        log.close()
        u = result_ev.get("usage") or partial
        db.set_stats(job["id"], {
            "agent": w.agent, "window": w.n, "seconds": int(time.time() - (w.started or time.time())),
            "turns": result_ev.get("num_turns"), "cost": result_ev.get("total_cost_usd"),
            "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
            "cache_read": u.get("cache_read_input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0),
            "stopped": bool(w.killed) or not result_ev})
        if not w.killed:                                     # a killed job's status was already set by kill()
            self._finish(w, job, result_text, proc.returncode)
        w.last_job = job["id"]
        w.proc, w.job_id, w.step, w.started, w.killed, w.agent = None, None, "", None, False, None
        self._maybe_finalize()

    @staticmethod
    def _terminate(proc):
        """End the Claude session and its whole process group (background shells, sleeps, polls)."""
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    proc.kill()
                proc.wait()
        try:
            proc.stdout.close()
        except Exception:
            pass

    def _finish(self, w, job, result_text, rc):
        r = parse_result(result_text)
        if rc and not result_text:
            r["note"] = f"claude exited with code {rc}; see logs/job-{job['id']}.jsonl"
        notes = r["note"] + (f" | NEEDS: {r['needs']}" if r["needs"] else "")
        self._record(job["id"], r["status"])
        db.log(job["url"], r["company"], r["role"], "", r["status"], notes, needs=r["needs"], worker=w.n)
        if r["learned"]:
            config.LEARNED.parent.mkdir(parents=True, exist_ok=True)
            with open(config.LEARNED, "a") as f:
                host = urllib.parse.urlsplit(job["url"]).netloc
                f.write(f"- **{r['company'] or host}** ({host}): {r['learned']}\n")

    # ---------------------------------------------------------------- view
    def snapshot(self) -> dict:
        n = max(1, min(int(config.load_settings().get("workers", 2)), 4))
        ws = []
        for i in range(1, max(n, max(self.workers, default=0)) + 1):
            w = self.workers.get(i) or Worker(i)
            job = db.get(w.job_id) if w.job_id else None
            ws.append({"n": i, "agent": w.agent if w.proc else None, "busy": bool(w.proc),
                       "job": dict(job) if job else None, "step": w.step,
                       "elapsed": int(time.time() - w.started) if w.started else 0,
                       "last_job": None})       # finished jobs move to their own row in "history"
        active = self.run is not None
        return {"running": self.running, "active": active, "workers": ws, "message": self.message,
                "finishing": active and not self.running, "last_run": None if active else self.last_run,
                "run_counts": self._run_counts() if active else {}, "history": self._history() if active else []}

    def _history(self) -> list[dict]:
        """Jobs this run has finished, newest first: one row each (a new agent session per job)."""
        running = {w.job_id for w in self.workers.values() if w.proc}
        out = []
        for o in reversed((self.run or {}).get("order", [])):
            if o["id"] in running:
                continue
            j = db.get(o["id"])
            if not j:
                continue
            out.append({"id": j["id"], "worker": o["worker"], "agent": o.get("agent"), "status": j["status"],
                        "role": j["role"], "company": j["company"] or urllib.parse.urlsplit(j["url"]).netloc,
                        "note": (j["needs"] or j["notes"] or "")[:220], "url": j["url"],
                        "started": time.strftime("%H:%M", time.localtime(o["started"])), "stats": db.stats_of(j)})
        return out

    def _run_counts(self) -> dict:
        c = {}
        for st in (self.run or {}).get("jobs", {}).values():
            c[st] = c.get(st, 0) + 1
        return c


def preflight(s: dict) -> list[str]:
    problems = []
    if not shutil.which("claude"):
        problems.append("Claude Code CLI not found")
    if not shutil.which("agent-browser"):
        problems.append("agent-browser not found (npm i -g agent-browser)")
    if not browser.browser_path():
        problems.append("no Chromium-based browser found")
    if not config.active_resume():
        problems.append("upload a resume first")
    if not config.PROFILE_JSON.exists():
        problems.append("fill in your profile first")
    return problems


ORCH = Orchestrator()
