"""The user's knowledge base.

profile.json  structured standard answers (edited in the dashboard form)
profile.md    free-form: experience bullets, ready-made answers, "Answers learned" table (edited as markdown)
profile.env   generated from profile.json, sourced by jobkit.sh so the bash helpers fill the user's own values
answers.md    generated from profile.json, read by the worker as its "Standard answers"
"""
import json
import shlex

from . import config

FIELDS = [
    # (key, label, section, placeholder)
    ("first_name", "First name", "Personal", ""),
    ("last_name", "Last name", "Personal", ""),
    ("salutation", "Salutation", "Personal", "Mr / Ms / Mx"),
    ("gender", "Gender (for EEO forms)", "Personal", "or 'Decline to answer'"),
    ("email", "Email", "Personal", ""),
    ("phone_country_code", "Phone country code", "Personal", "+91"),
    ("phone", "Phone (national number, no country code)", "Personal", ""),
    ("address1", "Address line 1", "Address", ""),
    ("address2", "Address line 2", "Address", ""),
    ("city", "City", "Address", ""),
    ("state", "State / region", "Address", ""),
    ("postal_code", "Postal code", "Address", ""),
    ("country", "Country", "Address", ""),
    ("linkedin", "LinkedIn URL", "Links", "https://www.linkedin.com/in/..."),
    ("github", "GitHub URL", "Links", ""),
    ("portfolio", "Portfolio / website", "Links", ""),
    ("current_ctc", "Current compensation", "Pay & availability", "e.g. 20 LPA (2000000) or USD 120k"),
    ("expected_ctc", "Expected compensation", "Pay & availability", "e.g. Negotiable; 25 LPA if a number is required"),
    ("notice_period", "Notice period", "Pay & availability", "e.g. 30 days"),
    ("total_experience", "Total experience (years)", "Experience", "e.g. 4.5"),
    ("skill_years", "Years per skill", "Experience", "Python 4, AWS 3, Go 1, Java 0"),
    ("mobility", "Relocation / work mode", "Eligibility", "Relocate anywhere in India; remote/hybrid/onsite OK"),
    ("work_authorization", "Work authorization", "Eligibility", "Citizen of India, no sponsorship needed"),
    ("veteran", "Veteran status", "EEO", "Not a protected veteran"),
    ("disability", "Disability", "EEO", "Decline to answer"),
    ("race", "Race / ethnicity", "EEO", "Decline to answer"),
    ("degree", "Degree", "Education", "B.E. Computer Science"),
    ("school", "School / university", "Education", ""),
    ("education_years", "Education years", "Education", "2018-2022"),
    ("grade", "Grade / GPA", "Education", ""),
    ("source", "How did you hear about us", "Other", "LinkedIn"),
    ("default_no", "Questions that are always 'No'", "Other",
     "competing offers, non-compete, relatives at the company, government employee"),
    ("ai_tools", "AI tools you use", "Other", "Claude Code, Cursor"),
]

WORK_FIELDS = ["company", "title", "start", "end", "location"]   # start/end as MM/YYYY; end blank = current

# Fields edited as multi-select chips (preset options + your own custom answers). Stored as "a; b; c".
OPTIONS = {
    "gender": ["Male", "Female", "Non-binary", "Decline to answer"],
    "mobility": ["Open to relocate anywhere in the country", "Remote OK", "Hybrid OK", "Onsite OK",
                 "5-day work from office OK", "Shifts / late overlap OK", "Travel up to 25%", "Travel up to 50%",
                 "Not open to relocation"],
    "work_authorization": ["Citizen of my country of residence", "Authorized to work without sponsorship",
                           "Will require visa sponsorship", "Hold a valid passport", "Over 18",
                           "Permanent resident", "Work permit holder"],
    "veteran": ["Not a protected veteran", "Protected veteran", "Decline to answer"],
    "disability": ["No disability", "Yes, I have a disability", "Decline to answer"],
    "race": ["Decline to answer", "Asian", "Black or African American", "Hispanic or Latino", "White",
             "Two or more races", "Native Hawaiian or Pacific Islander", "American Indian or Alaska Native",
             "Not Hispanic or Latino"],
    "default_no": ["Competing offers", "Employment gap", "Non-compete / NDA restrictions",
                   "Previously worked at the company", "Relatives at the company", "Relatives in government",
                   "Government employee", "Medical conditions affecting work", "Criminal record",
                   "Previously applied in last 6 months"],
    "source": ["LinkedIn", "Company website", "Referral", "Job board", "Naukri", "Indeed", "Glassdoor", "Other"],
}
SINGLE = {"gender", "veteran", "disability", "source"}   # pick one (plus custom); others allow many

