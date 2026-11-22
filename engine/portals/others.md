**emagine** (portal.emagine.org): sign up first (`otp --match emagine --len 6`), then a 9-step profile wizard (Skip optional steps). Job form date picker takes dd.mm.yyyy; or toggle "Select notice period" → "1 month notice".

# Other portals (one-off company sites and small ATSs)

Find your site with `grep -n -A4 -i "<domain>" others.md` instead of reading the whole file.
Read "Common patterns" once. Before adding a note, grep for it; add only rules that are new. Keep each site to 1–3 bullets.

## Common patterns (any portal)
- **Captcha** (visible reCAPTCHA/hCaptcha, text captcha, Cloudflare check): fill everything else first, then pending-user with the tab id.
- **Country/location combobox:** typing "India" then Enter often picks *British Indian Ocean Territory*. Click the exact "India" / "<City, State, Country>" option.
- **Hidden or custom selects** (chosen, select2, native selects set via eval): set the value with JS, then dispatch a `change` event. Re-check after Back/Next, because the value can be stale.
- **Overlays block clicks** (chatbot, sticky footer, Google `.pac-container`, cookie banner): use `scrollintoview` or eval `.click()`, or remove the overlay via JS.
- **Resume parse fixes:** wrong city (Mumbai/LeetCode → <city>), missing employer or start date, `+91` doubled in the phone field. Check every prefilled field.
- **CTC fields** take full rupees (<CTC as a number>), not "33".
- **Order matters:** some uploads and country changes clear other fields (passwords, address, location). Fill those last.
- **Upload without a usable input** (no input[type=file] reachable via CDP): pending-user.

## Sites
**Accenture** (accenture.com/careers → mycareer.accenture.com): email OTP `otp --match accenture --len 6`, password 9–16 chars. Citizenship is nested (India → "Citizen (India)"). Step 2 needs PAN + DOB.

**ADP WorkforceNow** (workforcenow.adp.com): 6-digit code `otp --match adp --len 6`. Set Country FIRST, because changing it clears the address. If 3 professional references are required → pending-user.

**Alignerr** (alignerr.com/jobs): "Apply now" opens app.alignerr.com sign-in with only Google/LinkedIn SSO (plus a Terms box) → pending-user; log any other Alignerr URLs the same way without a worker.

