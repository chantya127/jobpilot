# phenom notes

### Phenom (HPE careers, Mastercard, NTT, GSK, Disney…)
- `/apply?jobSeqNo=…` multi-step. Native `<select>`s set with `$AB select` may not register in React — if Next complains "required", re-dispatch: set value via the native setter + `change`/`blur` events, and for textareas type a key with real keystrokes. Text inputs filled with `fill` may also not stick (phone kept "91<phone>") — verify on the Review page and fix with focus+select+Backspace+`keyboard type`.
- Date pickers are react-datepicker: select the year in `.react-datepicker select`, click `option "Choose <Month> <YYYY>"`.
- Some Phenom sites hand off to Workday — then follow the Workday notes.

### Phenom (careers.marsh.com etc.)
- Resume parse drops current job: "+ Add experience" <current employer>, tick "I currently work here" (`$AB click @ref`); <earlier employer> company blank -> fill.
- Clear prefilled text: el.select() then Backspace. Next disabled ~10s after click (invisible reCAPTCHA): wait, don't re-click.
- Two "Next" refs per step (a header or carousel arrow, plus the real btn-next at the bottom): always click the bottom one. The URL can lag behind the page after Next. Parse often sets City Mumbai and prefills phone 91<phone> → fix. <current employer> title "Senior Software Engineer" is correct.
- Field of study: "Computer and Information Science".
- Mastercard Phenom: no login. Parse drops <current employer> + <earlier employer> company; phone prefills 91<phone>, City Mumbai -> fix. Experience dates = react-datepicker (pick year in picker).
- Mastercard: education dates are year-only pickers (click the year); after Source "Job Board" a 2nd select applicantSource appears (pick LinkedIn).
- Mastercard (2026-11): the form may now be 5 steps (info, experience, 2 question pages, terms) with no education date pickers. Degree "Bachelors", field "Computer Science". Selects take the React native setter plus change/blur. /us/en/apply?jobSeqNo=<id> opens the form directly. After Next, `$AB eval` can lag a step; recheck before re-clicking. Submit stays disabled ~5-8s before applythankyou?status=success. Year pickers: click `.react-datepicker__year-text`.
- Disney Phenom: OneTrust overlay blocks clicks -> REJECT ALL first. Parse: City Mumbai, phone 91<phone>, drops <current employer> + <earlier employer> company -> fix. Month pickers cover radios: remove #pv_id_*_panel via JS. Gender Man/Woman/Prefer not to respond. Salary free text ("Negotiable").

### Quest Global (careers.quest-global.com)
- No login. Resume parse drops some jobs/company names (check experience list) and prefills phone as 91<phone>.
- Phone fix: click field, eval `document.activeElement.select()`, Backspace, type number.
- Datepicker options hidden under sticky footer: JS-click the [role=option] found by aria-label.
- Submit needs Talent Network/Privacy (DisclaimerText) checkbox; leave SMS unticked.
- GSK (jobs.gsk.com): React-safe keyboard typing for address/city/postal/phone (fill does not stick). Date fields are month pickers: pick year then click month. Screening = native selects (eligible Yes, sponsorship No, govt No, relationships No, other opportunities No, accuracy Yes).
- NTT DATA (careers.nttdata.com): phone "+91<phone>" with country India (10 digits = Invalid); State typeahead (type "<first letters of state>", click option); react-datepicker rejects typing; SUBMIT disabled ~10s before thank-you. Only 4 steps (info, questions, disclosure agree, review), with no experience step. The State typeahead is blank on review, but Submit still works.

## Ecolab (jobs.ecolab.com)
- The job page has no Apply button. Open /global/en/apply?jobSeqNo=<id> directly; no login needed. Deny cookies, then upload the resume to the file input.
- Selects: `$AB select` with the option text. The degree list has no B.E.; use "Bachelor's Degree (3 or 4-year...)".
- "Next" is slow. Check the URL step before deciding it failed.
- Never type into the GPA field after Next has fired: the stray keys get appended (one GPA was saved as "9.2082025").

