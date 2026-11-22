# eightfold notes

### Eightfold (e.g. jobs.ascendion.com)
- Data Privacy popup after resume upload → "I Agree"; afterwards target fields by `[id="..."]`. Number fields: clear + Backspace + type, check value. Date: `td[title="YYYY-MM-DD"]`.

## Infineon (jobs.infineon.com)
- A ref click doesn't close the Privacy Policy dialog: click Ok with a mouse click at its coordinates. For comboboxes, click, then click the option ref. Refs shift after each pick.
- From the Chrome worker, Submit returned "Error submitting application / Please try again later" 3 times. In Brave it worked first time.
- Brave combobox: `$AB scrollintoview @ref; $AB focus @ref; $AB keyboard type "<text>"`, then click the filtered option ref. Control+a doesn't clear the field, so use repeated Backspace. The Bangalore location chip is preselected.

- Ascendion: the form needs only the resume upload, "I Agree" on the privacy dialog, and Salutation. Salutation is required and not autofilled: scrollintoview, focus, click the combobox, pick "Mr.".

- Twilio (jobs.twilio.com): upload via input[type=file] on the job page, click "I Agree", then "Apply Now". The resume autofills City as Mumbai, so change it to <city>. Checkboxes under the sticky footer need scrollintoview before click.
- Qualcomm (careers.qualcomm.com): login is email + 6-digit code (`otp --match qualcomm --len 6`). Resume and contact info prefill. Still fill address line, postal code, state and gender, then tick "I consent".

- Applied Materials (careers.appliedmaterials.com, jobs.appliedmaterials.com; dsp.prng.co links redirect there): click Apply, then Apply Now (refs shift after upload). Upload on the job page and click Confirm on the privacy dialog. Set Country=India, Gender, How heard = Job Board or Social Media → LinkedIn, Worked before = No. The last "Yes" checkbox is consent; the first is "preferred name", so leave it.
