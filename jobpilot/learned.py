"""The "Answers learned" table in profile.md: answers the user gave in Needs you, stored as reusable facts.

Agents ask questions with job-specific context mixed in ("Harvey's Bengaluru role is hybrid... Worker 2, tab t2.
Pick the option and click Submit"). Stored verbatim, such a row is hard to reuse on the next job, so before saving we
ask Claude to turn it into generic one-fact rows ("Able to work from the office 3 days a week (hybrid)?" | "Yes"),
splitting multi-part questions. If Claude isn't available the text is cleaned up with simple rules instead.
"""
import json
import re
import subprocess

from . import profile
from .procs import child_env, exe, group_kwargs

HEADING = "## Answers learned during applications"
TABLE_HEAD = "| Question | Answer |\n|---|---|\n"

PROMPT = """You maintain a job applicant's knowledge base of reusable screening answers. Rewrite the raw
question/answer pairs below into clean rows that an agent filling ANY future job application can reuse.

Rules:
- One fact per row. Split multi-part questions into separate rows (e.g. address line, postal code, salutation; or
  each numbered "experience with X?" item). If the answer covers several parts ("yes to all"), give each row its part.
- Generic questions: remove company names, role/city specifics that don't change the fact, worker/tab ids, and any
  instructions ("pick the option", "click Submit", "fill step 4"). Keep qualifiers that matter (e.g. "3 days a week",
  "in INR", "annual").
- Drop parts that are not questions about the applicant (e.g. "tick the privacy box", "pick the Location").
- Answers: short and factual, using ONLY what the applicant wrote. Keep their numbers, currencies, units and spelling
  of names/addresses exactly; never invent or convert anything. For multiple choice, the answer is the chosen option.
- Merge rows that ask the same thing; the later pair wins.
- If a row asks the same thing as one of the EXISTING QUESTIONS below, use that exact question text (so it replaces
  the old answer instead of duplicating it).

Reply with ONLY a JSON array of objects {{"question": "...", "answer": "..."}}, no prose.

EXISTING QUESTIONS (JSON):
{existing}

RAW PAIRS (JSON):
{pairs}
"""

_NOISE = re.compile(
    r"[^.?!]*\b(worker\s*\d+|tab\s+t?\d+|click|submit|fill (them|it)|step\s*\d)\b[^.?!]*[.?!]?", re.I)


def _cell(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).replace("|", "/").strip()


def _key(q: str) -> str:
    return re.sub(r"[^a-z0-9]", "", q.lower())


def _fallback(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out = []
    for q, a in pairs:
        cleaned = _NOISE.sub("", q).strip()
        out.append((cleaned if "?" in cleaned else q, a))
    return out


def generalize(pairs: list[tuple[str, str]], existing: list[str] | None = None,
               timeout: int = 90) -> list[tuple[str, str]]:
    """Raw (question, answer) pairs -> generic one-fact rows. Never raises: falls back to rule-based cleanup."""
    pairs = [(q, a) for q, a in pairs if q.strip() and a.strip()]
    if not pairs:
        return []
    raw = json.dumps([{"question": q, "answer": a} for q, a in pairs], ensure_ascii=False)
    have = json.dumps(existing or [], ensure_ascii=False)
    try:
        out = subprocess.run([exe("claude"), "-p", "--model", "haiku", "--output-format", "json", "--tools", ""],
                             input=PROMPT.format(pairs=raw, existing=have), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", env=child_env(), timeout=timeout, **group_kwargs())
        result = json.loads(out.stdout).get("result", "") if out.returncode == 0 else ""
        m = re.search(r"\[[\s\S]*\]", result)
        rows = [(r.get("question", ""), r.get("answer", "")) for r in json.loads(m.group(0))] if m else []
        rows = [(q, a) for q, a in rows if str(q).strip() and str(a).strip()]
        if rows:
            return rows
    except Exception:
        pass
    return _fallback(pairs)


def _split(md: str) -> tuple[str, list[tuple[str, str]], str]:
    """profile.md -> (text up to and including the section heading, table rows, everything after the table)."""
    i = md.find("## Answers learned")
    if i < 0:
        return md.rstrip("\n") + "\n\n" + HEADING + "\n", [], ""
    end_head = md.find("\n", i)
    head = md[:end_head + 1] if end_head >= 0 else md + "\n"
    lines = md[len(head):].split("\n")
    rows, other, n = [], [], len(lines)
    for j, line in enumerate(lines):
        s = line.strip()
        if s.startswith("## "):
            n = j
            break
        if not s.startswith("|"):
            if s:
                other.append(line)      # stray notes inside the section are kept, below the table
        elif not re.fullmatch(r"\|[\s:|-]*\|", s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 2 and cells[0].lower() != "question":
                rows.append((cells[0], " / ".join(cells[1:])))
    rest = "\n".join(other + [""] + lines[n:]).strip("\n")
    return head, rows, ("\n" + rest + "\n" if rest else "")


def _merge(rows: list[tuple[str, str]], new: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """A new row asking the same question replaces the old answer in place."""
    rows, index = list(rows), {_key(q): i for i, (q, _) in enumerate(rows)}
    for q, a in new:
        k = _key(q)
        if k in index:
            rows[index[k]] = (q, a)
        else:
            index[k] = len(rows)
            rows.append((q, a))
    return rows


def _write(head: str, rows: list[tuple[str, str]], rest: str) -> None:
    table = TABLE_HEAD + "".join(f"| {_cell(q)} | {_cell(a)} |\n" for q, a in rows)
    profile.save_md(head + table + rest)


def learn(question: str, answer: str) -> list[tuple[str, str]]:
    """Save one answer from Needs you as generic rows. Returns the rows saved."""
    head, rows, rest = _split(profile.load_md())
    new = generalize([(question, answer)], existing=[q for q, _ in rows])
    _write(head, _merge(rows, new), rest)
    return new


def tidy() -> int:
    """Rewrite the whole existing table into generic rows (one-time cleanup of older verbatim entries)."""
    head, rows, rest = _split(profile.load_md())
    if not rows:
        return 0
    new = _merge([], generalize(rows, timeout=180))
    _write(head, new, rest)
    return len(new)
