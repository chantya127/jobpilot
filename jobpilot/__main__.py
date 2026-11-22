"""`jobpilot` -> start the local dashboard and open it in the browser."""
import argparse
import threading
import time
import webbrowser


def main():
    ap = argparse.ArgumentParser(prog="jobpilot")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="check every requirement, print the result and the fix for anything missing, then exit")
    ap.add_argument("--deep", action="store_true", help="with --check: also verify the Claude Code login (uses a few tokens)")
    a = ap.parse_args()
    if a.check:
        raise SystemExit(check(a.deep))
    import os
    import uvicorn
    os.environ["JP_PORT"] = str(a.port)       # lets the orchestrator chat's CLI reach this server
    url = f"http://127.0.0.1:{a.port}"
    if not a.no_browser:
        threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open(url)), daemon=True).start()
    print(f"JobPilot running at {url}  (Ctrl-C to stop)")
    uvicorn.run("jobpilot.server:app", host="127.0.0.1", port=a.port, log_level="warning")


def check(deep: bool = False) -> int:
    from .server import system_checks
    rows = system_checks(deep=deep)
    for c in rows:
        print(f"{'OK  ' if c['ok'] else 'MISSING'}  {c['label']}: {c['detail']}")
        if not c["ok"] and c["fix"]:
            print(f"         fix: {c['fix']}")
    bad = [c for c in rows if not c["ok"]]
    print("\nAll requirements met. Start with: uv run jobpilot" if not bad else f"\n{len(bad)} requirement(s) missing.")
    return 1 if bad else 0


if __name__ == "__main__":
    main()