## Veralto (jobs.veralto.com)
- No login. Open /global/en/apply?jobSeqNo=<id> directly.
- Resume parsing drops the <current employer> start date and changes its location to Mumbai. Fix both.
- The start date uses a react-datepicker: set the year select, then JS-click the option with aria-label "Choose August 2025". Setting the input value with the native setter does not stick.
- Remove #onetrust-consent-sdk before clicking Next.
- Application questions are native selects; set them by option value.

## Cisco (careers.cisco.com)
- No login. Reject cookies and remove #onetrust-consent-sdk so Apply becomes clickable. Resume parsing drops the <current employer> start date and sets its location to Mumbai: fix both, using the datepicker steps under Veralto.
- `#consent` is the "Send SMS" opt-in: leave it unticked. Tick only `#IndiaConsent` (privacy).
- Next stays disabled for about 10s on each step.

## GE HealthCare (careers.gehealthcare.com)
- No login. Open /global/en/apply?jobSeqNo=<id> directly. Set fields by element id with the native value setter, then fire input, change and blur.
- Resume parsing leaves address, city and state blank, and sets the <current employer> location to Mumbai with no start date. Fix them using the Veralto datepicker steps.
- Degree "Bachelor's", field of study "Computer Science". Next needs a real click (about 5s). Submit takes about 15s to reach /applythankyou.

- Ecolab: the start-date datepicker input sits under the sticky footer and `$AB click` fails. `el.focus()` via eval, set the `.react-datepicker select` year, then JS-click `[aria-label="Choose <Month> <Year>"]`. `selectedOptions` read right after setting a select can be stale; re-check after Back/Next.

- FIS (careers.fisglobal.com): Next stays disabled 30-60s per step, so poll the URL for the next step= value instead of re-clicking. The resume parse leaves <current employer> location/start date wrong and prefills phone as 91<phone>; fix both. Native-setter select values do not stick, so use `$AB select`. Two "Next" refs: ignore the slick carousel arrow, use the bottom btn-next. PAN question = checkbox labels, not a select. Parse also leaves <earlier employer> company blank.
- WEX (careers.wexinc.com): no login. No B.E. degree option, so use "Bachelor´s Degree or Equivalent (BAC+3 or 4)" and field "Computer and Information Science". Terms step has 2 required checkboxes. Source is a native select, "LinkedIn". On review the phone reverts to 91<phone>: click Edit on My information, retype <phone> with real keys, press Tab, then Next. Education dates are optional (typing into them does not stick).
- Roche (careers.roche.com): starts with an email code step (`otp --match roche --len 6`, 6 boxes). Degree "Bachelors Degree". The supplementary-questions Next works only after you re-dispatch change events and wait. Fields are addressed by id, not name (`[id="..."]`). Device Type (Mobile) is required on My information. Expected salary and notice period are free text on the supplementary step.

