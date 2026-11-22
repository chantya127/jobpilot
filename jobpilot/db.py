"""SQLite store: one `jobs` table is both the queue and the tracker; `events` holds live worker output."""
import csv
import datetime
import io
import re
import sqlite3
import urllib.parse

from . import config

STATUSES = ["queued", "running", "applied", "ready-for-review", "pending-user", "blocked", "skipped", "easy-apply",
            "failed"]
DONE = ("applied", "skipped")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  url TEXT NOT NULL,
  ukey TEXT NOT NULL UNIQUE,
  company TEXT DEFAULT '', role TEXT DEFAULT '', portal TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'queued',
  notes TEXT DEFAULT '', needs TEXT DEFAULT '',
  worker INTEGER, source TEXT DEFAULT 'manual',
  created TEXT, updated TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  job_id INTEGER, worker INTEGER, ts TEXT, kind TEXT, text TEXT
);
CREATE INDEX IF NOT EXISTS events_job ON events(job_id);
"""

_TRACK = re.compile(r"^(utm_.*|source|src|_src|ref|refid|gh_src|iis|iisn|medium|sourcetype|domain|lang|bid|cid|ss|"
                    r"feedid|target|jobpipeline|publisher|sid|mode|usp|ouid|brid|sbdid|rx_.*|amp;.*|trk|trackingid)$", re.I)


def ukey(u: str) -> str:
    """Job identity key. Unwraps redirect wrappers and drops only tracking params, so jobs whose id lives in the
    query (vacancyNo=, jobid=, gh_jid=) stay distinct."""
    u = u.strip()
    m = re.search(r"[?&]rx_url=([^&]+)", u)
    if m:
        u = urllib.parse.unquote(m.group(1))
    elif "?http" in u:
        u = u[u.index("?http") + 1:]
    p = urllib.parse.urlsplit(u)
    q = sorted((k.lower(), v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not _TRACK.match(k))
    frag = p.fragment if "job" in p.fragment.lower() else ""
    return (p.netloc.lower() + p.path.rstrip("/").lower() + ("?" + urllib.parse.urlencode(q) if q else "")
            + ("#" + frag if frag else ""))


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


_MIGRATED = False


def connect() -> sqlite3.Connection:
    global _MIGRATED
    config.ensure_dirs()
    c = sqlite3.connect(config.DB, timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    if not _MIGRATED:
        c.executescript(SCHEMA)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(jobs)")}
        if "stats" not in cols:            # per-agent-session stats: time, turns, tokens, cost (JSON)
            c.execute("ALTER TABLE jobs ADD COLUMN stats TEXT DEFAULT ''")
        _MIGRATED = True
    return c


def set_stats(job_id: int, stats: dict) -> None:
    import json
    with connect() as c:
        c.execute("UPDATE jobs SET stats=? WHERE id=?", (json.dumps(stats), job_id))


def stats_of(row) -> dict:
    import json
    try:
        return json.loads(row["stats"] or "{}")
    except (ValueError, KeyError, IndexError):
        return {}


def add_url(url: str, source: str = "manual") -> str:
    """Queue a URL. Returns 'added', 'duplicate' or 'invalid'."""
    url = url.strip()
    if not re.match(r"https?://", url):
        return "invalid"
    with connect() as c:
        try:
            c.execute("INSERT INTO jobs(url, ukey, source, created, updated) VALUES (?,?,?,?,?)",
                      (url, ukey(url), source, now(), now()))
            return "added"
        except sqlite3.IntegrityError:
            return "duplicate"


def log(url, company, role, portal, status, notes="", needs="", worker=None) -> None:
    """Insert or update the tracker row for this job (matched by ukey)."""
    k = ukey(url)
    with connect() as c:
        row = c.execute("SELECT id FROM jobs WHERE ukey=?", (k,)).fetchone()
        if row:
            c.execute("UPDATE jobs SET company=coalesce(nullif(?,''),company), role=coalesce(nullif(?,''),role),"
                      " portal=coalesce(nullif(?,''),portal), status=?, notes=?, needs=?, updated=?,"
                      " worker=coalesce(?,worker) WHERE id=?",
                      (company, role, portal, status, notes, needs, now(), worker, row["id"]))
        else:
            c.execute("INSERT INTO jobs(url,ukey,company,role,portal,status,notes,needs,worker,created,updated)"
                      " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (url, k, company, role, portal, status, notes, needs, worker, now(), now()))


def known(url: str) -> bool:
    """Any row for this job (queued, applied, skipped…)."""
    with connect() as c:
        return c.execute("SELECT 1 FROM jobs WHERE ukey=?", (ukey(url),)).fetchone() is not None


def is_done(url: str) -> bool:
    with connect() as c:
        r = c.execute("SELECT status FROM jobs WHERE ukey=?", (ukey(url),)).fetchone()
        return bool(r and r["status"] in DONE)


def set_status(job_id: int, status: str, **fields) -> None:
    cols = ", ".join(f"{k}=?" for k in fields)
    with connect() as c:
        c.execute(f"UPDATE jobs SET status=?, updated=?{', ' + cols if cols else ''} WHERE id=?",
                  (status, now(), *fields.values(), job_id))


def get(job_id: int):
    with connect() as c:
        return c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()


def jobs(status=None, limit=500):
    with connect() as c:
        if status:
            qs = status if isinstance(status, (list, tuple)) else [status]
            return c.execute(f"SELECT * FROM jobs WHERE status IN ({','.join('?' * len(qs))})"
                             " ORDER BY updated DESC LIMIT ?", (*qs, limit)).fetchall()
        return c.execute("SELECT * FROM jobs ORDER BY updated DESC LIMIT ?", (limit,)).fetchall()


def queued():
    with connect() as c:
        return c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id").fetchall()


def delete(job_id: int) -> None:
    with connect() as c:
        c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        c.execute("DELETE FROM events WHERE job_id=?", (job_id,))


def counts() -> dict:
    with connect() as c:
        return {r["status"]: r["n"] for r in c.execute("SELECT status, count(*) n FROM jobs GROUP BY status")}


def add_event(job_id, worker, kind, text) -> None:
    with connect() as c:
        c.execute("INSERT INTO events(job_id,worker,ts,kind,text) VALUES (?,?,?,?,?)",
                  (job_id, worker, now(), kind, text[:2000]))


def events(job_id, limit=40):
    with connect() as c:
        rows = c.execute("SELECT * FROM events WHERE job_id=? ORDER BY id DESC LIMIT ?", (job_id, limit)).fetchall()
        return list(reversed(rows))


def events_after(job_id, after: int = 0, limit: int = 300):
    with connect() as c:
        return c.execute("SELECT * FROM events WHERE job_id=? AND id>? ORDER BY id LIMIT ?",
                         (job_id, after, limit)).fetchall()


def reset_running() -> None:
    """After a crash/restart, nothing is actually running: put those jobs back in the queue."""
    with connect() as c:
        c.execute("UPDATE jobs SET status='queued', worker=NULL WHERE status='running'")


def export_csv() -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["url", "company", "role", "portal", "status", "date", "notes"])
    for r in jobs(limit=100000):
        w.writerow([r["url"], r["company"], r["role"], r["portal"], r["status"], (r["updated"] or "")[:10], r["notes"]])
    return buf.getvalue()


def import_csv(text: str) -> int:
    """Import an existing tracker.csv (url,company,role,portal,status,date,notes)."""
    n = 0
    for r in csv.DictReader(io.StringIO(text)):
        if r.get("url"):
            log(r["url"], r.get("company", ""), r.get("role", ""), r.get("portal", ""),
                r.get("status") or "applied", r.get("notes", ""))
            n += 1
    return n
