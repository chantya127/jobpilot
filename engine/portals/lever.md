# lever notes

### Lever (jobs.lever.co)
- Resume upload clears "Current location" (plain text) -> refill after. Visible hCaptcha on Submit -> pending-user.
- hCaptcha iframe may exist without visible "captcha" text: after Submit, check for iframe[src*=hcaptcha] → pending-user.
