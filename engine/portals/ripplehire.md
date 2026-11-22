# ripplehire notes

### RippleHire (usource.ripplehire.com = UST)
- Privacy page first: "I Agree". Apply view may render blank -> reload.
- Ids: firstName, middleName, lastName, emailAddr, phoneNo, day/month/year (DOB, required selects), custom18 gender, expYears/expMonths, custom1 current company, currentCTC, expectedCTC, noticePeriodSelect, currentLocation, custom11/16/17 preferred locs, custom4 past UST radio, resume, custom6 work auth, termscondition.
- Submit: `document.querySelector("#btn-submit-app").click()` (overlay span blocks normal click).
- currentLocation required; may be blank after earlier fill -> check for "Please enter your location".
- Selects: one `$AB select "#id" "Option"` call each (don't chain); notice "1 month" = value 30.
- After submit, "#duplicate-check" / "We already have your profile with us" = already applied -> log skipped.

## 7-Eleven (7-eleven-gsc.ripplehire.com)
- If the first Apply Now click gives a blank page, reload and click "I Agree". The form has 2 steps: basic details, then Continue.
- Fields: indiaLocation (type "<city>", click the link), employerOther, currentCTC, noticePeriodSelect ("1 month"), expYears/expMonths, ex-employee radio No, termscondition. Submit with `#btn-submit-app`.click().
- PAN must be UPPERCASE ("Invalid PAN" otherwise). Mphasis: #currentLocation is Google Places (click, type "<city>", ArrowDown, Enter); notice period is free-text days; skills token inputs optional.
