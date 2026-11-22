# Job-apply worker reference

Read this at the start of every job, then ONLY the one portal file you need (see "Portal notes"). Answers come from
`$JP_HOME/answers.md` (standard answers) and `$JP_HOME/profile.md` (experience, ready-made answers, and the
"Answers learned" table, which overrides everything else).

## Shell setup (every Bash call)
Each Bash call is a fresh shell, so start every call with:
```bash
cd "$JP_HOME" && source "$JP_ENGINE/jobkit.sh" <W>
```
`<W>` is your worker number. Then use `$AB` (never call agent-browser directly). Each worker has its own browser
window. Your `$AB` session is pinned to the tab you open with `$AB tab new`. Never switch to (`$AB tab <n>`), close or
reload a tab you didn't open, unless you were handed a specific tab id to resume.
Note: `$AB eval` shares one JS scope per page, so wrap code in `(()=>{...})()` to avoid "already declared".

Profile values are exported as env vars (`$JP_FIRST`, `$JP_LAST`, `$JP_EMAIL`, `$JP_PHONE`, `$JP_CITY`, `$JP_RESUME`…).
Portal account credentials: run `creds` to load `$email`, `$password`, `$password_strong`, `$pan`. **Never print or echo them.**

## Email codes / verification links (IMAP)
Only if email codes are enabled (the job prompt tells you). After a portal sends a code (it polls up to 75 s, prints only the code):
```bash
CODE=$(otp --match <Company> --len 8)    # Greenhouse security code (subject has the company name)
CODE=$(otp --match "oracle" --len 6)     # 6-digit OTPs (Oracle, Hirist, Keka...)
otp --match myworkday --link             # Workday account verification link -> $AB open it
otp --list --timeout 0                   # debug: newest senders/subjects
```
Use `--match` with the company/portal name so parallel workers don't steal each other's codes. A very small `--since`
(e.g. 5) can miss a code that has already arrived. Exit code 1 = nothing arrived → return pending-user (leave the tab
open at the code prompt). Greenhouse code goes into 8 inputs: `$AB click "#security-input-0"; $AB keyboard type "$CODE"`,
verify all 8 filled, Submit. If email codes are disabled: fill everything up to the code prompt and return pending-user
with `NEEDS: enter the email code from <sender> in worker <W> tab <id>`.

## Passwords
- Use `$password`. If a NEW account rejects it for strength rules, use `$password_strong` and note "strong pw" in the tracker notes.
- Many portals reject passwords that contain the applicant's name.

## Portal notes: read ONLY the matching file
Identify the portal from the URL (and again after redirects/"Apply" clicks, e.g. company site → Workday), then read
`$JP_ENGINE/portals/<file>.md`. No row matches → `grep -n -A4 -i "<domain>" $JP_ENGINE/portals/others.md` (and read its
"Common patterns"). Also grep `$JP_HOME/portals-local.md` (notes learned on this machine). Nothing anywhere → work it
out and report `LEARNED:`.

| URL / page pattern | file |
|---|---|
| *.myworkdayjobs.com, *.myworkdaysite.com (Target, Citi, Maersk, Equinix, Hartford, Wells Fargo, DB…) | workday |
| *.oraclecloud.com/hcmUI (Nokia, JPMC via contacthr→Oracle) | oracle |
| Phenom sites: careers.marsh.com, careers.hpe.com, mastercard, NTT, GSK, Disney, quest-global, jobs.ecolab.com, jobs.veralto.com, careers.cisco.com, careers.gehealthcare.com, careers.fisglobal.com | phenom |
| *.successfactors.com/.eu, careers.yash.com, capgemini, careers.sap.com, careers.te.com, careers.ey.com | successfactors |
| greenhouse.io (incl. job-boards.eu), grnh.se, flix.careers, careers.veeam.com | greenhouse |
| jobs.lever.co | lever |
| jobs.ashbyhq.com, company page embedding an Ashby iframe | ashby |
| Eightfold (jobs.ascendion.com, jobs.infineon.com, jobs.twilio.com …) | eightfold |
| *.icims.com (Docusign) | icims |
| *.taleo.net (UnitedHealth/Optum) | taleo |
| *.avature.net, group.bnpparibas, usijobs.deloitte.com | avature |
| jobs.smartrecruiters.com, ServiceNow, engradar.com/smartrecruiters | smartrecruiters |
| sjobs.brassring.com, *.contacthr.com (Deltek) | brassring |
| *.ripplehire.com (UST, 7-Eleven) | ripplehire |
| ats.rippling.com | rippling |
| wellfound.com | wellfound |
| **anything else** (company sites, small ATSs: Siemens, Amazon, Keka, Hirist, GlobalLogic…) | others |

