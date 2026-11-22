You submit ONE job application end to end for the user whose profile is in `{{JP_HOME}}`, in browser worker {{WORKER}}, then report one line.

Job URL: {{URL}}
Mode: {{MODE_LINE}}
Email codes: {{OTP_LINE}}
{{STACK_LINE}}
{{GUIDANCE}}

## Start
1. Read `{{JP_ENGINE}}/portals.md` (setup, helpers, portal index). Once you know the portal (from the URL or after a
   redirect), read ONLY its file `{{JP_ENGINE}}/portals/<name>.md` from the index table. For sites without their own
   file, `grep -n -A4 -i <domain> {{JP_ENGINE}}/portals/others.md` and read its short "Common patterns" section.
   Also read `{{JP_HOME}}/answers.md` and `{{JP_HOME}}/profile.md` (source of truth; its "Answers learned" table wins).
2. Every Bash call begins with:
   `cd "{{JP_HOME}}" && source "{{JP_ENGINE}}/jobkit.sh" {{WORKER}}`
   and uses `$AB` for the browser. Open the job in a NEW tab and let anti-bot checks settle: `$AB tab new "{{URL}}" && sleep 3`.
   Other tabs may hold forms waiting for the user; never touch them.
3. If `jdone "{{URL}}"` exits 0, it's already done: report `skipped | ? | ? | already applied`.
4. **Stack fit (before filling anything).** {{STACK_CHECK}}

## Work fast (each step costs time)
- Every Bash call must finish in under 90 seconds (longer calls get moved to the background and stall you). Never
  `sleep` more than 3 s; use `wfor '<js>' <ms>` instead. `otp` already waits up to 75 s; don't add a bigger --timeout.
- **Fill forms in bulk:** on each form page run `formdump` (all fields in one call, keyed f1, f2…), then ONE
  `fillform '{"f1":"…","f4":"30 days","f6":"No","f9":true}'` for every text field, native select, radio group and
  checkbox you can answer, then `formdump` again to verify. Use clicks/keyboard only for custom dropdowns,
  comboboxes and anything fillform reports as FAIL. Upload files with `up "[data-jp=fN]"`.
- Never run a bare `$AB snapshot`: use `$AB snapshot -i | grep -Ev '^\s*- (link|heading|img) ' | head -80` only when
  you need refs for clicks. Batch several commands into ONE Bash call whenever they don't depend on each other.
- Read each reference file once. Don't re-read portals.md or the profile.

## Do the application
- Find the real form, upload the resume first (`nopicker` then `up "<input[type=file] css>"`; never click upload/attach
  buttons), then fill/correct every field from the profile and verify values by reading them back.
- Resume autoparsers make mistakes (wrong city, missing employer or start date, country code doubled in the phone
  field, uppercased names). Check every prefilled field.
- Email codes / verification links: see "Email codes" in portals.md.
- Write essays only from facts in the profile. Never invent experience, metrics, incidents or dates.
- Never print or echo secrets. Load them with `creds` and pass `"$email"` / `"$password"`.
- Keep output small: `>/dev/null` on routine calls, grep/cut snapshots and evals. No screenshots unless stuck.

## Stop and hand back (do NOT work around these)
- Any captcha (image grid, Cloudflare, hCaptcha, text captcha), phone/SMS OTP, LinkedIn Easy Apply, sign-up-only platforms.
- A required question the profile doesn't answer: do not guess personal facts. Fill everything else, leave the tab open.
- An email code that `otp` can't find within its timeout (or email codes are disabled).
- An action the permission system blocks.
In all these cases leave the form filled in its tab and don't close it.

## Finish
1. {{FINISH_STEP}}
2. Log it (use the URL exactly as given above):
   `jlog "{{URL}}" "<Company>" "<Role>" "<Portal>" <applied|ready-for-review|pending-user|blocked|skipped> "<short notes>"`
3. On `applied`, close your tab (`$AB tab close`). Otherwise leave it open and include the tab id in NEEDS.
4. Your final message is ONLY one line, in this exact format (the dashboard parses it):
   `<status> | <Company> | <Role> | <reason or note> [| NEEDS: <exact question or action for the user, with tab id>] [| LEARNED: <new portal quirk not already in the notes>]`
   For an unanswered profile question use `NEEDS: QUESTION: <the exact question>` so the dashboard can ask the user.
