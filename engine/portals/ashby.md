# ashby notes

### Ashby (jobs.ashbyhq.com)
- Open `<job-url>/application`; resume `#_systemfield_resume`. Yes/No are buttons; location is an autocomplete (type <city>, click "<City, State, Country>").
- Click "Submit Application" via `$AB click @ref` (JS click sometimes doesn't fire). Success text "successfully submitted". A visible reCAPTCHA challenge (bframe iframe height > 100) → pending-user, leave the tab.

- Number fields (e.g. WhatsApp) can come out mangled after `$AB fill`: read the value back and refill if it differs (Protegrity, 2026-11-15).

### engradar.com/jobs/ashby:<org>:<id> links
- They redirect to jobs.ashbyhq.com/<org>/<id>; open `<that>/application`. Salary is a combobox that lists options only after you type "INR": pick the matching bucket (SurveyMonkey: 3,000,000-4,000,000 INR, 2026-11-15).

### Company sites embedding Ashby (sycamore.so)
- Open the direct jobs.ashbyhq.com/<org>/<id>/application link from the iframe. Stale ref on first Submit: re-snapshot, click again.
- The first Submit click can return "Unknown ref" (the page re-rendered): re-snapshot and click Submit again. Same for radios/checkboxes right after a combobox pick: click them one per call. Gender and race are separate radio groups.
- Location combobox: `$AB fill` then click the option (keyboard type after a click lands in the wrong field).
- Handshake (joinhandshake.com/careers/job?ashby_jid=<id>) renders no job → open jobs.ashbyhq.com/handshake/<id>/application.
- Location field can be a plain text input with no dropdown: just fill "<City, State, Country>". Yes/No button state shows via an `_active_` class. ClickHouse submitted successfully (Go/Python accepted; Postgres 4 yrs; AI-evaluation consent Yes).
- The first Submit click on Ashby can seem to do nothing, with no error shown. A second trusted click produced the "successfully submitted" page (Sentient).
- Sarvam (Ashby): a per-applicant cap of applications within 60 days ("You have reached the maximum number of applications allowed within 60 days"). Skip other Sarvam roles until the window passes.
- Date field ("Pick date...") accepts MM/DD/YYYY typed followed by Enter. Notice-period options are checkboxes.
