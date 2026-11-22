# successfactors notes

### SAP SuccessFactors (e.g. Capgemini careers5.successfactors.eu)
- Sign In with creds; else Create an Account (privacy notice "Acknowledge", leave both email opt-ins unticked).
- Upload CV via "Upload a CV" → `input[type=file]`. Dropdowns are buttons → `option`. Then Apply → "Your application has been sent".

### SuccessFactors - YASH (career10 yashtechnoP)
- Quick-apply: account + application on one page. Resume: click "Upload a Resume", then hidden input [id="97:_file"].
- SF comboboxes [id="N:_input"], options [id="N+1:_listSelect"] li: type, then Backspace + retype last char to filter, click li. Gender F/M only.
- Existing account: Apply now -> menuitem "Apply Now" -> "Please sign in"; resume + most answers carried over. Press Escape before opening the next combobox. CTC = plain numbers.
- Untick the 2 default-ticked notification opt-ins. Terms of Use = button -> dialog Accept.
- YASH comboboxes: open, wait ~1200ms, click option from a FRESH snapshot (refs change each open) — more reliable than type-to-filter. Interest Level: Actively Looking. Shifts/travel: Maybe/No/Yes. Signed-in session goes straight to form after Apply Now.
- YASH Currency option is "Indian Rupee" (not "INR"). Relevant-experience Years/Months and Gender (M) may be blank; fill them.
- YASH quick-apply: sign-in link can be covered by a stuck loading overlay; reload, then real-click "Please sign in" (JS click fails). The upload on the registration page does nothing (no file input), so click "Please sign in" first and sign in with secrets.env. The saved resume carries over, but replace it with the latest PDF if the form allows.

### SAP careers (career5.successfactors.eu, company=SAP)
- "Apply now" -> generic SF sign-in; Create account sends 6-digit email OTP (`otp --match sap --len 6`). One-page form of comboboxes (click, then option from fresh snapshot).
- School: "*** School Not On List ***" (no SPPU). "Recruiter may contact me" = talent pool -> No.
- Required "SAP Sanction Party Screening" consent: permission system denied ticking it -> pending-user (user ticks + Apply).

### TE Connectivity (careers.te.com -> career8.successfactors.com TEConnect)
- Apply now -> menuitem "Apply Now" -> generic SF sign-in; no account yet. "Create an account" ref click does nothing: click the anchor via eval (keeps career_job_req_id).
- Create-account step (recruiter radio, untick opt-ins, Terms) was blocked by the permission system -> pending-user.
- SAP (careers.sap.com): "Apply now" href redirects home if opened directly → JS-click it from the job page. After sign-in at career5.successfactors.eu saved form opens. TrustArc banner covers buttons → "Reject All" first. Sanction Party Screening consent: classifier has blocked ticking it twice → hand to user.

## EY (careers.ey.com → career5.successfactors.eu, company=EYHRISPRD1)
- An account exists with an unknown password. Neither secrets.env password works, and the forgot-password reset didn't confirm. Return pending-user until the user resets it.
- The "Apply now" menu only opens after you reject the cookie banner. Direct URL: career5.successfactors.eu/careers?company=EYHRISPRD1&career_ns=job_application&career_job_req_id=<reqId>.
- Iris (career44.sapsf.com): CV input appears only after clicking "Upload a CV" (nopicker first). New account then email OTP (`otp --match iris --len 6`). Country/Region Code: match exact "India (+91)" (substring "India" picks British Indian Ocean Territory).
- Teradyne (jobs.teradyne.com → career41.sapsf.com?company=teradynein): the resume file input (id like "52:_file") appears only after clicking the "Resume/CV" button (run `nopicker` first). Comboboxes need ~1500ms after the click before menuitems show; pick them via menuitem refs.
- Firstsource (careers.firstsource.com → Apply now → menuitem "Apply Now" → career5.successfactors.eu, company=firstsourc): sign-in with the creds password failed, so a new account was created. Source Type: "Social Media" → "LinkedIn" (no LinkedIn under Job Board/Portal). DOB is MM/DD/YYYY. Required: Source Type, Sub-Source, DOB, Gender, "applied in last 30 days" = No.
- QualityAI (careers.quality-ai.com → career44.sapsf.com, company=qualitesti): "Apply now" → menuitem "Apply Now" opens same tab. Register page has reCAPTCHA → fill, then pending-user. Password max 18 chars.
- Penguin Solutions (careers.penguinsolutions.com → career41.sapsf.com, company=smartmodul): first sign-in lands on the generic page; create the account and the job opens. Same Resume/CV-button file input as Teradyne. Expand Profile/Employment/Education/Job-Specific sections. Source "Job Board - LinkedIn".
- Atlas Copco (career5.successfactors.eu, company=atlascopcoP): Apply opens a new tab; creds sign-in rejected → create account (no OTP). Form reloads after resume upload and resets phone to +91… → re-fill <phone>.
- Birlasoft (jobs.birlasoft.com → career44.sapsf.com, company=birlasoftl): no account for secrets.env → create one. Fields clear after the first Terms Accept + Create Account attempt, so refill before retrying. Terms "Accept" click was blocked by the permission classifier on 2026-11-09 → pending-user.
- Avaya (careers.avaya.com → career5.successfactors.eu, company=C0000211211P): Apply Now menuitem errors → open careers?company=C0000211211P&career_ns=job_application&career_job_req_id=<reqId> directly. Resume input appears after eval-clicking ".attachActions" in the resume block (nopicker first). Salary numeric only (<CTC as a number>).
- AGCO (careers.agcocorp.com → career4.successfactors.com, company=Agco): creds sign-in failed → create account (privacy dialog "dataPrivacyId" → Accept; activation link `otp --link EMAIL_VER`). Never re-open the activation link with the form filled (resets it). State: "0--Other/Not Applicable". Availability "< 1 month". Has a Yes-only "minimum 6 years" knockout → pending-user.
- Axtria (career10, company=axtriaindiP): register (retry fill, --human click Create Account). Then a long mandatory profile incl. Aadhaar document upload → pending-user.
- Iris Software (career44.sapsf.com): the Country/Region Code combobox ignores clicks, so set hidden select #fbclc_ituCode to IN via eval + change event. Country/Region of Residence (#fbclc_country) is also required. The Terms dialog link (#dataPrivacyId) opens only on focus + Enter; then click button dlgButton_127 "Accept". Dropdown options are li ids like "34:item3", clickable via eval. An existing account sends an email OTP, then "Account Already Exists": click "Please sign in" and use secrets.env. Confirmation: "Your application has been sent. Thank you!".
- SES (careers.ses.com → career5.successfactors.eu, company=SES): Apply Now lands on the generic sign-in, so create an account there (the job context carries over). CV input appears via eval-click of the first .attachActions (run nopicker first). Work history needs an End Date even for the current job (use today). Salary expectations is a USD range dropdown: pick "I prefer not to disclose". The Apply button needs a --human click after fixing errors.
- Cargill (careers.cargill.com → career2.successfactors.eu, company=cargill): sign-in with creds fails, so create an account (the job context carries over). Resume input appears after eval-clicking .attachActions (run nopicker first). Salary expectations must be numeric (<CTC as a number>): "Negotiable" gives "Invalid number". Terms Accept and Apply need --human clicks.
- Firstsource (careers.firstsource.com → SuccessFactors): the account exists now, and secrets.env sign-in works. The resume carries over, so only Source Type = Social Media/LinkedIn, DOB, Gender and "applied in last 30 days" = No were needed.
