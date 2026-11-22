# Rippling ATS (ats.rippling.com)
- File inputs have no id: tag one via eval (`setAttribute("data-ja","file0")`), then upload `[data-ja=file0]`.
- Location autocomplete "<City, State, Country>". SMS consent No. The resume parse sets +91 IN, so don't type into the country-code combobox.
- A Cloudflare check can appear after Apply (fields lock, "Loading...") → pending-user.
- `fill` on the LinkedIn field appends to the resume-autofilled value instead of replacing it (on 2026-11-08 a garbled URL got submitted). Clear it first (select-all + Delete), then verify the value before clicking Apply.
- Clearing the prefilled LinkedIn field: Meta+a then Delete does not work. Click the field, press End, send about 90 Backspaces, then type the URL. Closing the confirmation tab can fail with "Cannot close the last tab"; leave it open.
- Location input can be covered by an overlay, so click fails. Use `$AB focus @ref`, type with the keyboard, then click the option.
- Active-application cap (2026-11-15): Rippling caps active applications per candidate. Once hit, every further Rippling Apply fails with "You've reached the limit of active applications". Skip Rippling jobs until existing applications close.
