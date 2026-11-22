"""FastAPI dashboard. Server-rendered Jinja pages + HTMX partials; everything runs locally."""
import platform
import re
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__, browser, chat, config, db, learned, otp, profile, ui
from .orchestrator import ORCH
from .procs import IS_WIN, OS_NAME, child_env, git_bash, group_kwargs, which

HERE = Path(__file__).parent
app = FastAPI(title="JobPilot")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
T = Jinja2Templates(directory=HERE / "templates")
ui.register(T.env)

NAV = [
    ("overview", "/", "Overview"),
    ("setup", "/setup", "Setup"),
    ("profile", "/profile", "Knowledge base"),
    ("resumes", "/resumes", "Resumes"),
    ("preferences", "/preferences", "Job preferences"),
    ("find", "/find", "Find jobs"),
    ("queue", "/queue", "Queue"),
    ("agents", "/agents", "Live agents"),
    ("inbox", "/inbox", "Needs you"),
    ("tracker", "/tracker", "Tracker"),
    ("settings", "/settings", "Settings"),
]
INBOX_STATUSES = ("ready-for-review", "pending-user", "blocked")
SCRAPER = {"proc": None}


def page(request: Request, name: str, active: str, **ctx):
    c = db.counts()
    ctx.update(request=request, nav=NAV, active=active, version=__version__, settings=config.load_settings(),
               inbox_count=sum(c.get(s, 0) for s in ("ready-for-review", "pending-user")),
               running=ORCH.running, flash=request.query_params.get("flash", ""))
    return T.TemplateResponse(request, name, ctx)


def back(url: str, flash: str = "") -> RedirectResponse:
    sep = "&" if "?" in url else "?"
    return RedirectResponse(url + (f"{sep}flash={flash}" if flash else ""), status_code=303)


