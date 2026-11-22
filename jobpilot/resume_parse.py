"""Resume PDF -> draft profile (profile.json fields + profile.md knowledge base) using the user's Claude Code login."""
import json
import re
import subprocess

from pypdf import PdfReader

from . import profile
from .procs import child_env, exe, group_kwargs

PROMPT = """Extract a job-application profile from this resume. Reply with ONLY a JSON object, no prose, with keys:
"fields": object with any of these keys you can fill from the resume (omit unknown ones, never guess):
  {keys}
  Phone: national number only (no country code) in "phone", country code like "+91" in "phone_country_code".
"work": list of {{"company","title","start","end","location"}} newest first; dates as MM/YYYY; "end" "" if current.
"markdown": a knowledge-base document in markdown with sections "## Summary", "## Work experience" (each job with its
bullets copied faithfully), "## Skills", "## Education", "## Achievements". Do not invent anything.

RESUME:
{text}
"""


def pdf_text(path) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)


def draft(path) -> dict:
    text = pdf_text(path)[:20000]
    if not text.strip():
        raise ValueError("No text found in the PDF (is it a scanned image?)")
    keys = ", ".join(k for k, *_ in profile.FIELDS)
    out = subprocess.run([exe("claude"), "-p", "--model", "sonnet", "--output-format", "json", "--tools", ""],
                         input=PROMPT.format(keys=keys, text=text), capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=child_env(), timeout=240, **group_kwargs())
    if out.returncode != 0:
        raise RuntimeError(f"claude failed: {(out.stderr or out.stdout)[-400:]}")
    result = json.loads(out.stdout).get("result", "")
    m = re.search(r"\{[\s\S]*\}", result)
    if not m:
        raise RuntimeError("Could not read the extracted profile")
    return json.loads(m.group(0))


def apply(path) -> dict:
    """Merge the draft into the existing profile without overwriting anything the user already filled."""
    d = draft(path)
    p = profile.load()
    for k, v in (d.get("fields") or {}).items():
        if v and not p.get(k):
            p[k] = str(v)
    if not p.get("work") and d.get("work"):
        p["work"] = [{k: str(w.get(k) or "") for k in profile.WORK_FIELDS} for w in d["work"]]
    profile.save(p)
    md = profile.load_md()
    if d.get("markdown") and md.strip() == profile.PROFILE_MD_TEMPLATE.strip():
        profile.save_md(d["markdown"].rstrip() + "\n\n## Ready-made short answers\n\n"
                        "## Answers learned during applications\n| Question | Answer |\n|---|---|\n")
    return p