- Cisco (careers.cisco.com): the job-page Apply goes to /global/en/hvhapply?jobSeqNo=<id>, then /apply?step=1. Resume parse is good, but <current employer>'s location stays "Mumbai" (no location input on step 2). Degree select needs "Bachelor of Engineering" (no field-of-study input). Questions: 3 selects (authorized Yes, sponsorship No, experience "4+ years").
- Quest Global: single-page form. Degree and Field of Study inputs only show placeholders ("Bachelors", "Computer Science") and are really empty; type with real keys or Submit fails silently with "Field Required". The resume parse can leave a Role Description over 1000 chars, so shorten it. Submit fails silently, with no error, if a Role Description is too long (~1700 chars), so keep each under about 1000 chars (keyboard type). Country/Gender are selects; Degree and Field of Study are text inputs.
- Cigna (jobs.thecignagroup.com): no login. Upload resume FIRST (it resets City to Mumbai), then fix City/phone by real typing; dismiss the "resume uploaded" modal (OK) or Next stays disabled. Degree "Bachelors", field "Computer and Information Science". Clear stray "Computer Science" in Role Descriptions. 7 native-select questions (a Yes, b–g No). Final: citizenship "Citizen (India)" + terms. Submit takes ~15–20s to applythankyou.
- Adobe (careers.adobe.com): no login; Apply now → /apply?step=1. Upload resume first (sets City Mumbai, phone 91…), then fix via native setter on ids like `cntryFields.city`, `phoneWidget.phoneNumber`. All 3 starred consents required (incl. email). Degree "Bachelors", field COMPUTER_AND_INFORMATION_SCIENCE; refill blank <earlier employer> company/location. Submit needs a native click.
- PwC (jobs-ta.pwc.com, Phenom-style 6-step form, no login): the job page renders no Apply button, so open /global/en/apply?jobSeqNo=<id> directly. "How Did You Hear" = Job Posting Sites (via `$AB select`) loads the Source options; LinkedIn is among them. DOB is a react-datepicker: select the year and month in the picker, then JS-click the day's aria-label. The two talent-pool and communication consent selects are required but accept No. Resume parse sets the location to Mumbai: change it to <city>. The form is now 6 steps (Jun 2026). Submit and Next are missing from `snapshot -i` while the DOB datepicker is open: press Escape, JS-click the last "Next", then `$AB click @ref --human` on Submit. Variable pay textarea accepts "0"; fixed pay accepts <CTC as a number>.
- HPE (careers.hpe.com): selects only stick with `$AB select "[id=...]"`; the native-setter approach does not work. Questionnaire ids contain dots, so use getElementById, not name. No State field. Required: Phone Device Type (Personal Mobile), an AI-consent checkbox, and a notice-agreement checkbox.
- Franklin Templeton (careers.franklintempleton.com): open /us/en/apply?jobSeqNo=<id> directly, no login. Education field has no "Computer Science" option, so use "Applied Computer Science". Degree is "Bachelor's Degree or equivalent experience". Compensation is free text ("Negotiable. Current fixed CTC is <current CTC>."). Voluntary step is gender only. Each Next takes about 12s.
- HPE Cloud Developer III (2026-11): 5 steps. Step 1 needs Device Type (Personal Mobile), the AI-consent checkbox and the notice-agreement checkbox; name arrives uppercase and phone prefills, so retype both. Step 3 has 9 selects (No/Not Applicable, one NO, one textarea "N/A"). Step 4 needs Gender and a terms checkbox.
- HPE Senior Cloud Developer (2026-11): step 3 has 8 selects plus a textarea (the 9-select note above is for Cloud Developer III). Picking Country India adds optional Local name fields. $AB select works with "NO" and "Not Applicable" labels.
- Franklin Templeton AI Software Engineer (2026-11): the Source select loads only after a "Job Board" or "Social Network" pick, so choose Job Board, then LinkedIn (via $AB select). Device Type options are Mobile/Landline. Resume parse sets location to Mumbai. Submit with --human worked.
- eBay (jobs.ebayinc.com, 2026-11): Apply Now opens a no-login 5-step form. Selects need `$AB select "[id='...']"`. Step 3 has 4 selects (non-compete No, retain data No, former employee No, relocate "Open to relocation"). Step 4 needs Gender and 2 checkboxes. Degree "Bachelors Degree or Equivalent", field "Computer and Information Science".
- HPE Storage AI Engineer (2026-11, careers.hpe.com): step 3 has 8 selects plus a textarea. Answers used: a, c, d, e, f = No; b = NO; h and i = Not Applicable; the g textarea = N/A. Step 1 firstName/lastName arrive in uppercase and the phone prefills as 91<phone>; fix both with the native setter. The step 2 resume parse was correct.
- HPE (careers.hpe.com, step 1): Country defaults to United States of America. Select India first; the address fields and the +91 phone code then appear.
- Quest Global (careers.quest-global.com, Phenom): the apply page works directly at /global/en/apply?jobSeqNo=<id>. The Role Description field parsed at 1706 characters, so retype it under 1000.
