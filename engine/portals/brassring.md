# Brassring (sjobs.brassring.com; *.contacthr.com links redirect here: Deltek, JPMorganChase)
- Use "Skip sign in" to apply as a guest.
- The resume upload sits in an iframe: `$AB upload @<Browse button ref>`.
- Parsing the resume wipes the contact fields (refill them) and drops your current job. Add it back by hand; dates look like "Aug-2025".
- Country and state are typeahead comboboxes: clear the input with the native value setter, type the text, then click the option.
- Dropdowns such as travel: focus, ArrowDown, Enter.
- It worked if the page shows "Application Complete".
