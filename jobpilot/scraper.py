"""Find jobs on LinkedIn and add their company apply URLs to the queue.

Runs in worker 1's browser (log in to LinkedIn there once from the dashboard). Two sources:
  1. your LinkedIn job-alert notifications: scrolls back through the notifications page until it has the last
     `notif_max` job notifications or reaches ones older than `notif_days` days, keeps those matching your keywords,
     and skips notifications and jobs it has already seen
  2. optionally, a LinkedIn job search per keyword (past 24 h, optional location)
Easy Apply jobs are never automated: they are listed in the tracker as `easy-apply` for you to do by hand.

Output lines start with a tag the dashboard renders: [head] [info] [queued] [known] [easy] [skip] [error] [done].
Run: python -m jobpilot.scraper   (the dashboard's "Find jobs" button does this)
"""
import random
import re
import sys
import time
from urllib.parse import parse_qs, quote_plus, urlencode, urljoin, urlparse

from playwright.sync_api import Page, sync_playwright

from . import browser, config, db

MAX_PAGES = 3
MAX_JOBS_PER_PAGE = 25
SEEN_JOBS = config.HOME / "seen_jobs.txt"
SEEN_NOTIFS = config.HOME / "seen_notifications.txt"

AVOID: list[str] = []


def say(msg: str, tag: str = "info") -> None:
    print(f"[{tag}] {msg}", flush=True)


_AGE = re.compile(r"(?:^|\s)(\d+)\s?(mo|months?|y|yrs?|years?|w|wks?|weeks?|d|days?|h|hrs?|hours?|m|mins?|minutes?|s)"
                  r"(?:\s+ago)?\s*$", re.I)
_DAYS = {"s": 0, "m": 0, "h": 0, "d": 1, "w": 7, "mo": 30, "y": 365}


def age_days(text: str) -> float | None:
    """Age of a notification from its relative timestamp ('5h', '2d', '1w', '3mo', '2 days ago'); None if unknown.
    LinkedIn puts the timestamp on its own line, so check each line from the end."""
    for line in reversed([l.strip() for l in text.splitlines() if l.strip()][-4:]):
        m = _AGE.search(line)
        if m:
            n, unit = int(m.group(1)), m.group(2).lower()
            key = "mo" if unit.startswith("mo") else unit[0]
            if key == "m" and unit in ("m", "min", "mins", "minute", "minutes"):
                return 0.0
            return n * _DAYS[key] if key in ("d", "w", "mo", "y") else n / (24 if key == "h" else 1440)
    return None


_NOTIFS_JS = """() => {const out=[],seen=new Set();
  for (const a of document.querySelectorAll('a[href*="/jobs/search-results/"],a[href*="/jobs/view/"],a[href*="/jobs/collections/"],a[href*="/jobs/search/"]')){
    if(!a.href||seen.has(a.href))continue;let c=a;for(let i=0;i<10&&c.parentElement;i++){if(c.parentElement.children.length>=3)break;c=c.parentElement;}
    const t=c.innerText?.trim()||'';if(t.length<10)continue;seen.add(a.href);out.push({text:t.substring(0,400),url:a.href});}
  return out;}"""


def load_notifications(page: Page, max_n: int, max_days: float) -> list[dict]:
    """Scroll the notifications page back until we have `max_n` job notifications, or the oldest one is older than
    `max_days`, or nothing new loads. Returns newest-first notifications within the day limit (at most max_n)."""
    found, stalled = [], 0
    for step in range(60):
        cur = page.evaluate(_NOTIFS_JS)
        new = [n for n in cur if n["url"] not in {f["url"] for f in found}]
        found.extend(new)
        ages = [a for a in (age_days(n["text"]) for n in found) if a is not None]
        oldest = max(ages) if ages else 0
        if new:
            say(f"loaded {len(found)} job notifications (oldest {oldest:.1f} days)")
        if len(found) >= max_n or oldest > max_days:
            break
        stalled = 0 if new else stalled + 1
        if stalled >= 3:
            break
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        more = page.query_selector('button:has-text("Show more results"), button:has-text("Load more")')
        if more and more.is_visible():
            more.click()
        nap(1.5, 2.8)
    within = [n for n in found if (age_days(n["text"]) or 0) <= max_days]
    return within[:max_n]


