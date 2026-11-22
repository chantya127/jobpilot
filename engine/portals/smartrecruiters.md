# smartrecruiters notes

### SmartRecruiters oneclick (ServiceNow, PhonePe etc.)
- First check `https://api.smartrecruiters.com/v1/companies/<org>/postings/<id>` "active"; false -> skipped (closed). engradar.com links: check for "ROLE CLOSED".
- May show DataDome captcha iframe (geo.captcha-delivery.com) before form -> pending-user; after user solves, fill form.
- oneclick-ui (e.g. jobs.mattel.com → Apply now) is shadow DOM: after `nopicker`, `$AB upload @<ref of "Choose a file" button>` (CSS selector fails). Next/Submit report "covered by span" → `$AB focus @ref` then `$AB press Enter`.
- ServiceNow: Apply Now opens a new tab. Questions are shadow DOM, so read labels with `$AB snapshot` (no -i). Choosing "Yes" on the relocate dropdown adds a required "relocate at own expense" radio.
- Nemetschek (oneclick-ui): not shadow DOM. Upload with `$AB upload @ref` after `nopicker`. Pick the City option from the dropdown, then focus Next/Submit and press Enter. The long background-check/disclosure box is a text field: answer "Yes".
