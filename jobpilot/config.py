"""Paths and settings. All user data lives in the data dir (default ~/.jobpilot), never in the repo."""
import json
import os
import stat
from pathlib import Path

HOME = Path(os.environ.get("JOBPILOT_HOME", Path.home() / ".jobpilot")).expanduser()


def engine_dir() -> Path:
    """Agent prompt, jobkit.sh and portal notes. Repo checkout: ../engine; installed wheel: ./engine."""
    here = Path(__file__).resolve().parent
    for p in (here / "engine", here.parent / "engine"):
        if (p / "jobkit.sh").exists():
            return p
    raise FileNotFoundError("engine/ directory not found")


PROFILE_MD = HOME / "profile.md"
PROFILE_JSON = HOME / "profile.json"
PROFILE_ENV = HOME / "profile.env"
SETTINGS = HOME / "settings.json"
SECRETS = HOME / "secrets.env"
DB = HOME / "jobpilot.db"
RESUMES = HOME / "resumes"
PROFILES = HOME / "browser-profiles"
BIN = HOME / "bin"
LOGS = HOME / "logs"
LEARNED = HOME / "portals-local.md"

DEFAULT_SETTINGS = {
    "workers": 2,
    "auto_submit": True,          # agents submit; turn off in Settings to review each form first (review lock)
    "model": "sonnet",
    "browser_path": "",
    "copy_profile_from": "",      # real browser profile copied into every worker without its own choice
    "worker_profiles": {},        # {"1": "<real profile dir>", ...}: per-worker override of copy_profile_from
    "keywords": [],
    "avoid_companies": [],
    "stack_accept": [],          # e.g. ["Python", "Go", "TypeScript/Node.js"]; empty = no stack filter
    "stack_skip": [],            # skip roles requiring any of these (languages, tools, keywords); works on its own
    "skip_easy_apply": True,
    "notif_max": 10,             # Find jobs: look at the last N job notifications…
    "notif_days": 3,             # …but none older than this many days
    "keyword_search": True,      # also run a LinkedIn search per keyword
    "search_location": "",
    "guidance": "",              # standing instructions added to every worker prompt (set from the agents chat)
    "otp_enabled": False,
    "active_resume": "",
    "onboarded": False,
}

SECRET_KEYS = ["email", "password", "password_strong", "gmail_user", "gmail_app_password", "pan"]


def ensure_dirs() -> None:
    for d in (HOME, RESUMES, PROFILES, BIN, LOGS):
        d.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    if SETTINGS.exists():
        s.update(json.loads(SETTINGS.read_text(encoding="utf-8") or "{}"))
    return s


def save_settings(s: dict) -> None:
    ensure_dirs()
    SETTINGS.write_text(json.dumps(s, indent=2), encoding="utf-8")


def load_secrets() -> dict:
    vals = {}
    if SECRETS.exists():
        for line in SECRETS.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def save_secrets(updates: dict) -> None:
    """Merge non-empty values only, so a blank (masked) form field never wipes a stored secret."""
    ensure_dirs()
    vals = load_secrets()
    vals.update({k: v.strip() for k, v in updates.items() if v and v.strip()})
    body = "".join(f"{k}='{v}'\n" for k, v in vals.items())
    SECRETS.write_text(body, encoding="utf-8", newline="\n")      # sourced by bash: LF only, even on Windows
    os.chmod(SECRETS, stat.S_IRUSR | stat.S_IWUSR)


def active_resume() -> Path | None:
    name = load_settings().get("active_resume")
    p = RESUMES / name if name else None
    if p and p.exists():
        return p
    pdfs = sorted(RESUMES.glob("*.pdf"))
    return pdfs[0] if pdfs else None
