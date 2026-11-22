"""Orchestrator chat: talk to the run in plain language ("skip Workday jobs today", "retry the Stripe one",
"what is worker 2 stuck on?"). Each message runs one headless Claude Code turn with the current dashboard state and the
jobpilot.tools CLI; the conversation continues across messages (--resume)."""
import datetime
import json
import subprocess
import sys
import threading

from . import config, tools
from .orchestrator import ISOLATION
from .procs import child_env, exe, group_kwargs, posix

# The prompt goes straight to the orchestrator Claude session (context kept by Claude via --resume).
# This in-memory list exists only so the dashboard can display the conversation; nothing is written to disk.
_LOCK = threading.Lock()
_MESSAGES: list[dict] = []
_BUSY = threading.Event()


def _add(role: str, text: str) -> None:
    with _LOCK:
        _MESSAGES.append({"id": len(_MESSAGES) + 1, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                          "role": role, "text": text})


def messages(after: int = 0) -> list[dict]:
    with _LOCK:
        return [m for m in _MESSAGES if m["id"] > after]

SYSTEM = """You are the coordinator of JobPilot, a local tool where Claude Code workers apply to jobs for the user.
You don't fill forms yourself. You manage the run with this CLI (run it with Bash; it's the ONLY way to change things):

  {py} -m jobpilot.tools <command>
{doc}
Rules:
- Running workers can't be messaged. To change how upcoming jobs are handled, use `guidance set` (applies to every
  NEW worker; include earlier guidance you want to keep, since it replaces it). Tell the user it applies from the next job.
- Read files in {home} (profile.md, answers.md, logs/job-<id>.jsonl, portals-local.md) to answer questions.
  Worker logs are JSON lines; grep them rather than reading whole files.
- Never print secrets (secrets.env). Don't edit profile files: tell the user where to change things in the dashboard.
- Be brief: 1-4 short sentences or a compact list. Say exactly what you changed."""


def busy() -> bool:
    return _BUSY.is_set()


def ask(text: str) -> None:
    """Send the message to the orchestrator Claude in the background; show it in the panel meanwhile."""
    _add("user", text)
    _BUSY.set()
    threading.Thread(target=_run, args=(text,), daemon=True).start()


def reset() -> None:
    """New conversation: clear the panel and start a fresh Claude session next time."""
    with _LOCK:
        _MESSAGES.clear()
    s = config.load_settings()
    s.pop("chat_session", None)
    config.save_settings(s)


def _run(text: str) -> None:
    try:
        s = config.load_settings()
        prompt = f"Current state:\n{tools.status()}\n\nUser: {text}"
        cmd = [exe("claude"), "-p", "--model", s.get("model") or "sonnet", "--output-format", "json",
               "--tools", "Bash", "Read", "Grep", "--allowedTools", "Bash", "Read", "Grep",
               "--append-system-prompt", SYSTEM.format(py=posix(sys.executable), doc=tools.__doc__, home=posix(config.HOME)),
               *ISOLATION]
        if s.get("chat_session"):
            cmd += ["--resume", s["chat_session"]]
        env = child_env(JP_HOME=posix(config.HOME))
        out = subprocess.run(cmd, input=prompt, cwd=config.HOME, env=env, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=600, **group_kwargs())
        try:
            data = json.loads(out.stdout)
        except ValueError:
            data = {}
        if data.get("session_id"):
            s = config.load_settings()
            s["chat_session"] = data["session_id"]
            config.save_settings(s)
        reply = data.get("result") or (out.stderr or out.stdout or "No reply").strip()[-800:]
        _add("assistant", reply)
    except Exception as e:
        _add("assistant", f"Error: {e}")
    finally:
        _BUSY.clear()
