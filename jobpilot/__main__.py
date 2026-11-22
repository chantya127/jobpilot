"""`jobpilot` -> start the local dashboard and open it in the browser."""
import argparse
import threading
import time
import webbrowser


def main():
    ap = argparse.ArgumentParser(prog="jobpilot")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    import os
    import uvicorn
    os.environ["JP_PORT"] = str(a.port)       # lets the orchestrator chat's CLI reach this server
    url = f"http://127.0.0.1:{a.port}"
    if not a.no_browser:
        threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open(url)), daemon=True).start()
    print(f"JobPilot running at {url}  (Ctrl-C to stop)")
    uvicorn.run("jobpilot.server:app", host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