PROFILE_MD_TEMPLATE = """# Application knowledge base

## Summary
<!-- 3-5 lines about you: role, years, main stack, what you are looking for. -->

## Work experience
<!-- One block per job: company, title, dates, 3-6 bullet points with concrete numbers. -->

## Skills

## Achievements

## Ready-made short answers
<!-- "Why do you want to join?", "Describe a challenging project", etc. Agents reuse these in essays. -->

## Answers learned during applications
| Question | Answer |
|---|---|
"""


def load() -> dict:
    p = json.loads(config.PROFILE_JSON.read_text(encoding="utf-8")) if config.PROFILE_JSON.exists() else {}
    p.setdefault("work", [])
    return p


def load_md() -> str:
    return config.PROFILE_MD.read_text(encoding="utf-8") if config.PROFILE_MD.exists() else PROFILE_MD_TEMPLATE


def save_md(text: str) -> None:
    config.ensure_dirs()
    config.PROFILE_MD.write_text(text, encoding="utf-8")


def save(p: dict) -> None:
    config.ensure_dirs()
    config.PROFILE_JSON.write_text(json.dumps(p, indent=2), encoding="utf-8")
    render(p)


def full_name(p: dict) -> str:
    return " ".join(x for x in (p.get("first_name"), p.get("last_name")) if x)


def render(p: dict | None = None) -> None:
    """Write profile.env (for jobkit.sh) and answers.md (for the worker prompt)."""
    p = p if p is not None else load()
    s = config.load_settings()
    resume = config.active_resume()
    work = [w for w in p.get("work", []) if w.get("company")]
    cur = next((w for w in work if not w.get("end")), work[0] if work else {})
    start = (cur.get("start") or "").split("/")
    env = {
        "JP_FIRST": p.get("first_name", ""), "JP_LAST": p.get("last_name", ""), "JP_FULL": full_name(p),
        "JP_TITLE": p.get("salutation", ""), "JP_EMAIL": p.get("email", ""),
        "JP_PHONE": p.get("phone", ""), "JP_PHONE_CC": p.get("phone_country_code", ""),
        "JP_ADDR1": p.get("address1", ""), "JP_ADDR2": p.get("address2", ""), "JP_CITY": p.get("city", ""),
        "JP_STATE": p.get("state", ""), "JP_POSTAL": p.get("postal_code", ""), "JP_COUNTRY": p.get("country", ""),
        "JP_LINKEDIN": p.get("linkedin", ""), "JP_SOURCE": p.get("source", "") or "LinkedIn",
        "JP_COMPANIES": "|".join(w["company"] for w in work),
        "JP_WORK_CITY": ", ".join(x for x in (p.get("city"), p.get("country")) if x),
        "JP_CUR_START_MONTH": start[0] if len(start) == 2 else "",
        "JP_CUR_START_YEAR": start[1] if len(start) == 2 else "",
        "JP_DEGREE": p.get("degree", ""),
        "JP_RESUME": resume.as_posix() if resume else "",      # bash path form (Git Bash on Windows)
    }
    config.PROFILE_ENV.write_text("".join(f"export {k}={shlex.quote(v)}\n" for k, v in env.items()),
                                  encoding="utf-8", newline="\n")

    lines = ["# Standard answers (generated from the dashboard profile; profile.md's 'Answers learned' wins)", ""]
    for key, label, _section, _ph in FIELDS:
        v = p.get(key)
        if v:
            lines.append(f"- **{label}:** {v}")
    if work:
        lines.append("- **Work history (resume parsers often drop employers or start dates; fix them):** " + " · ".join(
            f"{w['company']}, {w.get('title', '')}, {w.get('start', '?')}–{w.get('end') or 'present'}"
            + (f", {w['location']}" if w.get("location") else "") for w in work))
    lines += [
        f"- **Phone rule:** type `{p.get('phone', '')}` in the number field and pick {p.get('phone_country_code', '')}"
        " in the country-code control; never put the country code inside the number field (autofill often does: fix it).",
        "- **Consents:** tick required terms/privacy/e-signature" + (f" (sign \"{full_name(p)}\")" if full_name(p) else "")
        + ". Decline marketing, SMS, WhatsApp and talent-pool opt-ins.",
        "- **AI disclosure:** if a form asks whether an AI assistant or agent is filling it in, answer truthfully: yes.",
        "- **Essays:** build only from facts in profile.md; never invent experience, metrics, incidents or dates.",
    ]
    if s.get("stack_accept"):
        lines.append(f"- **Stack:** {', '.join(s['stack_accept'])}.")
    (config.HOME / "answers.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def completeness(p: dict | None = None) -> tuple[int, list[str]]:
    p = p if p is not None else load()
    need = ["first_name", "last_name", "email", "phone", "city", "country", "notice_period", "work_authorization"]
    missing = [label for key, label, *_ in FIELDS if key in need and not p.get(key)]
    return int(100 * (len(need) - len(missing)) / len(need)), missing
