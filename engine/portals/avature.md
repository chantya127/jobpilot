# avature notes

### Avature (*.avature.net, e.g. dth.avature.net = Delta)
- Account required: Apply Now -> Register -> From Computer, upload resume -> CONTINUE -> big Register form.
- Nationality / authorized-to-work / Highest Education = typeahead: click, then click option. Expected Salary numeric (<CTC as a number>).
- Password rule (8+, upper+lower+digit, no common word/personal info) REJECTS secrets.env password -> pending-user. Validation errors clear password fields.
- Rejects passwords containing the name ("<first name>"): both secrets.env passwords fail -> needs a password with no personal info.

### Deloitte USI (usijobs.deloitte.com)
- Mandatory Candidate Photo (passport-size) -> no file in repo, hand to user.
- Phone format +91XXXXXXXXXX. College/employer are select2: type "Other" + Enter (SPPU not listed).
- Month fields: set hidden input[type=month] via JS (YYYY-MM).

## BNP Paribas (group.bnpparibas → bwelcome.hr.bnpparibas)
- Apply leads to ApplicationMethods. Upload the CV to #resumeFile (no login needed), then Continue to the Register form.
- Register: fill in the phone number, upload the CV again to input[name=file_1394], choose "Only for the opening I am applying to", tick T&C.
- Password must be 15+ characters with a number and a symbol: use `password_strong` (the 13-character one is rejected). Continue, then Submit. A verification email follows.
- BNP account exists (email verified 2026-11-07). If login fails: "Resend verification email" → `otp --match bnpparibas --link`. After login, ApplicationConfirmation prefills the form: upload the CV to input[name=file_NNNN] (the number differs per job), tick T&C, Continue, then SUBMIT APPLICATION.
- DHL (dpdhlgroup.avature.net): no account; resume -> #resumeFile, Continue to Register; phone without +91, Preferred language English, resume again into input[name=file_4982], contact-for-offers No, Save and Next; final page has reCAPTCHA (user).
- Intuit (intuit.avature.net): account already exists for the profile email -> log in first; if secrets.env passwords fail use "Forgot your password?" + `otp --match intuit --link` (Avature rejects passwords containing name/personal info). Register form prefills edu/work from resume (fix Employer/title); required: privacy checkbox, Talent Community No, Text Message No.
- Siemens (jobs.siemens.com/externaljobs): account exists under password_strong (try it first). Register form needs the CV again in input[name="file_42348"]. Numeric ids: use [id="123"], not #123.
- MetLife (metlife.avature.net): creds password OK. Phone code/Country/Nationality are select2 ajax: click #select2-<id>-container, type, wait ~3s, (ArrowDown if a lookalike is first), Enter. Resume: nopicker + up "#resumeFile" + click From Device to reveal Continue. Register prefill City "LeetCode" → fix.
- Intuit (jobs.intuit.com, Avature): the login works with the secrets.env password_strong (plain password fails). Logging in skips the resume upload and uses the stored profile resume. The prefilled form needs fixing: remove the duplicate education row, add a <current employer> work row, and set the work-history selects by option value (7=Yes, 8=No). Success page shown.
