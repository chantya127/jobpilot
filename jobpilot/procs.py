"""Cross-platform process helpers (macOS, Linux, Windows).

On Windows the agents' Bash tool runs in Git Bash (Claude Code requires Git for Windows there), so the bash engine
(jobkit.sh, bin/abN) works unchanged. Python itself must never exec those scripts directly, must pass POSIX-style
paths (C:/Users/...) into bash, and has no process groups / POSIX signals: this module hides those differences.
"""
import os
import platform
import shutil
import signal
import subprocess
import threading
from pathlib import Path

IS_WIN = platform.system() == "Windows"
OS_NAME = {"Darwin": "macOS", "Linux": "Linux", "Windows": "Windows"}.get(platform.system(), platform.system())


def posix(p) -> str:
    """Path as bash (incl. Git Bash on Windows) understands it: C:\\Users\\me -> C:/Users/me. No-op on macOS/Linux."""
    return Path(p).as_posix() if p else ""


def which(name: str) -> str | None:
    """Full path of an executable. Windows needs it: `claude`/`agent-browser` may be .cmd shims that CreateProcess
    won't find from a bare name."""
    return shutil.which(name)


def exe(name: str) -> str:
    return which(name) or name


def child_env(**extra) -> dict:
    """Environment for child processes: UTF-8 everywhere (Windows defaults to the ANSI code page otherwise)."""
    return dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", **{k: str(v) for k, v in extra.items()})


def group_kwargs(gui: bool = False) -> dict:
    """Popen kwargs that start the child in its own process group/session, so it can be killed as a tree (POSIX) and
    so Ctrl-C in the dashboard terminal doesn't kill it. On Windows also hides console windows of CLI children."""
    if IS_WIN:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP
        flags |= subprocess.DETACHED_PROCESS if gui else subprocess.CREATE_NO_WINDOW
        return {"creationflags": flags}
    return {"start_new_session": True}


def kill_tree(proc: subprocess.Popen, wait: float | None = 5) -> None:
    """Terminate a process and everything it started (bash shells, polls). wait=None: signal only, don't wait."""
    if proc.poll() is not None:
        return
    if IS_WIN:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        if wait is not None:
            try:
                proc.wait(wait)
            except subprocess.TimeoutExpired:
                proc.kill()
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        proc.terminate()
    if wait is None:
        return
    try:
        proc.wait(wait)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()
        proc.wait()


def git_bash() -> str | None:
    """Git Bash on Windows (what Claude Code's Bash tool uses). Not WSL's System32\\bash.exe."""
    env = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if env and os.path.exists(env):
        return env
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
        if base and os.path.exists(p := os.path.join(base, "Git", "bin", "bash.exe")):
            return p
    b = shutil.which("bash")
    return b if b and "system32" not in b.lower() else None


class KeepAwake:
    """Stop the computer from sleeping while a run is active (macOS caffeinate, Linux systemd-inhibit,
    Windows SetThreadExecutionState). Best effort: silently does nothing if unavailable."""

    def __init__(self):
        self.proc = None
        self._stop = None

    def start(self):
        if self.proc or self._stop:
            return
        try:
            if platform.system() == "Darwin" and shutil.which("caffeinate"):
                self.proc = subprocess.Popen(["caffeinate", "-dims"])
            elif platform.system() == "Linux" and shutil.which("systemd-inhibit"):
                self.proc = subprocess.Popen(["systemd-inhibit", "--what=idle:sleep", "--who=JobPilot",
                                              "--why=Applying to jobs", "sleep", "infinity"],
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif IS_WIN:
                self._stop = threading.Event()
                threading.Thread(target=self._win_hold, args=(self._stop,), daemon=True).start()
        except Exception:
            self.proc = None

    @staticmethod
    def _win_hold(stop: threading.Event):
        import ctypes
        es_continuous, es_system, es_display = 0x80000000, 0x00000001, 0x00000002
        k = ctypes.windll.kernel32
        k.SetThreadExecutionState(es_continuous | es_system | es_display)
        stop.wait()
        k.SetThreadExecutionState(es_continuous)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None
        if self._stop:
            self._stop.set()
            self._stop = None

    @property
    def active(self) -> bool:
        return bool(self.proc or self._stop)
