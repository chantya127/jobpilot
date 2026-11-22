# oracle notes

### Oracle HCM (*.oraclecloud.com/hcmUI/CandidateExperience)
- Apply Now → email + terms checkbox (click its label) → 6-digit email code into `#pin-code-1` (`$AB keyboard type`), Verify. Already-known profile skips the code.
- The profile is reused across Oracle jobs: check Experience (<previous employer> end 08/2025, <earlier employer>, <current employer> current) and the resume (REMOVE RESUME → upload `#attachment-upload-*` "Upload Resume").
- Date/combobox fields: click the input, pick `gridcell "<value>"`. Yes/No are `.cx-select-pill-section` buttons (`--selected`). E-signature `fullName-*` = <full name>. SUBMIT → "Thank you for your job application".

- DAMAC (ejwe.fa.em2): new email skipped the email code and went straight to the form. Required Marital Status dropdown (see profile).
- JPMorganChase.contacthr.com → jpmc.fa.oraclecloud.com; email step can show hCaptcha → pending-user.
- DAMAC (ejwe.fa.em2): DOB becomes required after first submit; server then rejects <date of birth> with PER-1530408 (DOB before person record start) → pending-user. Escape on DOB dropdown clears Month. Grep "ref=e[0-9]*" for grid picks.

## Nokia (fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com)
- No email code. Radios are hidden: click them with JS `input[type=radio]`.click().
- "Where did you first hear about this position?" is required and only lists internal sources. If the profile's "Answers learned" table has no answer for it, return pending-user.

## All Oracle HCM sites
- Country-code combobox: click the remove (x) first, type "+91", then click the gridcell "+91 (India)".
- Autofill sets Address Line 1 and 2 to "<City, State>" and the pin code to 411002. Correct them from the profile.

## Goldman Sachs (hdpc.fa.us2.oraclecloud.com)
- The required "Name of Latest Employer" widget stays on a loading skeleton forever. Submit still works after a reload and Back/Next.
- Gender, sexual orientation and pronouns are required radios.

## BNY (eofe.fa.us2.oraclecloud.com)
- No email code. 4 pages. Work history needs at least one experience entry and one education entry. Education "Completed Amount" takes whole numbers only (9). Compensation bucket: 3,000,001-4,000,000 INR.

- Nokia (fa-evmr-saasfaprod1): email code mail is subject "Confirm your identity" from NokiaME, so use `otp --match nokia`, not `--match oracle`. Some Nokia postings are internal-only: the required "Where did you first hear about this position?" lists only internal sources (MyGrowth Portal, Opportunity Marketplace…). Return pending-user.

- JPMorgan Chase (contacthr.com goes to Oracle): hCaptcha can appear after Next on the email step (2026-11-15), even in Brave, so don't assume there is none. Page 2 shows more required questions after the first answers are picked: primary area (Software Engineering), AWS proficiency, Python expertise, top 2 languages (Python + SQL). The saved profile has stale Education/Experience entries (old <previous employer> marked Current), so check and fix them each time.
- Nokia: "Where did you first hear" has no Other option; neutral pick = "New Jobs in Your Area Newsletter". Submit may fail with server error PER-1530147 "disability category doesn't exist" whatever the disability radio value (seen 2026-11-08 on job 40728) -> pending-user, user decides. Same error on the WSP tenant (emit.fa.ca3, job 98032) with "No" and "Prefer not to answer" (2026-11-15). DOB is required there; the resume goes into #attachment-upload-2.
- eClerx (fa-ewji tenant): page 2 requires a National Identifier (PAN/Aadhaar number) under Sensitive Personal Information → pending-user (the profile has no ID numbers). Education, Experience and the page-3 "Source Information" carousels are optional.
- EXL/eClerx (fa-ewjt): email code is usually asked AFTER Submit, but once it came before the form (2026-11-15), so run `otp --match EXL` when a code field appears either way; "Are you referred by anyone?" needs a manual No; sender "EXL-Fusion-Notification", subject "Confirm your identity" → `otp --match "EXL-Fusion"` (`--match oracle` hangs). Ethnicity: "Indian". Application questions are free text.
- Zensar (fa-etvl-saasfaprod1 Oracle HCM): PAN goes in as the National Identifier on page 1. Click the field and type it uppercase with keyboard type (fill leaves it empty). The email code comes after Submit (`otp --match zensar` works). Notice period is a radio: "15 - 30 Days". Confirmation: "Thank you for your job application".
- Oracle HCM (eeho.fa.us2.oraclecloud.com, job 347645): resume upload via REMOVE RESUME then `up` showed "Something went wrong" and did not stick. After a reload the saved profile resume came back, so submit with that. Autofilled earliest-available date was Dec 5; the worker set Dec 11. The disability Category dropdown has no "none" option, so leave it blank (optional). Confirmation: "Thank you for your job application".
- eeho tenant (job 349608): a saved profile and resume are reused, so the resume upload step may be skipped. The email code is asked before the form. Earliest-date autofill (Dec 11) is fine.
- eeho tenant (job 349597): the first email code from `otp --since 600` was rejected as stale. Click Send New Code and re-run otp with --since 90. The saved profile and resume are reused; an `up` may land in the cover-letter slot, which is harmless.
- Amex (egug.fa.us2 Oracle HCM): the email code comes after Submit, sender "Amex Careers": use `otp --match amex`. School list has "<your university>" (type "<city>", click the gridcell via JS). Education is required, Experience optional. Page 3 has 23 Yes/No radios: set them via JS, grouped by name.
- Akamai (fa-extu, Oracle HCM, 2026-11): the email step asks for last name first, then a 6-digit code (`otp --match akamai`). Single-page form that needs at least 1 Skill. A typed skill is accepted only when you pick a gridcell (e.g. "Cloud Computing"); typing "Python" offers only "Python in Azure". Click ADD EXPERIENCE with --human to save a new entry (no SAVE button). Pin code <postal code> is not in the list: leave blank (optional).
- Oracle tenant eeho.fa.us2 (2026-11): the resume input is #attachment-upload-33 on page 3, not page 1. The disability Category has no "None" option; leave it blank (optional) and submit still works.
- eeho tenant (job 348372): after SUBMIT it redirects straight to the profile page with no "Thank you" text. Confirm via MY APPLICATIONS. The saved resume is reused, and the email code comes before the form.
- Verisk (fa-ewmy Oracle HCM): the email step asks for last name, then a 6-digit code (`otp --match verisk`). The imported profile can carry wrong employers (it showed "async" for <earlier employer> and marked <previous employer> current), so fix them; add <current employer> by hand. The page-4 privacy checkbox needs a JS label click (its ref is not visible). New experience entries use the "ADD EXPERIENCE" button, not SAVE.
- Goldman Sachs (hdpc.fa.us2 Oracle HCM): the email code is 6 digits (`otp --match oracle` or `goldman`). The saved profile, resume and page-2 answers prefill correctly. After SUBMIT the page shows "Saving..." for about 10s before it redirects to my-profile; wait for that before reporting.