**Amazon** (amazon.jobs): two codes (the second is "Amazon A to Z", 6 boxes: `otp --match "A to Z" --since 90`), then set a password. The old profile is stale: fix address, employer, school (<your university>), source LinkedIn.com, resume. Skills max 200 chars. SMS step: click "Skip & continue" (#save-and-continue-form-button) via its ref. After Submit, #aiPreferenceModal: No → Continue. Already signed in: no code at all, or only one email code; the modal may not appear. Sometimes the flow is email + password + one email code with no A to Z code (2026-11-15). Job-specific dropdowns ignore `$AB select`: click the combobox, then the option by ref. Option refs change after each click, so re-snapshot before picking, and verify the combobox values afterwards (a first pick can fail silently). Radio ids re-randomize after each click, so pick radios by label text. Work Eligibility "date of application" = YYYY-MM. Work Eligibility "Continue" and the job-question "Continue" are links, not buttons. The Submit click on the review page can hang the tab (os error 35): wait about 10s and re-check before retrying.

**Bain & Company** (careers.bain.com): password must be alphanumeric only, so the account uses `password_strong` with its special characters removed. Resume: `up "input#resumeFile"`, then click #uploadFileResume via eval. School/country are select2 ajax: click `.select2Container<id>`, fill the searchbox, dispatch mouseup on the option. The last page is a voluntary EEO acknowledgment checkbox, then APPLY.

**BambooHR** (*.bamboohr.com/careers): no login; "Apply for This Job"; reCAPTCHA before Submit → pending-user. Date Available ≈ today + 30 days.

**BCG** (careers.bcg.com → experiencedtalent.bcg.com): the default Apply link lands on employee Okta SSO, so open /careerhub/explore/jobs/<id>?profile_type=candidate&customredirect=1&refNum=BCG1US. Email + 6-digit code (`otp --match bcg --len 6`), no password. Work-auth document prefills "Driving License" → change to Indian Passport. Start date via the datepicker.

**BMC** (jobs.bmc.com, Tenrox-style ATS): no account. The resume upload only attaches the file and the page then waits. Run `nopicker`, then `up "input#resumeFile"`. Un-hide #methodButton--fileFieldSetContainer via JS, set .resumeRegistrationFileMode to "file", and click [id="uploadFileResume"] with --human. Numeric ids need the form [id="16656-next"]. After Continue: PAN (uppercase) and a select2 visa question (No), then EEO (Gender, career break), then Submit. Confirmation: "Thank you for applying". BMC posts the same role under several job ids (47802/47803/47804): check tracker.csv for BMC first; a duplicate fails with "existing account with the username you entered".

**Binary** (binary.so/<id>, Tradl AI): form, then an email 6-digit code after Submit (`otp --match binary --len 6`); the form auto-submits once the code is entered. Confirmation: "We have received your submission".

**Blue Yonder** (careers.blueyonder.com, Phenom): no login, 4 steps. Upload the resume first. After Next the browser can hang (os error 35) for about a minute, so click `$AB click "button.btn-next" --human`. Location is Mumbai or blank on all jobs, so set it to <city>. Degree "Bachelor's Degree - Completed" and field "Computer and Information Science" via `$AB select 'select[id="educationData[0].degree"]'`. Step 3 questions are selects (eligible Yes, rest No), then a signature textarea ("<full name>") and a date input (YYYY-MM-DD). Success: applythankyou?status=success.

**Bombay Softwares** (app.mycandidature.com, via a tinyurl redirect): upload the resume first and the form autofills. Location fields (Current and Other Preferred) clear on blur unless a Google Places suggestion is picked. Type "<city>", then use a trusted mouse move, down and up on the .pac-item coordinates; Enter and JS click do not work. Submit opens a "Yes, Submit" confirm modal, then a processing page of about 4 minutes. The referral fields are disabled and stay empty.

**EPAM** (jobs.welcome.epam.in): an APPLY modal with steps: CV upload, LinkedIn URL, contact, location, skills, employment, extra info, then consent. Clicks can lag, so re-check state before re-clicking. The City combobox prefills Mumbai (clear it and type <city>). Primary Skill prefills Go Language (change it to Python.Core). Optional EPAM account creation can be skipped. City/PIN react-select inputs get polluted if you type over a prefilled value ("<city>Mumbai"): clear via the native value setter + input event, then type. Preferred Office is multi-select (type "<city>" + Enter). Step 4 needs total and relevant experience months (4y 6m). Tenure field: 08/18/2025.

**HireZapp** (hirezapp.com/jobs/…/apply): renders duplicate mobile and desktop forms with two file inputs. The first is hidden, so tag the visible one (offsetParent!==null) with an id and `up` into it. The phone field is prefilled with +91: click it and type only the 10 digits.

**IDFC FIRST Bank** (careers.idfcfirst.bank.in/in/en/job/…): steps are OTP, My Information, Work Experience, then E-signature (tick, Next). Years/Months are typeahead: fill years, Tab, type "6", click the "6 months" option. CTC <CTC as a number>, notice "30 days". Selects have ids (title1, genderDetails, country, state, city, phoneWidget.countryPhoneCode), not names. After the DOB datepicker, press Tab so Next shows.

**Moody's** (careers.moodys.com → career8.successfactors.com/sfcareer/jobreqcareer?jobId=<id>&company=MoodysProd): Apply opens a SuccessFactors sign-in with a visible reCAPTCHA → pending-user.

**NJoyn / CGI** (cgi.njoyn.com): no bot check seen recently. Resume attach needs the document checkbox ticked before Save & Continue, otherwise the page silently stays put. Flow: Apply (I'm Interested) → sign in → "referred by CGI Partner" = No → Apply Now → tick the document box → Save & Continue.

**PharmSight** (pharmsight.com): the MUI modal closes on Escape. Data is kept, but the file upload is lost, so re-run the upload. The availability date is a native input[type=date]: set it with the native value setter plus input and change events (fill and typing fail). Technical Skills is a multi-select dropdown.

**Sense HQ** (sensehr.sensehq.com/careers/jobs/…): simple form (resume, name, email, phone, Notice Period as a number of days, Current Location as text). No account or captcha. Click "Apply Now" to reveal it.

**Sourcebae** (sourcebae.com/apply-job): two steps. Step 1 is a Mantine form (country/city dropdown, 3-7 skill chips) and needs a trusted click on "Save And Apply". Step 2 is an MUI dialog of free-text questions where `fill` and ref typing land in the wrong inputs. Setting values with the native value setter + `input` event, then a trusted click on SUBMIT, works.

**UKG** (apply.ukg.com/careers/job/…): no resume parse beyond the contact fields. Uploading the resume opens a Data Privacy dialog: untick "job recommendations by email", then click I Agree, and the contact fields prefill. Address, city and zip are manual. State appears only after Country = India. The start date is a typed datepicker (e.g. 12/12/2026). Two "I Accept" boxes sit at the bottom. Confirmation: success page.

**Bristlecone** (Oracle HCM, iaagiz tenant, /sites/bristlecone-careers/job/<id>): resume import does not prefill, so fill contact and address by hand, then upload the resume on page 4. Page 4 requires Gender, DOB, at least one Skill, and one Citizenship (Indian, Active; the add form opens in edit mode). The email code arrives only after SUBMIT (`otp --match bristlecone`). A freshly opened `tab new` sometimes vanishes ("tab_gone"); retry with the /sites/bristlecone-careers/job URL. Success: "Thank you for your job application".

**Ceipal** (candidateportal.ceipal.com): one-page PrimeNG modal, resume not parsed. City "<City-State>" resets Zip, so set <postal code> after. Open p-selects via JS `.p-select[i].click()` and click the li in the newest overlay. Success = button turns "Applied". Also a gender select, and a required "Consent for all jobs" radio appears only after the terms checkbox is ticked. City is a p-autocomplete: type "<city>" and click the "<City-State>" option.

**ClanX** (jobs.clanx.ai): no login, /c/new. Radios `input[name^="candidate.openQuestionAnswers.<id>."]` via JS. Clear the "+91" prefill before typing. A required Loom video URL → pending-user.

**Cenara** (cenara.ai/careers/<slug>): custom form, no file upload. It needs a public resume link (Google Drive/Dropbox/Notion) in the "Resume link" field, so without one → pending-user. The intro video field is optional.
**CodeRound** (candidate.coderound.tech/jobs/<id>): apply on the job page (resume, name, email, phone, Apply), then email OTP (`otp --match coderound --len 6`); for an existing profile click "Use Existing Profile & Apply". Caution: on 2026-11-08 the success page and email named a different job ("Engineering Manager, Nurix AI"), so check the confirmation title and log pending-user if it does not match.

**Cornerstone CSOD** (*.csod.com/ux/ats/careersite): guest apply, no account; 4 steps. Resume parse can clear address, so refill after upload. Click radios via their LabelText ref after scrollintoview. NDA "I agree" required. Step 2: Desired Salary must be numeric (<CTC as a number>, not "Negotiable"); delete resume-parse competency rows that demand a Proficiency. Step 3 diversity survey fields are required even when the "I agree" opt-in is skipped. Final Submit stays disabled for a few seconds.

**Cutshort** (cutshort.io/job/…): Apply opens a resume-upload modal (nopicker, then up input[type=file]). "Log into your account" needs an email code with `otp --match notify@cutshort --len 4` (4 digits; plain --match returned the word "<first name>"). Then a details modal: experience, notice, city <city>, WFO/remote, salary in Lacs, declaration tick, Save. The phone step can be skipped. Success: "successfully applied". If Apply lands on /profile/all-jobs with "No jobs found" and no form, the posting is closed: log blocked.

**datascience-jobs.co.uk**: Apply opens my.futuretechjobs.co.uk/sso/start (Cloudflare challenge + Future Tech Jobs account) → blocked.

**Darwinbox** (*.darwinbox.in, e.g. neurealm.com Apply Now): form fields are in shadow DOM, so use a screenshot plus coordinate clicks and keyboard typing. Sign-up uses an email OTP (`otp --match <company> --len 6 --since 900`); the Cloudflare check passes on its own. Resume autofill: fix Last name, Gender, CTC, Primary Skill, Notice Period (15-30 Days) and Address, tick consent, Submit. Qoala (qoala.darwinbox.com/ms/candidatev2): not shadow DOM. Sign-up needs an email OTP (`otp --match qoala`). The resume input has no id: tag input[type=file]#0 via eval, `up`, then click "Yes, Auto-fill". Autofill leaves Gender, Last name, Marital status (preselected "Married": set Single), Personal Identity phone and country code (+91), Last Salary (INR; fixed <CTC as a number>, variable 0), and the Misc Expected Salary currency (plain text, type "INR") blank. There is no company field on Work Experience, and autofill sets the location to Mumbai (change to <city>). The final Submit opens a confirm dialog with a second Submit. Confirmation URL ends in /success.

**Dover** (app.dover.com/apply → jobs.dover.com): single-page form, no captcha. The resume input is the 2nd input[type=file] (the 1st is autofill), so tag it with an id via eval, then `up "#id"`. May include essay questions.

**fdetimes** (fdetimes.net/en/jobs/*): aggregator, not an apply portal. "Quick Apply" is sign-in/account only, with no form → don't log blocked: the slug is <company>-<ATS job id>, so apply directly (Greenhouse numeric id → job-boards.greenhouse.io/embed/job_app?for=<company>&token=<id>; UUID → Ashby/Lever on the company board). Log with the fdetimes URL.

**GlobalLogic** (globallogic.com/careers): single page, native selects (#gender, #jobCountry, #notice_period…), #coverLetter = source, phone without code. Visible reCAPTCHA v2 → pending-user.

**Gem job board** (jobs.gem.com): simple form with fields plus resume input[type=file], then "Apply without saving" (trusted click). Confirmation: "Congratulations! application received".

**Google Careers / Google Forms** (careers.google.com, forms.gle): both can force a Google sign-in first. Careers: Apply is a link, and it requires a Google account sign-in. If the worker profile is signed out → pending-user (the user signs in in that worker window). (2026-11-09: the worker Brave profiles are already signed in to Google Careers; flow Apply → Role info → self-ID → review, tick privacy, Apply, all --human clicks.) Google Careers caps applications at 3 per 30 days per account ("You've reached the limit of 3 applications in a 30 day window"). Check the dashboard before starting more Google roles; a capped submit is saved as a draft.

**greytHR** (*.greythr.com/hire): Experience must be an integer (4), since a decimal fails with "Missing fields - experience_months". Tick T&C via JS `.click()` on [name=tnc], because clicking the label does nothing. City: type in the search box, then click the ".item" inside "[id^=location]". The T&C box can untick after the first Submit, so check [name=tnc].checked right before Submit.

**Grid Dynamics** (careers.griddynamics.com): WordPress CF7 form. Apply stays disabled until the resume upload fires input/change (dispatch via eval after `up`). The consent checkbox opens a modal: click I ACCEPT, not I DECLINE. Then a required "City of application" combobox (Hyderabad/Bangalore) appears.

**Happiest Minds** (jobs.happiestminds.com): Angular Material. DOB is a readonly picker (calendar icon → period → year → month → cell "<date of birth>"). mat-select: click #mat-select-N, then mat-option; re-snapshot in the same call. CTC fields reject "33", so enter the full number (<CTC as a number>). Notice, authorization and sponsorship mat-selects open only via JS: scrollIntoView, then click `.mat-mdc-select-trigger`. Current Location is an autocomplete: type "<city>", then pick the first mat-option. A successful submit shows no confirmation. Only a duplicate-profile toast can appear, so re-check before resubmitting.

**Harness** (harness.io/company/jobs/apply?gh_jid=<id>): embeds Greenhouse at job-boards.greenhouse.io/embed/job_app?for=harnessinc&token=<id>. The ghbase form leaves Country and Location empty: pick Country via ghcombo, and type "<City>, <first letter of state>" + Enter for Location. No email code. Success: confirmation page.

**HiBob** (*.careers.hibob.com): dropdowns are cdk overlays (fill the Search box, click the treeitem). The "Add file" uploader is unreachable → pending-user.

**Hiresome** (*.hiresome.ai): phone country defaults to Kazakhstan, so click `li[data-country=in]` via eval. Success: "application received".

**Hirist** (hirist.tech/.com): logged in via the profile. `hirist <url>` lists questions; `hset`/`hradio`; number inputs use `question-<id>`. Success `/job/applied?jobId=`. If logged out: email → Get OTP → type the code in the first box, and the pending Apply submits itself. `otp --match hirist --len 6` (fixed 2026-11-08 to prefer all-digit codes; if it still returns a word, read the code from the mail body). OTP login: the Hirist mail has no plain-text body, so `otp --match hirist` returns a word. Try `--len 6`, or read the HTML body (jobtool `recent_messages` + `body_text(msg)[1]`, strip the tags, take the first 6-digit number). `hirist <url>` prints nothing when logged out. Screening spinbuttons come prefilled with wrong numbers (10/13): overwrite them. The notice period is a button group (the worker picked "1 month"). WARNING: `hirist <url>` auto-submits when the job has no screening questions, even when you only meant to list them. Read the JD with `$AB eval` first and check the seniority and stack before running any hirist helper.

**HTC Global Services** (htcinc.com, WordPress + Contact Form 7): job page, then Apply Now (close the cookie banner first). One form: resume, name, email, phone, PIN, city, state, "authorized to work in" select, 18+ radio, terms checkbox. No redirect; success is the CF7 "Thank you for your message. It has been sent." text.

**IDFC FIRST Bank** (careers.idfcfirst.bank.in): Apply Now → email → Get OTP (`otp --match idfc --len 6`) → My Information with a required PAN number (`$pan` from secrets.env); phone autofills with a 91 prefix (remove it); state/city are plain selects set by JS + change event. Upload the resume first: it resets DOB and City. DOB is a react-datepicker (year/month selects, then click the day). Country select must be exactly "India" (a substring match picks British Indian Ocean Territory). A reCAPTCHA image challenge can appear at Next, which goes to pending-user. Then come the Work Experience and E-signature steps (sign "<full name>").

**HuntingCube** (huntingcube.ai/browse/job-apply?jobId=): quick apply with no login (email, resume, notice, CTC). The Terms checkbox registers only via an @ref click (not an eval click); then click Apply (a trusted --human click worked). Confirmation text is "Application submitted / Applied on <date>". A stray confirm dialog may appear on load and clears itself.

**IBM** (ibmglobal.avature.net → careers.ibm.com → login.ibm.com): Apply needs an IBMid, and the secrets.env passwords are rejected → pending-user. The reset sends a 14-digit code (`otp --match ibm --len 14`), which may not arrive.

**Husky** (husky.co/en/careers/portal): modal form, Turnstile auto-passes; email/phone → resume/address → 3 consents → source LinkedIn → Apply.

**Instahyre** (instahyre.com job pages): logged in already in Brave. The Apply now button submits instantly with no form; the button changes to "Application sent!".

**Isha Foundation** (isha.sadhguru.org → careers.isha.in/jobs/apply/<id>): Apply Now redirects to careers.isha.in. Native selects need the JS value plus a change event. DOB is a date input (YYYY-MM-DD). Salary is monthly INR (e.g. 275000). stay_in_ashram is required: the worker picked "No, I prefer to work from above stated location", which is a judgment call to check.

**Isomorph** (isomorph.ai/careers): custom form, confirmation shown. The links field accepts only one https:// URL (no comma-separated list).

**JobBricks** (jobbricks.com): login has an OTP plus visible reCAPTCHA before any form → pending-user.

**joblet.ai → micro1** (joblet.ai/jobs/micro1-*, jobs.micro1.ai): Apply Now opens 2 jobs.micro1.ai tabs, so close one (it also creates a joblet account). Email code via `otp --match micro1 --len 6`. Hourly rate = profile contract pay. The next step is an AI interview the user does.

**Kake** (kake.co): antd single page; "Reject all" closes the cookie banner; reCAPTCHA image on Apply Now → pending-user. The reCAPTCHA can pass silently with no image challenge (Apply Now with --human worked). The antd Location list is a country list: keyboard Enter picks the wrong item (Afghanistan), so click the option by ref right after opening it.

**Keka** (*.keka.com/careers): `#resume-upload`, `[id="mobilePhone.countryCode"]` +91, INR. Resume parse sets <current employer> location to Mumbai (fix: <city>) and wrongly ticks "currently working" on <previous employer> and <earlier employer>, so fix those before handing over. Text captcha → pending-user. DOB is a readonly jQuery datepicker: `jQuery("#dateOfBirth").datepicker("setDate",new Date(y,m,d))` (format dd-mm-yy), then trigger change. Apply Now stays disabled until the text captcha is filled. Pressing Enter in the Skills field submits the whole form (don't press Enter there). Experience months parse as 7, set to 6; "currently working" is unticked on all parsed jobs, so tick it for <current employer>. Cloudesign: no captcha shown, submitted.

**Kula** (careers.kula.ai, e.g. Greylabs): Basics plus the resume are enough: the education and experience sections are optional, but remove the empty education row first. the resume input is `#resume`. Compensation and notice period must be numeric (notice period 30). Education and experience search fields need a dropdown suggestion picked. Submit with the main button using a trusted click. No captcha. Success URL ends in applySuccess=true.

**Macquarie** (recruitment.macquarie.com): Apply now leads to ApplicationMethods. Click "From Device" first (it reveals Continue), then `nopicker` and `up "#resumeFile"`, then click #uploadFileResume to reach the Register page. Salutation, gender and SMS are native selects (set via eval). "Currently employed" is a custom dropdown: click its textbox, then the option. The account step has a reCAPTCHA checkbox, so it needs the user.

**Michael Page** (michaelpage.co.in): Apply with CV → email → info → employment info (chosen widgets, salary required). Untick "Email me more jobs". Success: "You've successfully applied".

**Microsive** (microsive.com/careers): custom form at /careers/apply with no resume upload. Turnstile passes passively. Years of experience must be a whole number (4.5 is rejected). Salary is in lakhs per year. Confirmation: "Thank you. Your application has reached our team".

**Microsoft** (apply.careers.microsoft.com): no email/password signup, only Microsoft/LinkedIn/Google/Facebook SSO -> pending-user. Create-account asks country first (type, click option, Submit).

**NestorBird** (nestorbird.com/career): the form is a same-origin HubSpot iframe (#hs-form-iframe-2). Give the file input an id via eval on iframe.contentDocument, run `$AB frame "#hs-form-iframe-2"`, then `up "#id"`. Refs inside the iframe work for fill and select. No captcha. Confirmation shown.

**Octopos** (octopos.notion.site): Notion form. There is no input[type=file] until Upload is clicked, so `up` fails and the resume must be attached by hand. Essay asks for a real production-agent failure: ask the user, never invent one.

**Oorwin** (*.oorwin.ai, e.g. tachyonind): apply form has a reCAPTCHA checkbox, so fitting roles go to pending-user.

**PeopleStrong** (*.peoplestrong.com, e.g. abgcareers): must Register first (name, email, mobile, reCAPTCHA), so it goes to pending-user. "Register And Apply" opens a login-required popup, and OK leads to /login.

**Aspire** (people-jobs.com/aspire, Revolut People iframe): open the revolutpeople.com iframe URL directly. Phone must be +91<phone> format (bare digits are rejected). The cookie banner covers the country dropdown: click "Reject all cookies" via eval, then scrollintoview before the country button. Confirmation: "Thank you for your application!".

**Persistent** (careers.persistent.com): unlabeled #mat-input-1..12 in order: phone, gender, company, total exp, relevant exp, CTC, expected CTC, current location (pick an option), preferred location. Submit via eval `.click()`. "Already in active pool" → skipped. Newer field order (2026-11-14): First, Last, Email, Phone, Gender, Company, Total exp, Relevant exp, CTC, Expected CTC, Current location, Preferred location, Notice, Employment type, Remarks, Source. A stale mat-option overlay blocks a --human click on Submit, so use the eval click fallback. The "already in active pool" popup appears only after Submit, and the page has no success banner.

**Pinpoint-style** (careers.infor.com /applications/new): file `[id="application_form[application][cv]"]`. Success `/applications/thanks`.

**PPFAS** (amc.ppfas.com): form at jobapplicationform.php?id=N (Apply link hidden from snapshot). Turnstile passes passively. "Reason for change" ≤50 chars; Total Experience integer (4).

**Recrew** (talent.recrew.ai/careers/<slug>/apply/): the page renders two identical forms and the first is hidden. Fill the second (`document.querySelectorAll("form")[1]`) and tag its file input with an attribute before `up`. No captcha. Submit redirects to /careers/ with no confirmation text.

**Reczee** (jobs.reczee.com): click Apply Now by ref. Notice "30 days". Leave the cybersecurity box unticked. The form just closes on success.

**Roche** (careers.roche.com): the email OTP step can redirect straight to applythankyou?status=alreadyApplied when that email already applied. Log skipped ("already applied"), not blocked.

**The Retail Insights** (theretailinsights.com/job/…): a slide-in apply drawer sits off-screen (x about 1460) until the page's "Apply now" button is clicked. `$AB click --human` on a drawer element fails with "outside the viewport" while it is closed. Fix: scrollintoview and click the page's "Apply now", wait about 1.5s, then click the drawer's Submit with --human. Do not click the drawer's own "Apply now" (it toggles). No captcha. The drawer closes on submit with no confirmation text, so verify.

**Sage** (sagehr.my.salesforce-sites.com): no password; `otp --match sage --len 6`. Employed/previously at Sage: No; entitlement "Yes - Citizen". Confirm: My Application shows "New".

**Scan-IT / Scan Group** (careers.scan-group.com): a simple single-page form with no captcha, and a cookie banner that doesn't block. Radio ids follow `..._answers_attributes_N_boolean_answer_true/false`; CTC fields are numbers. Answer the UiPath/Power Automate question No, and the 3+ years automation/integration and LLM APIs questions Yes.

**Screenloop** (app.screenloop.com, easyapply.jobs/r/): click Browse before the file input appears. Country, location, currency and experience are react-selects: type, re-snapshot, click the option by fresh ref (ArrowDown+Enter picks wrong places). Currency defaults to Pound Sterling → set Indian Rupee. The LinkedIn field can truncate after fill: re-read it and refill. The work-experience react-select shows buckets only after Backspace following the typed text (0-2/3-5/6-10/+10).

**SeekOut** (connect.seekout.io/interview/…): resume upload plus 4 screening questions on one page. The resume parse uppercases name fields (FIRST/LAST), so fix them. Submit lands on /intro as the confirmation page; the optional AI video interview can be skipped.

**Shamrock AI** (shamrockus.ai/jobs/…): Apply Now opens a Google Form in a new tab. The same form, with its saved draft, is shared across all Shamrock roles. The resume goes through the Google Drive picker (not automatable), and a later page has a production-issue essay the profile does not cover → pending-user.

**Shine** (shine.com/jobs, auto_apply=true): Apply goes to /pages/myshine/login (OTP/Password/Google/Register). No account for this email, so treat as blocked (sign-up or phone OTP).

**Siemens** (jobs.siemens.com): if the email already has an account, log in with password_strong from the ApplicationMethods page (…/en_US/externaljobs/ApplicationMethods?folderId=<id>&source=LinkedIn). That skips registration and prefills the profile. Then 3 steps: tick the declaration, leave the PwC "Yes" box unticked, eligibility Yes, salary <CTC as a number> INR, DOB via native setter. register (upload CV, profile; passwords LAST, use `password_strong`), `otp --match siemens --link`, log in, "Complete application". Citizenship select2: type "Indi", wait, mouseup on "India". DOB needs a native value set (2000-01-23).

**SourcingXpress** (sourcingxpress.com): WorkOS sign-in with email code (`otp --match sourcingxpress --len 6`), no password. First login runs a 6-step onboarding (name, phone, title, LinkedIn, tech areas, university, city/pincode). Apply-form dropdowns are hidden native selects: set via eval with the native value setter + change event. Yes/No radios: click the LabelText, not the radio ref. Click "Email sign-in code" after entering the email before running `otp`; the early `otp` call hangs past the tool timeout. Re-run `otp --since 300` once the code field appears. The apply form has 21 native selects; notice options are Immediate, 15 Days, 1 Month, 2 Months, 3 Months+. Confirmation: "We have received your application". If already onboarded, the email code goes straight to the /apply form, which has about 15 hidden selects (work type, employment, skill-years for Flask/AWS/Python/HLD/LLD/LLM/GenAI/RAG/MLOps/Vector DBs, notice, preferred work type). Salary fields auto-format to 33,00,000.

**Synmatch AI** (app.synmatch.ai/jobs/…): the date field is a native date input that ignores typed digits. Set it with the native value setter ("2026-12-11") plus input and change events. The CV upload shows "Replace CV" even though files.length reads 0. Confirmation: "Application received".

**Syfe** (syfe.careers-page.com, Manatal form): the form is in shadow DOM, so `up` cannot find the file input. Set the resume via JS DataTransfer with base64 on the shadow-DOM input, then dispatch input and change events. Location: type "<City, Country>" and pick the autocomplete (type a char, Backspace, ArrowDown, Enter), or Apply stays disabled. The AI-example essay is capped at 255 chars. The phone country picker needs a real mouse click on India. Salary needs INR and Annually. Confirmation: thank-you page.

**Talemetry** (apply.talemetry.com; jobs.telusdigital.com embeds it): open the iframe URL directly. 8 steps; add the current job by hand. TELUS needs Aadhaar ID → pending-user. Languages: from the profile. ttcportals.com (e.g. Meltwater): APPLY NOW opens a Talemetry iframe that never shows in the tab list. Run `CareerSite.Apply.launchApplicantJob` via eval, read `document.querySelector("iframe").src`, and open that URL directly. Next stays disabled briefly after filling, so click again. It ends on the search page with no confirmation text. Sanmina (Talemetry): the race and job-question selects ignore `$AB select`. Set them via eval with the native value setter plus a `change` event, and click NEXT only after that. Its work-history parse omits <current employer>, so add it by hand. Talemetry selects (veteran, job questions) need the native value setter plus input, change and blur events. A failed NEXT can re-render and clear the first select, so re-check all selects before clicking NEXT again. The state/region select is optional and can be left blank.

**Teamtailor** (*.teamtailor.com, careers.lyzr.ai): click "Apply for this job" to reveal the form. Resume input is #candidate_resume_remote_url (files.length reads 0 after upload, but the filename shows). No consent checkbox. Confirmation text is "Thanks for applying". Upload goes through a remote-URL input, so files.length reads 0 after `up` even when attached. A location checkbox must be ticked (e.g. Mumbai), or Submit fails with "Can't be blank". The first Submit can re-render the form and clear the resume: re-upload and check before resubmitting. Ateme confirmed "Thanks for applying". WSA (careersapac.wsa.com, Teamtailor): click the enabled "Apply now" to open the form; CV goes in via input#candidate_resume_remote_url. The required "Describe a real example" essay warns against AI-generated text, so write it by hand. Clinisys (careers.clinisys.com, Teamtailor): emails a verification link after Submit. The modal closes on submit. `--human` clicks may return os error 35 yet still register, so re-check the state before retrying. The form has an extra required question "worked at Roper Technologies group?" (No). Run `otp --match clinisys --link --since 600` and open the link to finish. Decline the cookie banner first, then click "Apply for this job" to open the modal form. Hupo (careers.hupo.co): "legally authorized in the country where role is based" radio, a notice period number field (unit not stated), and a Locations checkbox list; the resume goes in via up "#candidate_resume_remote_url". Confirmation: "Thanks for applying". TeamViewer (careers.teamviewer.com): "Apply now" opens the modal with no account. Address is a combobox: type "<city>" and pick the option. The talent-pool consent is optional, so leave it unticked.

**TalentRecruit** (*.talentrecruit.com): a stale job id can render an empty Angular shell (no body, no inputs). Nothing to fill: log blocked. open the iframe src from appcareer.talentrecruit.com. Location: type "<city>", Backspace, retype, click "<City, State, Country>". The OTP comes from the company: `otp --match <company> --since 600`.

**Top Billing** (topbilling.in/careers): apply needs a free account (signup, then email-link verification via `otp --link`). Required DOB is a native date input: set it via the JS value setter + input/change events (typing into the spinbuttons fails). Expected pay must be numeric (e.g. <CTC as a number>); "Negotiable" keeps Send disabled. Confirmation: "Thank you — we have it".

**Tesco** (careers.tesco.com): upload #resumeFile, "I do not currently work for Tesco", register (`password_strong`). Prefill is wrong (City "LeetCode", blank employer). EEO "prefer not to say".

**Thermo Fisher** (jobs.thermofisher.com, jsv3.recruitics.com rx_cid=3436): the chatbot covers Apply Now, so use eval `.click()`. 6-step wizard; step 1 has a visible reCAPTCHA → fill step 1, then pending-user. Judge stack from the title if the JD doesn't render.

**TriNet** (jobs.trinet.com): an Eightfold page whose Apply Now goes to Oracle HCM (fa-etgw-saasfaprod1). Open the Oracle apply URL directly. Email code usually comes after Submit (sometimes before the form, and sometimes not at all): `otp --match etgw` (`--match trinet` hangs). Radios are hidden inputs: set them via JS on `input[type=radio]` by index (4 groups of 3: Yes/No/No Answer). Experience and Education sections are optional. Source "Social Media", then the follow-up "Please specify" pill → LinkedIn. Mr. title and Yes/No radios need JS clicks on `span.cx-select-pill-name`.
**TurboHire** (*.turbohire.co): email 6-digit OTP login (`otp --match turbohire` works). Uploading the resume into the first input[type=file] autofills name and phone. The question step asks for 10th/12th percentages and years, which the profile does not have: ask the user.

**UKG Recruiting** (epack.rec.pro.ukg.net JobBoard): Apply goes to signin-us.ukg.net, then Sign up (email + password), then a name/phone/consent step (Turnstile passes passively), then the form. Resume `up` prefills most fields, but fix Title, Country, State (option is uppercase "<STATE>"), Address, City, Zip, the phone ("+91" prefilled), and the current job's To date. On Submit a "save changes to documents" Yes/No dialog appears; the application submits only after clicking Yes or No.

**UKG UltiPro** (recruiting2.ultipro.com): Apply goes to signin-us.ultipro.com. Use Sign up with the email and password, then a name and phone step with a Cloudflare Turnstile that passes passively. After the resume upload the form prefills but needs fixes: Title, Country, State (appears after Country), address, and the work-experience location and end date (it fills today's date for the current job). The start date prefills with today, so change it. Submit shows a "save changes to documents" Yes/No dialog, and the application is only submitted after you click Yes or No.

**Web Spiders** (webspiders.com/careers): own form under "Click here to Apply" tab, no login; mandatory essay with a public URL (GitHub). reCAPTCHA v2 checkbox → fill, then pending-user.

**Workable** (apply.workable.com/j/*): /apply form, no account. Resume via `up 'input[data-ui=resume]'`. Custom questions are plain radios and textboxes.

**Xenqube** (xenqube.com/careers): Apply goes to /contact/?role=…, a plain contact form with no resume field and no captcha. Do not treat it as an application: log pending-user unless the user wants a contact message sent.

**Xponentium (Konceive)** (careers.xponentium.com/apply): simple 2-step custom form (basics, then details with location/CTC/notice/CV). "Serving notice period? No" reveals 15d/30d/45d/60d/90d buttons.

**Zoho Recruit** (e.g. jobs.foodhubcareers.com): "I'm interested" → rec-easyresume_file. Postal lookup: type "<locality>", press ArrowDown, then Enter → "<locality, city> … <postal code>", then refill Street. A wrong pick: use the "Clear all fields in the Address Information section" button. Notice Period opens a list: click it via find text "30 days". Text captcha → pending-user.
- GreyOrange (careers.greyorange.com/#!/job-view): custom Angular Material form. The location autocomplete shows no options, but free-text "<city>" is accepted. Click options only via eval on mat-option (the cdk overlay backdrop blocks native clicks). Notice Period has no 30-day bucket: pick "15 - 30 Days".

**Zuroth** (zuroth.com/careers): simple custom form. A cookie banner (.ck) covers Submit, so click "Essential only" first.
- Meltwater (Talemetry iframe, 2026-11): once Country=India is selected, State becomes required. Pick "<State with diacritics>" with `$AB select @ref "<State with diacritics>"`. Step 5 has no work-history page. Submit redirects to the search page with no confirmation text.
- ElectroGlobal (electroglobal.in, 2026-11): the form is at /careers/<slug>/apply with no captcha. Success replaces the form in place with "APPLICATION SUBMITTED!" and the URL does not change. The listing shows 1-3 yrs and up to 11 LPA; the form has a 3+ Years bucket.
- Amazon (2026-11): the profile is usually prefilled (employer, school, skills, source), but legal first/last name can be blank and the resume may need re-upload. On the review page, "Replace Resume" opens the upload step: run nopicker, then the input[type=file], then Save & continue. One email code was enough.
- Neo (neo.work/careers): a simple form (name, email, resume). Its fields are textareas, so `$AB fill` does not stick: click, then `keyboard type`, and read values back with eval on input,textarea. Success: "Application received".
