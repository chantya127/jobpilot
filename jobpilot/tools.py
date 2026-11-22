"""CLI used by the agents (via jobkit.sh) and by the orchestrator chat:  python -m jobpilot.tools <command> ...

Worker commands
  log <url> <company> <role> <portal> <status> [notes]   record a result (status: see `statuses`)
  done <url>                                              exit 0 if already applied/skipped
  otp [--match RE] [--len N] [--link [RE]] [--since S] [--timeout S] [--list]

Orchestrator-chat commands
  status                                  run state, workers, counts, next jobs in the queue
  list <status|all> [N]                   jobs with that status (id | status | company | role | url | notes)
  add <url> [<url> ...]                   queue job links
  set <job_id> <status> [note]            change a job's status (e.g. queued to retry, skipped to drop)
  remove <job_id>                         delete a job from the queue/tracker
  guidance show | set "<text>" | clear    standing instructions added to every NEW worker prompt
  control start|pause|stop|kill <n>       control the run (talks to the running dashboard)
  statuses                                list valid statuses
"""
import json
import os
import sys
import urllib.request

from . import config, db, otp


def control(action: str, arg: str = "") -> str:
    port = os.environ.get("JP_PORT", "8765")
    path = f"/agents/kill/{arg}" if action == "kill" else f"/agents/{action}"
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="POST", data=b"")
    try:
        urllib.request.urlopen(req, timeout=10)
        return f"ok: {action} {arg}".strip()
    except Exception as e:
        return f"failed: {e}"


def status() -> str:
    port = os.environ.get("JP_PORT", "8765")
    try:
        snap = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/agents/state", timeout=5))
    except Exception:
        snap = {"running": None, "workers": []}
    s = config.load_settings()
    out = [f"run: {'running' if snap.get('running') else 'stopped'} · auto_submit={s['auto_submit']} · "
           f"workers={s['workers']} · otp={'on' if s['otp_enabled'] else 'off'}",
           "counts: " + ", ".join(f"{k}={v}" for k, v in sorted(db.counts().items()))]
    for w in snap.get("workers", []):
        job = w.get("job") or {}
        out.append(f"worker {w['n']}: " + (f"#{job.get('id')} {job.get('company') or job.get('url')} · {w.get('step', '')[:120]}"
                                           if w.get("busy") else "idle"))
    q = db.queued()
    out.append(f"queue ({len(q)}): " + "; ".join(f"#{j['id']} {j['company'] or j['url'][:70]}" for j in q[:10]))
    if s.get("guidance"):
        out.append(f"guidance: {s['guidance']}")
    return "\n".join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "otp":
        otp.main(rest)
    elif cmd == "done":
        sys.exit(0 if db.is_done(rest[0]) else 1)
    elif cmd == "log":
        if len(rest) < 5:
            sys.exit("usage: log <url> <company> <role> <portal> <status> [notes]")
        url, company, role, portal, st = rest[:5]
        if st not in db.STATUSES:
            sys.exit(f"unknown status {st}; use one of {', '.join(db.STATUSES)}")
        db.log(url, company, role, portal, st, rest[5] if len(rest) > 5 else "")
        print(f"logged {st}: {company}")
    elif cmd == "status":
        print(status())
    elif cmd == "statuses":
        print(" ".join(db.STATUSES))
    elif cmd == "list":
        st = rest[0] if rest else "all"
        n = int(rest[1]) if len(rest) > 1 else 30
        for j in db.jobs(None if st == "all" else st, limit=n):
            print(f"#{j['id']} | {j['status']} | {j['company']} | {j['role']} | {j['url']} | {j['notes'][:120]}")
    elif cmd == "add":
        for u in rest:
            print(f"{db.add_url(u)}: {u}")
    elif cmd == "set":
        if len(rest) < 2 or rest[1] not in db.STATUSES:
            sys.exit(f"usage: set <job_id> <{'|'.join(db.STATUSES)}> [note]")
        fields = {"needs": ""}
        if len(rest) > 2:
            fields["notes"] = rest[2]
        db.set_status(int(rest[0]), rest[1], **fields)
        print(f"#{rest[0]} -> {rest[1]}")
    elif cmd == "remove":
        db.delete(int(rest[0]))
        print(f"removed #{rest[0]}")
    elif cmd == "guidance":
        s = config.load_settings()
        sub = rest[0] if rest else "show"
        if sub == "set":
            s["guidance"] = " ".join(rest[1:]).strip()
        elif sub == "clear":
            s["guidance"] = ""
        if sub in ("set", "clear"):
            config.save_settings(s)
        print(f"guidance: {s.get('guidance') or '(none)'}")
    elif cmd == "control":
        if not rest:
            sys.exit("usage: control start|pause|stop|kill <n>")
        print(control(rest[0], rest[1] if len(rest) > 1 else ""))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