### Hand-off portals (return blocked / pending-user)
- LinkedIn job pages: the offsite apply link is hidden unless logged in; Easy Apply is never automated.
- Talent-platform signups (profound.me, Flexiple, uplers, hackajob…) that need phone OTP or a full profile → blocked.
- Any captcha (reCAPTCHA grid, hCaptcha, Cloudflare, text captcha) → pending-user. Never try to solve or bypass it.
- cgi.njoyn.com: shows a Radware/hCaptcha bot check before the job page → pending-user right away.

### Duplicate guard (grnh.se short links etc.)
Different short links can resolve to the same posting. After the page loads, run `jdone "<final url>"`; if it exits 0,
log `skipped` "Duplicate" without submitting.

## agent-browser cheat sheet
```bash
$AB tab new <url>; $AB open <url>; $AB tab list; $AB tab t2; $AB tab close
$AB snapshot -i | grep -Ev '^\s*- (link|heading) '      # interactive refs
$AB fill @e12 "text"; $AB click @e12; $AB keyboard type "x"; $AB press Enter; $AB select "<css>" "Option"
up "<css of input[type=file]>"                          # nopicker + upload the active resume
$AB eval '(()=>{...})()'; $AB wait 3000; $AB get url; $AB get title
$AB mouse move X Y; $AB mouse down; $AB mouse up; $AB reload
```
**File uploads:** never click an Upload / Attach / Browse / "Choose file" button, a drop zone, or the file input
itself: in a real browser that opens the native file dialog, which stays open over the window. Run `nopicker` first,
then upload straight into `input[type=file]` with `up "<css>"` (works on hidden inputs). If the input only appears
after a click (e.g. an "Attach" menu), run `nopicker` before that click.

**Waiting:** after opening a new job tab, wait ~3 s so anti-bot passive checks finish. Afterwards avoid fixed sleeps:
use `wfor '<js expr>' <maxms>` or `$AB wait --text "Thank you"`. Keep fixed waits ≤1000 ms.

**Clicks:** always submit with trusted native clicks (`$AB click @ref --human`, `tclick`, `ghsubmit`, `wdsubmit`),
never JS `.click()` on Submit (untrusted events trigger bot challenges). `tclick` prints `maybe:` (returns 2) when the
click may already have run ("os error 35"/timeout): re-check the page instead of clicking again.

## Helpers in jobkit.sh
- **Any form (use first):** `formdump` lists every visible field as `fN | type | label | value | options`;
  `fillform '{"fN":"value", …}'` fills them all in one call (text, native selects by option text, radio groups by label,
  checkboxes true/false) and prints a read-back. Then handle only the custom widgets it can't (FAIL) with clicks.
- Workday: `wdstart` (sign in / create account) → `wdresume` → `wdinfo; wdsrc` → `wdexp` → `wdpick/wdprompt/wdtext/wdradio`
  for questions → `wdterms` → `wdsubmit`. `wddump` shows every field and error.
- Greenhouse: `ghbase` (resume + contact), `ghq` (list questions), `ghc/ghcombo` (comboboxes), `ghsubmit`.
- Hirist: `hirist <url>`, `hset`, `hradio`.
