# Taleo (e.g. uhg.taleo.net)
- UHG careers Apply → uhg.taleo.net; "Apply as Guest" with email only works (no account).
- Resume parse may drop the latest job (<current employer>) → add via "Add Work Experience".
- Country Code field max 3 chars → "91".
- Current/Ending Salary required on every work entry; use "NA" when profile has no figure.
- Source: no LinkedIn in Job Board list → Source Type "Other", detail "LinkedIn".
- Success: "Step 1 – Application complete".

## UnitedHealth (account now exists, 2026-11-07)
- Account: the username is the secrets.env email and the password is the secrets.env password (set on 2026-11-07). Sign in directly.
- Account recovery: guest apply fails because the email already has a record. Click Send Email, then `otp --match UnitedHealth --link taleo` (the default link regex misses it). The email body holds a temporary username and access code (read it with jobtool `body_text`). Sign in with them, then reset the username and password as above and reopen jobapply.ftl.
- Success text: "Process completed".
- Taleo sign-in may ask an emailed "Multifactor authentication access code" (alphanumeric + symbols, e.g. $Y56FUjBr7!): otp --match/--len misparse it; read the mail body via jobtool recent_messages/body_text, fill single-quoted. UHG/Optum: Source Type "Other" can error "Please Specify is mandatory" and the Source section vanishes -> click the Attachments step link, then Save and Continue again.
- Burns & McDonnell (rr.jobsyn.org → burnsmcd.jobs → apply.burnsmcd.com): account exists and now uses `password_strong` (reset 2026-11-08). Recover Password emails a temp access code: sign in with the creds email as username plus the code, then set a new password. Employer/Institution are lookup-list picks ("Other IT companies", "<your university>"). Education needs Country/State/Region (<city>) in the "Other Institution Location" selects. Save and Continue works only via an eval click.
- UnitedHealth Group (careers.unitedhealthgroup.com, Taleo): sign-in now always asks for an emailed MFA access code. Read it from the mail body (format like LT#Xy21BOG) and fill it quoted. The Source Tracking section disappears after the first Save and Continue: click the Attachments step link, then Save and Continue twice. Submit: `$AB click "[id$=submitCmdBottom]" --human`. Confirmation: "Process completed". If the session is still signed in, About You and Education/Experience prefill; only the Job Profile Questions (PM201 Yes) and the eSignature Full Name need filling.
