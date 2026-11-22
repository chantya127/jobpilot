# icims notes

### iCIMS (*.icims.com)
- Form is in an iframe: open its src with &in_iframe=1. Login asks email + phone; country code: click li[value=IN][role=option] in iframe contentDocument.
- Next -> hCaptcha challenge -> pending-user.

- Docusign (careers.docusign.com): links to indiacareers-docusign.icims.com/jobs/<id>/login. Open it with &in_iframe=1. The email gate shows an hCaptcha after you tick privacy, so it goes to the user before the form. After they solve it, a worker must still fill the whole application.
- Form lives in iframe #icims_content_iframe: `$AB frame "#icims_content_iframe"`, then `up 'input[id="PortalProfileFields.Resume_File"]'`. Parse sets city Mumbai + "+91" in phone -> fix. Address line 1 combobox: type, then click "— Enter Manually —". hCaptcha may appear at Submit Profile (Planview) -> pending-user.
- Native selects whose options load only after opening (HERE careers-here.icims.com): set via JS in the iframe (`contentDocument.getElementById(id)`, set `.value`, dispatch `change`); snapshot option refs are stale and give a box-model error. Time Zone has no IST, so pick +05:00 (Etc/GMT-5). HERE showed no hCaptcha at the email gate.
- SymphonyAI (jobs.symphonyai.com): even with &in_iframe=1 the form stays in #icims_content_iframe. hCaptcha can appear at the email gate (after ticking privacy) or after Submit Profile → pending-user; Candidate Questions come after.
- N-able (careers.n-able.com "Begin Your N-able Journey Here" → globalcareers-n-able.icims.com): no hCaptcha. Profile has a required "I certify the information is true" dropdown (rcf2191); the classifier blocked setting it → pending-user.