def nap(a, b):
    time.sleep(random.uniform(a, b))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()


def avoided_company(company: str = "", url: str = "") -> str | None:
    """Whole-word match on the company name, or the name (spaces removed) equals a URL host/path segment."""
    company_n = _norm(company) if company else ""
    tokens = set()
    if url:
        p = urlparse(url.strip())
        tokens = {t for t in re.split(r"[^a-z0-9]+", (p.netloc + p.path).lower()) if t}
    for name in AVOID:
        if company_n and re.search(rf"\b{re.escape(name)}\b", company_n):
            return name
        if tokens and name.replace(" ", "") in tokens:
            return name
    return None


def resolve_linkedin_redirect(href: str) -> str:
    parsed = urlparse(href)
    if "linkedin.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        for key in ("url", "redirect", "dest"):
            if params.get(key):
                return params[key][0]
    return href


def lines(path) -> set[str]:
    return {l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()} if path.exists() else set()


def append(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def notification_key(n: dict) -> str:
    text = re.sub(r"\s+", " ", n["text"].lower())
    text = re.sub(r"\b\d+\s*(s|m|h|d|w|mo|y|yr|yrs|mins?|minutes?|hours?|days?|weeks?|months?|years?)\b(\s+ago)?", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return n["url"].strip() + "\t" + text


_CARD = '[role="button"][componentkey^="job-card-component-ref-"], [data-occludable-job-id], [data-job-id]'
_CARDS_JS = """
const CARD_SELECTOR = '""" + _CARD.replace("'", "\\'") + """';
function jobIdOf(el){const key=el.getAttribute('componentkey')||'';const m=key.match(/^job-card-component-ref-(\\d+)$/);
 if(m)return m[1];const a=el.getAttribute('data-occludable-job-id')||el.getAttribute('data-job-id');return a&&/^\\d+$/.test(a)?a:null;}
function findJobCards(){const cards=[],seen=new Set();for(const el of document.querySelectorAll(CARD_SELECTOR)){
 const id=jobIdOf(el);if(!id||seen.has(id))continue;seen.add(id);cards.push({el,id});}return cards;}
function findListScroller(){const f=findJobCards()[0];let el=f?f.el.parentElement:null;
 while(el&&el!==document.body){const s=getComputedStyle(el);if(/(auto|scroll)/.test(s.overflowY)&&el.scrollHeight>el.clientHeight)return el;el=el.parentElement;}
 return document.scrollingElement;}
"""


def collect_job_ids(page: Page) -> list[str]:
    try:
        page.wait_for_selector(_CARD, timeout=15_000)
    except Exception:
        return []
    time.sleep(2)
    ids, stalled = [], 0
    for _ in range(40):
        r = page.evaluate("() => {" + _CARDS_JS + """
            const ids=[...new Set(findJobCards().map(c=>c.id))];const sc=findListScroller();const before=sc.scrollTop;
            sc.scrollBy(0,Math.max(300,sc.clientHeight*0.8));
            return {ids, atBottom: sc.scrollTop===before || sc.scrollTop+sc.clientHeight>=sc.scrollHeight-5};}""")
        new = [i for i in r["ids"] if i not in ids]
        ids.extend(new)
        stalled = 0 if new else stalled + 1
        if r["atBottom"] and stalled >= 2:
            break
        nap(0.6, 1.2)
    return ids


def next_page(page: Page, n: int) -> bool:
    for sel in (f'button[aria-label="Page {n}"]', 'button[data-testid="pagination-controls-next-button-visible"]',
                'button[aria-label="View next page"]', 'button.jobs-search-pagination__button--next'):
        btn = page.query_selector(sel)
        if btn and btn.is_enabled():
            btn.scroll_into_view_if_needed()
            btn.click()
            nap(3, 5)
            return True
    p = urlparse(page.url)
    q = parse_qs(p.query)
    q["start"] = [str((n - 1) * 25)]
    q.pop("currentJobId", None)
    try:
        page.goto(p._replace(query=urlencode(q, doseq=True)).geturl(), wait_until="domcontentloaded", timeout=60_000)
        nap(3, 5)
        return True
    except Exception as e:
        say(f"  could not open page {n}: {e}")
        return False


def fetch_apply_method(page: Page, job_id: str) -> dict | None:
    """LinkedIn's internal job feed (undocumented, may change): easy / external(url) / closed."""
    try:
        js = next((c["value"] for c in page.context.cookies("https://www.linkedin.com") if c["name"] == "JSESSIONID"), None)
        if not js:
            return None
        resp = page.context.request.get(f"https://www.linkedin.com/voyager/api/jobs/jobPostings/{job_id}",
                                        headers={"csrf-token": js.strip('"'), "x-restli-protocol-version": "2.0.0",
                                                 "accept": "application/json"}, timeout=15_000)
        if not resp.ok:
            return None
        data = resp.json()
    except Exception:
        return None
    title, company = data.get("title") or "", ""
    for v in (data.get("companyDetails") or {}).values():
        if isinstance(v, dict):
            company = (v.get("companyResolutionResult") or {}).get("name") or v.get("companyName") or ""
            if company:
                break
    if data.get("jobState") and data["jobState"] != "LISTED":
        return {"kind": "closed", "title": title, "company": company}
    for key, value in (data.get("applyMethod") or {}).items():
        if key.endswith("OffsiteApply") and value.get("companyApplyUrl"):
            return {"kind": "external", "title": title, "company": company,
                    "url": resolve_linkedin_redirect(value["companyApplyUrl"])}
        if key.endswith("OnsiteApply"):
            return {"kind": "easy", "title": title, "company": company}
    return None


def handle_job(page: Page, job_id: str, stats: dict) -> bool:
    job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
    if db.known(job_url):
        stats["known"] += 1
        return True
    info = fetch_apply_method(page, job_id)
    if not info:
        # fallback: read the Apply link from the job page
        try:
            page.goto(job_url, wait_until="domcontentloaded", timeout=45_000)
            nap(2, 3)
            if page.query_selector('button[aria-label*="Easy Apply"], a[aria-label*="Easy Apply"]'):
                info = {"kind": "easy", "title": page.title(), "company": ""}
            else:
                a = page.query_selector('a[aria-label*="Apply"]:not([aria-label*="Easy Apply"])')
                href = a.get_attribute("href") if a else None
                if not href:
                    stats["error"] += 1
                    return False
                info = {"kind": "external", "title": page.title(), "company": "",
                        "url": resolve_linkedin_redirect(urljoin(page.url, href))}
        except Exception as e:
            say(f"{job_url} · {e}", "error")
            stats["error"] += 1
            return False
    title = info.get("title", "")[:80]
    company = info.get("company", "")
    label = f"{company} · {title}" if company else title
    av = avoided_company(company, info.get("url", ""))
    if av:
        say(f"{label} · avoid list: {av}", "skip")
        stats["avoided"] += 1
    elif info["kind"] == "easy":
        db.log(job_url, company, info.get("title", ""), "LinkedIn Easy Apply", "easy-apply",
               "Easy Apply is never automated: apply by hand")
        say(f"{label} · Easy Apply, yours to do", "easy")
        stats["easy"] += 1
    elif info["kind"] == "external":
        r = db.add_url(info["url"], source="linkedin")
        if r == "added":
            db.log(info["url"], company, info.get("title", ""), "", "queued", "Found on LinkedIn")
            stats["queued"] += 1
            say(f"{label} · {urlparse(info['url']).netloc}", "queued")
        else:
            stats["known"] += 1
            say(f"{label} · already in queue/tracker", "known")
    else:
        say(f"{label} · closed", "skip")
        stats["closed"] += 1
    nap(0.5, 1.2)
    return True


def process_results(page: Page, stats: dict, seen: set[str]) -> None:
    for n in range(1, MAX_PAGES + 1):
        if n > 1 and not next_page(page, n):
            break
        results_url = page.url
        ids = collect_job_ids(page)
        new = [i for i in ids if i not in seen]
        say(f"results page {n}: {len(ids)} jobs, {len(new)} not seen before")
        if not new:
            break
        for job_id in new[:MAX_JOBS_PER_PAGE]:
            seen.add(job_id)
            if handle_job(page, job_id, stats):
                append(SEEN_JOBS, job_id)
        if page.url != results_url:   # the click fallback navigated away
            page.goto(results_url, wait_until="domcontentloaded", timeout=60_000)


def main() -> None:
    s = config.load_settings()
    keywords = [k.strip().lower() for k in s.get("keywords", []) if k.strip()]
    AVOID.extend(n for n in (_norm(x) for x in s.get("avoid_companies", [])) if n)
    location = s.get("search_location", "")
    max_n = int(s.get("notif_max") or 10)
    max_days = float(s.get("notif_days") or 3)
    seen, seen_n = lines(SEEN_JOBS), lines(SEEN_NOTIFS)
    stats = {"queued": 0, "known": 0, "easy": 0, "avoided": 0, "closed": 0, "error": 0}

    browser.write_wrappers(max(1, int(s.get("workers", 2))))
    browser.launch(1)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{browser.port(1)}")
        ctx = b.contexts[0] if b.contexts else b.new_context()
        page = ctx.new_page()
        try:
            say("notifications", "phase")
            say(f"Job notifications: last {max_n}, up to {max_days:g} days old", "head")
            page.goto("https://www.linkedin.com/notifications/", wait_until="domcontentloaded", timeout=60_000)
            if "login" in page.url or "authwall" in page.url:
                say("Not logged in: log in to LinkedIn in the worker 1 window (Settings → Open worker browser), then retry.",
                    "error")
                sys.exit(2)
            time.sleep(5)
            notifs = load_notifications(page, max_n, max_days)
            todo = []
            for n in notifs:
                first = n["text"].splitlines()[0][:90]
                if notification_key(n) in seen_n:
                    say(f"{first} · seen before", "known")
                elif keywords and not any(kw in (n["text"] + " " + n["url"]).lower() for kw in keywords):
                    say(f"{first} · no keyword match", "skip")
                else:
                    todo.append(n)
            say(f"{len(notifs)} notifications in range, {len(todo)} new and matching")
            for i, n in enumerate(todo, 1):
                age = age_days(n["text"])
                say(f"Notification {i}/{len(todo)} · {n['text'].splitlines()[0][:90]}"
                    + (f" · {age:.0f}d ago" if age and age >= 1 else ""), "head")
                errs = stats["error"]
                page.goto(n["url"], wait_until="domcontentloaded", timeout=60_000)
                process_results(page, stats, seen)
                if stats["error"] == errs:
                    append(SEEN_NOTIFS, notification_key(n))
                nap(3, 5)
            searches = keywords if s.get("keyword_search", True) else []
            if searches:
                say("search", "phase")
            for kw in searches:
                say(f"Search · {kw}" + (f" · {location}" if location else ""), "head")
                url = (f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(kw)}&f_TPR=r86400"
                       + (f"&location={quote_plus(location)}" if location else ""))
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                process_results(page, stats, seen)
                nap(3, 5)
        finally:
            try:
                page.close()
            except Exception:
                pass
    say(f"{stats['queued']} queued · {stats['known']} already known · {stats['easy']} Easy Apply · "
        f"{stats['avoided']} avoided · {stats['closed']} closed · {stats['error']} errors", "done")


if __name__ == "__main__":
    main()
