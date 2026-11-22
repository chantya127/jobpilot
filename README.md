# JobPilot ✈

**A local dashboard where Claude Code agents fill in job applications for you, while you stay in control.**

You build a knowledge base (resume plus standard answers), paste job links or let JobPilot find them on LinkedIn, and
press Start. Each worker drives its own browser window: it opens the job, picks the portal-specific playbook (Workday,
Greenhouse, Lever, Oracle, Phenom, SuccessFactors and 10+ more), uploads your resume, fills every field from your
profile, answers screening questions from facts you gave it, and either **stops for your review** or **submits**. You
choose which.

Everything runs on your computer. Nothing is sent anywhere except to the job sites themselves and to Claude through
your own Claude Code login.

## Features
| Section | What you do there |
|---|---|
| **Setup** | A checklist that verifies every requirement and shows the fix for anything missing |
| **Knowledge base** | Standard answers (contact, pay, notice, eligibility, EEO…), work history, plus a markdown knowledge base. **Draft from my resume** fills it for you |
| **Resumes** | Upload several PDFs and pick the active one |
| **Job preferences** | Keywords, avoid-companies list, stack filter (e.g. only Python/Go/Node roles) |
| **Find jobs** | Scrolls back through your LinkedIn job alerts (the last *N* notifications, none older than *D* days), skips anything already seen, and queues the company apply links. A live feed shows each step, with a Stop button. Optional keyword searches |
| **Queue** | Paste links. Duplicates and already-applied jobs are dropped |
| **Live agents** | 1–4 parallel workers side by side, each with its current step, a live log you can scroll freely, and Stop / Show browser buttons. **Talk to the orchestrator** in plain language (“skip Workday jobs today”, “retry the Stripe one”, “what is worker 2 stuck on?”) |
| **Needs you** | Forms waiting for your review, captchas, missing email codes, and questions about you. An answer you give here is saved for next time |
| **Tracker** | Every job and its status, with search and CSV import/export |
| **Settings** | Auto-submit on/off, number of workers, browser, portal login, Gmail codes |

## Requirements
| Need | Why |
|---|---|
| macOS or Linux (Windows: use WSL) | the browser helpers are bash scripts |
| [uv](https://docs.astral.sh/uv/) (installs Python 3.10+ for you) | runs the dashboard |
| Node.js 20+ | for agent-browser |
| [agent-browser](https://www.npmjs.com/package/agent-browser) `npm i -g agent-browser` | lets the agents control the browser |
| [Claude Code](https://docs.claude.com/en/docs/claude-code) `npm i -g @anthropic-ai/claude-code`, logged in | runs the agents (Pro/Max plan or API key) |
| Chrome, Brave, Chromium or Edge | the worker windows |
| Optional: Gmail with 2-Step Verification | lets agents read verification codes automatically |

## Quick start
```bash
git clone https://github.com/<you>/jobpilot && cd jobpilot
uv sync
uv run playwright install chromium   # only needed for Find jobs
uv run jobpilot                      # opens http://127.0.0.1:8765
```
Then follow the **Setup** page: upload your resume → **Draft from my resume** → check the fields → set preferences →
paste a few links into **Queue** → **Start**.

**Auto-submit is ON by default**: agents submit each application once every field is filled and checked. To review
forms first, turn it off in **Settings**. Agents then stop before the final Submit, a review lock in the page stops
any accidental submit, and each form waits in *Needs you* for you to check, unlock and submit.

## How it works
```
Dashboard (FastAPI, 127.0.0.1 only)
  ├─ Orchestrator ── for each free worker: next queued job (never two jobs on one portal tenant at once)
  │      └─ claude -p "<job-applier prompt>"  (headless Claude Code, Bash/Read/Grep only)
  │             └─ $AB = ~/.jobpilot/bin/abN → agent-browser → that worker's own browser (CDP port 9333+N)
  │             └─ jobkit.sh helpers + engine/portals/<ats>.md playbooks + your answers.md/profile.md
  │             └─ replies with one line: status | company | role | note | NEEDS: … | LEARNED: …
  └─ SQLite tracker, live event log, Needs-you inbox
```
- **Engine** (`engine/`): the worker prompt, `jobkit.sh` (bash helpers for Workday, Greenhouse, Hirist, uploads,
  trusted clicks), and portal notes written up from hundreds of real applications.
- **Your data** (`~/.jobpilot/`, or `$JOBPILOT_HOME`): `profile.json`, `profile.md`, `resumes/`, `settings.json`,
  `secrets.env` (chmod 600), `jobpilot.db`, `browser-profiles/`, `logs/`. It is never inside the repo.
- **Learning:** when an agent finds a new portal quirk, it reports `LEARNED:`, and the note is appended to
  `~/.jobpilot/portals-local.md`. Future runs read that file too. Please open a PR to share good ones in `engine/portals/`.

## What agents never do
- Solve or bypass captchas. They hand them to you.
- Automate LinkedIn Easy Apply.
- Invent experience, numbers or dates. Essays use only facts from your knowledge base.
- Guess personal facts. Unknown questions come to *Needs you*.
- Hide that an AI filled the form. If a form asks, the agent answers truthfully.

## Privacy & safety
- The server listens on `127.0.0.1` only. Secrets are write-only in the UI.
- Agents run with **Bash, Read and Grep** permissions inside `~/.jobpilot`. They have no file-editing or web-fetch tools.
- The Gmail app password gives read access to your mailbox. Agents only look for codes and verification links, and
  you can revoke the password at myaccount.google.com/apppasswords.
- Read [DISCLAIMER.md](DISCLAIMER.md). You are responsible for following each job site's terms.

## CLI use (without the dashboard)
```bash
uv run python -m jobpilot.tools log <url> <company> <role> <portal> <status> "<notes>"
uv run python -m jobpilot.tools otp --list --timeout 0
uv run python -m jobpilot.scraper
```

## Contributing
Portal notes are the most valuable contribution: keep each one to a few short bullets in the file for that ATS, or
under "Sites" in `engine/portals/others.md`. Never include personal data. `scripts/secret-scan.sh` should report nothing.

## License
MIT