def run_ok(cmd: list[str], timeout=20) -> tuple[bool, str]:
    try:
        cmd = [which(cmd[0]) or cmd[0], *cmd[1:]]
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                             env=child_env(), **group_kwargs())
        return out.returncode == 0, (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else ""
    except Exception as e:
        return False, str(e)


def system_checks(deep: bool = False) -> list[dict]:
    checks = []

    def add(key, label, ok, detail, fix):
        checks.append({"key": key, "label": label, "ok": ok, "detail": detail, "fix": fix})

    add("os", "macOS, Linux or Windows", OS_NAME in ("macOS", "Linux", "Windows"), f"{OS_NAME} {platform.release()}",
        "Use macOS, Linux or Windows 10/11.")
    if IS_WIN:
        gb = git_bash()
        add("git-bash", "Git for Windows (Git Bash)", bool(gb), gb or "not found",
            "winget install --id Git.Git -e   (Claude Code runs the agents' shell commands in Git Bash). If Git is "
            "installed somewhere unusual, set CLAUDE_CODE_GIT_BASH_PATH to its bin\\bash.exe.")
    curl = which("curl")
    add("curl", "curl", bool(curl), curl or "not found",
        "Install curl with your package manager (e.g. sudo apt install curl).")
    add("python", "Python 3.10+", sys.version_info >= (3, 10), platform.python_version(), "Install Python 3.10+ (uv does this for you).")
    node = which("node")
    add("node", "Node.js 20+", bool(node), run_ok(["node", "-v"])[1] if node else "not found",
        "Install Node.js 20+ from nodejs.org or with your package manager.")
    ab = which("agent-browser")
    add("agent-browser", "agent-browser", bool(ab), run_ok(["agent-browser", "--version"])[1] if ab else "not found",
        "npm install -g agent-browser")
    cl = which("claude")
    detail = run_ok(["claude", "--version"])[1] if cl else "not found"
    ok = bool(cl)
    if cl and IS_WIN and cl.lower().endswith((".cmd", ".bat")):
        detail += " (npm .cmd shim: the native installer is more reliable on Windows)"
    if cl and deep:
        ok, out = run_ok(["claude", "-p", "Reply with the single word: ok", "--model", "haiku"], timeout=90)
        detail = "logged in" if ok else f"not logged in: {out[:120]}"
    add("claude", "Claude Code CLI (logged in)", ok, detail,
        ("Install Claude Code (Windows PowerShell: irm https://claude.ai/install.ps1 | iex; macOS/Linux: "
         "curl -fsSL https://claude.ai/install.sh | bash), then run `claude` once in a terminal to log in."))
    bp = browser.browser_path()
    add("browser", "Chromium-based browser", bool(bp), bp or "none found", "Install Chrome, Brave, Chromium or Edge.")
    try:
        import playwright  # noqa: F401
        add("playwright", "Playwright (for Find jobs)", True, "installed", "")
    except ImportError:
        add("playwright", "Playwright (for Find jobs)", False, "missing", "uv sync")
    return checks


def onboarding_steps() -> list[dict]:
    s = config.load_settings()
    pct, _ = profile.completeness()
    return [
        {"label": "Install the requirements", "done": all(c["ok"] for c in system_checks()), "href": "/setup#checks"},
        {"label": "Upload your resume", "done": bool(config.active_resume()), "href": "/resumes"},
        {"label": "Fill in your knowledge base", "done": pct == 100, "href": "/profile"},
        {"label": "Set job preferences", "done": bool(s.get("keywords") or s.get("stack_accept") or s.get("avoid_companies")), "href": "/preferences"},
        {"label": "Portal login + email codes (optional)", "done": bool(config.load_secrets().get("email")), "href": "/settings"},
        {"label": "Log in to LinkedIn in worker 1 (for Find jobs)", "done": browser.profile_dir(1).exists(), "href": "/settings#browser"},
    ]


# ------------------------------------------------------------------ overview / setup
@app.get("/", response_class=HTMLResponse)
def overview(request: Request):
    steps = onboarding_steps()
    return page(request, "overview.html", "overview", counts=db.counts(), steps=steps,
                setup_done=all(s["done"] for s in steps[:3]), recent=db.jobs(limit=8), snap=ORCH.snapshot())


@app.get("/setup", response_class=HTMLResponse)
def setup(request: Request, deep: int = 0):
    return page(request, "setup.html", "setup", checks=system_checks(deep=bool(deep)), steps=onboarding_steps(),
                deep=deep)


# ------------------------------------------------------------------ knowledge base
def to_month_input(v: str) -> str:
    """'08/2023' -> '2023-08' for <input type=month>."""
    m = re.match(r"^\s*(\d{1,2})/(\d{4})\s*$", v or "")
    return f"{m.group(2)}-{int(m.group(1)):02d}" if m else ""


def from_month_input(v: str) -> str:
    m = re.match(r"^(\d{4})-(\d{2})$", v or "")
    return f"{m.group(2)}/{m.group(1)}" if m else ""


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    p = profile.load()
    sections = {}
    for key, label, section, ph in profile.FIELDS:
        sections.setdefault(section, []).append({
            "key": key, "label": label, "ph": ph, "value": p.get(key, ""),
            "options": profile.OPTIONS.get(key), "single": key in profile.SINGLE})
    work = [dict(w, start_m=to_month_input(w.get("start", "")), end_m=to_month_input(w.get("end", "")),
                 present=not w.get("end")) for w in (p.get("work") or [])]
    pct, missing = profile.completeness(p)
    return page(request, "profile.html", "profile", sections=sections, work=work,
                md=profile.load_md(), pct=pct, missing=missing, has_resume=bool(config.active_resume()))


@app.post("/profile")
async def profile_save(request: Request):
    form = await request.form()
    p = profile.load()
    for key, *_ in profile.FIELDS:
        if key in form:
            p[key] = str(form[key]).strip()
    work = []
    for i in range(int(form.get("work_count", 0))):
        g = lambda f: str(form.get(f"work_{i}_{f}", "")).strip()  # noqa: E731
        if not g("company"):
            continue
        work.append({"company": g("company"), "title": g("title"), "location": g("location"),
                     "start": from_month_input(g("start")),
                     "end": "" if g("present") else from_month_input(g("end"))})
    p["work"] = work
    profile.save(p)
    return back("/profile", "Profile saved")


@app.post("/profile/md")
def profile_md_save(md: str = Form("")):
    profile.save_md(md)
    return back("/profile#kb", "Knowledge base saved")


@app.post("/profile/tidy-learned")
def profile_tidy_learned():
    n = learned.tidy()
    return back("/profile#kb", f"Answers learned rewritten as {n} reusable rows. Check them below"
                if n else "No learned answers to tidy yet")


@app.post("/profile/from-resume")
def profile_from_resume():
    from . import resume_parse
    r = config.active_resume()
    if not r:
        return back("/resumes", "Upload a resume first")
    try:
        resume_parse.apply(r)
    except Exception as e:
        return back("/profile", f"Couldn't read the resume: {str(e)[:150]}")
    return back("/profile", "Draft filled from your resume. Check every field.")


# ------------------------------------------------------------------ resumes
@app.get("/resumes", response_class=HTMLResponse)
def resumes(request: Request):
    active = config.active_resume()
    files = [{"name": f.name, "size": f.stat().st_size // 1024, "active": active and f.name == active.name}
             for f in sorted(config.RESUMES.glob("*.pdf"))] if config.RESUMES.exists() else []
    return page(request, "resumes.html", "resumes", files=files)


@app.post("/resumes/upload")
async def resume_upload(file: UploadFile = File(...)):
    config.ensure_dirs()
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(file.filename or "resume.pdf").name)
    if not name.lower().endswith(".pdf"):
        return back("/resumes", "Please upload a PDF")
    (config.RESUMES / name).write_bytes(await file.read())
    s = config.load_settings()
    first = not s.get("active_resume")
    if first:
        s["active_resume"] = name
        config.save_settings(s)
    profile.render()
    return back("/resumes", f"Uploaded {name}" + (" and set as active" if first else ""))


@app.post("/resumes/active")
def resume_active(name: str = Form(...)):
    s = config.load_settings()
    s["active_resume"] = Path(name).name
    config.save_settings(s)
    profile.render()
    return back("/resumes", "Active resume changed")


@app.post("/resumes/delete")
def resume_delete(name: str = Form(...)):
    f = config.RESUMES / Path(name).name
    if f.exists():
        f.unlink()
    s = config.load_settings()
    if s.get("active_resume") == f.name:
        s["active_resume"] = ""
        config.save_settings(s)
    profile.render()
    return back("/resumes", "Deleted")


@app.get("/resumes/file/{name}")
def resume_file(name: str):
    return FileResponse(config.RESUMES / Path(name).name, media_type="application/pdf")


# ------------------------------------------------------------------ preferences
def split_lines(text: str) -> list[str]:
    return [l.strip() for l in re.split(r"[\n,]", text or "") if l.strip()]


@app.get("/preferences", response_class=HTMLResponse)
def preferences(request: Request):
    return page(request, "preferences.html", "preferences")


@app.post("/preferences")
def preferences_save(keywords: str = Form(""), avoid: str = Form(""), stack_accept: str = Form(""),
                     stack_skip: str = Form(""), search_location: str = Form(""),
                     notif_max: int = Form(10), notif_days: float = Form(3), keyword_search: str = Form("")):
    s = config.load_settings()
    s.update(keywords=split_lines(keywords), avoid_companies=split_lines(avoid), stack_accept=split_lines(stack_accept),
             stack_skip=split_lines(stack_skip), search_location=search_location.strip(),
             notif_max=max(1, min(notif_max, 200)), notif_days=max(0.5, min(notif_days, 60)),
             keyword_search=bool(keyword_search))
    config.save_settings(s)
    profile.render()
    return back("/preferences", "Preferences saved")


@app.post("/preferences/easy-apply")
def preferences_easy_apply(on: str = Form("")):
    s = config.load_settings()
    s["skip_easy_apply"] = bool(on)
    config.save_settings(s)
    return back("/preferences", "LinkedIn Easy Apply " + ("will never be automated" if on else "setting changed"))


# ------------------------------------------------------------------ find jobs
@app.get("/find", response_class=HTMLResponse)
def find(request: Request):
    return page(request, "find.html", "find", busy=scraper_busy())


def scraper_busy() -> bool:
    p = SCRAPER["proc"]
    return bool(p and p.poll() is None)


LOG_TAG = re.compile(r"^\[(\w+)\]\s?(.*)$")


def scraper_lines() -> list[dict]:
    f = config.LOGS / "scraper.log"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        m = LOG_TAG.match(line)
        out.append({"tag": m.group(1), "text": m.group(2)} if m else {"tag": "raw", "text": line})
    return out


@app.post("/find/run")
def find_run():
    if not scraper_busy():
        config.ensure_dirs()
        log = open(config.LOGS / "scraper.log", "w", encoding="utf-8")
        SCRAPER["proc"] = subprocess.Popen([sys.executable, "-u", "-m", "jobpilot.scraper"], stdout=log,
                                           stderr=subprocess.STDOUT, cwd=config.HOME, env=child_env(),
                                           **group_kwargs())
    return {"ok": True}


@app.post("/find/stop")
def find_stop():
    p = SCRAPER["proc"]
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()
        with open(config.LOGS / "scraper.log", "a", encoding="utf-8") as f:
            f.write("[done] Stopped by you\n")
    return {"ok": True}


def find_summary(lines: list[dict]) -> dict | None:
    """Counts for the last run, built from its tagged log lines."""
    f = config.LOGS / "scraper.log"
    if not lines or not f.exists():
        return None
    c = {k: 0 for k in ("queued", "known", "easy", "skip", "error")}
    for l in lines:
        if l["tag"] in c:
            c[l["tag"]] += 1
    done = [l["text"] for l in lines if l["tag"] == "done"]
    notes = [l["text"] for l in lines if l["tag"] == "error"]
    import datetime as _dt
    return {"counts": c, "finished": _dt.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d %b, %H:%M"),
            "stopped": any("Stopped by you" in d for d in done), "complete": bool(done),
            "login_needed": any("Not logged in" in n for n in notes),
            "error": notes[-1] if notes and not done else ""}


@app.get("/find/log.json")
def find_log_json(after: int = 0):
    lines = scraper_lines()
    busy = scraper_busy()
    phases = [l["text"] for l in lines if l["tag"] == "phase"]
    activity = next((l["text"] for l in reversed(lines) if l["tag"] not in ("phase", "raw")), "Starting…")
    return {"busy": busy, "total": len(lines), "lines": lines[after:], "phase": phases[-1] if phases else "starting",
            "activity": activity, "summary": None if busy else find_summary(lines)}


# ------------------------------------------------------------------ queue
@app.get("/queue", response_class=HTMLResponse)
def queue(request: Request):
    return page(request, "queue.html", "queue", jobs=db.queued())


@app.post("/queue/add")
def queue_add(urls: str = Form("")):
    res = {"added": 0, "duplicate": 0, "invalid": 0}
    for u in re.findall(r"https?://\S+", urls):
        res[db.add_url(u.rstrip(").,;'\""))] += 1
    return back("/queue", f"Added {res['added']}" + (f", {res['duplicate']} already known" if res["duplicate"] else ""))


@app.post("/queue/{job_id}/delete")
def queue_delete(job_id: int):
    db.delete(job_id)
    return back("/queue")


@app.post("/queue/clear")
def queue_clear():
    for j in db.queued():
        db.delete(j["id"])
    return back("/queue", "Queue cleared")


# ------------------------------------------------------------------ live agents
@app.get("/agents", response_class=HTMLResponse)
def agents(request: Request):
    return page(request, "agents.html", "agents")


@app.get("/agents/state")
def agents_state():
    snap = ORCH.snapshot()
    s = config.load_settings()
    snap.update(queued=len(db.queued()), auto_submit=s["auto_submit"], guidance=s.get("guidance", ""),
                chat_busy=chat.busy())
    return snap


@app.get("/agents/events")
def agents_events(job: int, after: int = 0):
    return [dict(e) for e in db.events_after(job, after)]


@app.get("/chat.json")
def chat_json(after: int = 0):
    return {"busy": chat.busy(), "messages": chat.messages(after)}


@app.post("/chat")
def chat_send(text: str = Form(...)):
    if text.strip() and not chat.busy():
        chat.ask(text.strip())
    return {"ok": True}


@app.post("/chat/reset")
def chat_reset():
    chat.reset()
    return {"ok": True}


@app.post("/agents/dismiss-summary")
def agents_dismiss_summary():
    ORCH.last_run = None
    (config.HOME / "last_run.json").unlink(missing_ok=True)
    return {"ok": True}


@app.post("/agents/{action}")
def agents_action(action: str):
    {"start": ORCH.start, "pause": ORCH.pause, "stop": ORCH.stop}.get(action, lambda: None)()
    return back("/agents", ORCH.message)


@app.post("/agents/kill/{n}")
def agents_kill(n: int):
    ORCH.kill(n, requeue=False)
    return back("/agents", f"Worker {n} stopped")


@app.post("/browser/open/{n}")
def browser_open(n: int, url: str = Form("about:blank"), next: str = Form("/settings")):
    browser.write_wrappers(max(n, int(config.load_settings().get("workers", 2))))
    try:
        browser.launch(n, url)
    except RuntimeError as e:
        return back(next, str(e))
    return back(next, f"Worker {n} browser opened")


# ------------------------------------------------------------------ inbox
@app.get("/inbox", response_class=HTMLResponse)
def inbox(request: Request):
    items = []
    for j in db.jobs(INBOX_STATUSES):
        needs = j["needs"] or ""
        q = needs.split("QUESTION:", 1)[1].strip() if "QUESTION:" in needs else ""
        items.append({"job": j, "question": q})
    return page(request, "inbox.html", "inbox", items=items)


@app.post("/inbox/{job_id}/answer")
def inbox_answer(job_id: int, question: str = Form(...), answer: str = Form(...)):
    rows = learned.learn(question, answer)
    db.set_status(job_id, "queued", needs="", notes="Answered: re-queued")
    return back("/inbox", f"Saved as {len(rows)} answer{'s' if len(rows) != 1 else ''} in your knowledge base and re-queued")


@app.post("/inbox/{job_id}/{action}")
def inbox_action(job_id: int, action: str):
    status = {"applied": "applied", "retry": "queued", "skip": "skipped"}.get(action)
    if status:
        j = db.get(job_id)
        note = {"applied": "Submitted by you", "retry": "Retry requested", "skip": "Skipped by you"}[action]
        db.set_status(job_id, status, needs="", notes=(j["notes"] + " | " if j and j["notes"] else "") + note)
    return back("/inbox")


# ------------------------------------------------------------------ tracker
PAGE_SIZE = 25


def portal_of(r) -> str:
    return r["portal"] or (r["url"].split("/")[2].replace("www.", "") if "://" in r["url"] else "")


@app.get("/tracker", response_class=HTMLResponse)
def tracker(request: Request, status: str = "", q: str = "", portal: str = "", p: int = 1):
    sel = [s for s in status.split(",") if s in db.STATUSES]
    all_rows = db.jobs(sel or None, limit=100000)
    portals = sorted({portal_of(r) for r in db.jobs(limit=100000) if portal_of(r)}, key=str.lower)
    rows = all_rows
    if portal:
        rows = [r for r in rows if portal_of(r) == portal]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in f"{r['company']} {r['role']} {r['url']} {r['notes']}".lower()]
    pages = max(1, -(-len(rows) // PAGE_SIZE))
    p = max(1, min(p, pages))
    return page(request, "tracker.html", "tracker", rows=rows[(p - 1) * PAGE_SIZE: p * PAGE_SIZE], total=len(rows),
                p=p, pages=pages, counts=db.counts(), status=",".join(sel), sel=sel, q=q, portal=portal,
                portals=portals, statuses=db.STATUSES, portal_of=portal_of)


@app.post("/tracker/update")
async def tracker_update(request: Request):
    """Set status for one or many jobs, or delete them. Form: ids=1,2,3 & status=<status>|delete"""
    form = await request.form()
    ids = [int(i) for i in str(form.get("ids", "")).split(",") if i.strip().isdigit()]
    status = str(form.get("status", ""))
    for i in ids:
        if status == "delete":
            db.delete(i)
        elif status in db.STATUSES:
            db.set_status(i, status, needs="")
    return {"ok": True, "n": len(ids)}


@app.get("/tracker.csv")
def tracker_csv():
    return Response(db.export_csv(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=tracker.csv"})


@app.post("/tracker/import")
async def tracker_import(file: UploadFile = File(...)):
    n = db.import_csv((await file.read()).decode("utf-8", "replace"))
    return back("/tracker", f"Imported {n} rows")


@app.get("/job/{job_id}/open")
def job_open(job_id: int, next: str = "/tracker"):
    """Open the job page in its worker's browser window (where the filled form lives), not in your own browser."""
    j = db.get(job_id)
    if not j:
        return back(next, "Job not found")
    w = j["worker"] or 1
    browser.write_wrappers(max(w, int(config.load_settings().get("workers", 2))))
    try:
        how = browser.show_url(w, j["url"])
    except Exception as e:
        return back(next, f"Couldn't open worker {w}'s browser: {str(e)[:100]}")
    return back(next if next.startswith("/") else "/tracker",
                f"{'Switched to' if how == 'focused' else 'Opened'} the job in worker {w}'s window")


@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    j = db.get(job_id)
    return page(request, "job.html", "tracker", job=j, events=db.events(job_id, 300), stats=db.stats_of(j) if j else {})


# ------------------------------------------------------------------ settings
@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    sec = config.load_secrets()
    have = {k: bool(sec.get(k)) for k in config.SECRET_KEYS}
    # Local-only page (127.0.0.1): stored values are filled in masked, with a show/hide toggle.
    return page(request, "settings.html", "settings", have=have, sec=sec, gmail_user=sec.get("gmail_user", ""),
                browsers=browser.detect(), current_browser=browser.browser_path(),
                real_profiles=browser.existing_profiles(),
                worker_profiles={w: browser.assigned_profile(w) for w in range(1, 5)})


@app.post("/settings")
def settings_save(workers: int = Form(2), auto_submit: str = Form(""), model: str = Form("sonnet"),
                  browser_path: str = Form("")):
    s = config.load_settings()
    s.update(workers=max(1, min(workers, 4)), auto_submit=bool(auto_submit), model=model, browser_path=browser_path)
    config.save_settings(s)
    return back("/settings", "Settings saved")


@app.post("/settings/secrets")
def settings_secrets(email: str = Form(""), password: str = Form(""), password_strong: str = Form(""),
                     pan: str = Form("")):
    config.save_secrets({"email": email, "password": password, "password_strong": password_strong, "pan": pan})
    return back("/settings#accounts", "Saved")


@app.post("/settings/otp")
def settings_otp(gmail_user: str = Form(""), gmail_app_password: str = Form(""), otp_enabled: str = Form("")):
    config.save_secrets({"gmail_user": gmail_user, "gmail_app_password": gmail_app_password.replace(" ", "")})
    s = config.load_settings()
    s["otp_enabled"] = bool(otp_enabled)
    config.save_settings(s)
    return back("/settings#otp", "Email code settings saved")


@app.post("/settings/otp/test", response_class=HTMLResponse)
def settings_otp_test():
    try:
        rows = otp.list_recent(since=86400, n=5)
        items = "".join(f"<li>{r}</li>" for r in rows) or "<li>Connected, but no mail in the last 24 h.</li>"
        return f'<div class="note ok">Connected to Gmail. Latest mail:<ul class="mono small">{items}</ul></div>'
    except otp.OTPError as e:
        return f'<div class="note bad">{e}</div>'


@app.post("/settings/copy-profile")
async def settings_copy_profile(request: Request):
    form = await request.form()
    s = config.load_settings()
    n = int(s.get("workers", 2))
    choice = {str(w): str(form.get(f"src{w}") or "") for w in range(1, n + 1)}
    s["worker_profiles"] = {k: v for k, v in choice.items() if v}
    s["copy_profile_from"] = ""     # the per-worker choice is now explicit ("" = the worker's own profile)
    config.save_settings(s)
    errors = []
    for w in range(1, n + 1):
        src = choice[str(w)]
        if src and browser.copied_from(w) != src:
            try:
                browser.copy_into(w, src)
            except Exception as e:
                errors.append(f"worker {w}: {str(e)[:120]}")
    if errors:
        return back("/settings#browser", "Copy failed (close that browser first): " + "; ".join(errors))
    return back("/settings#browser", "Worker profiles updated")


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.on_event("shutdown")
def shutdown():
    """Closing the dashboard stops the agents too (their jobs go back to the queue), so none keep running unseen."""
    ORCH.stop()


@app.on_event("startup")
def startup():
    config.ensure_dirs()
    db.reset_running()
    if not config.PROFILE_MD.exists():
        profile.save_md(profile.PROFILE_MD_TEMPLATE)
    profile.render()
