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
| **Job preferences** | Keywords, avoid-companies list, stack filter (your languages, plus a skip list of languages, tools or keywords: any job requiring one is skipped) |
| **Find jobs** | Scrolls back through your LinkedIn job alerts (the last *N* notifications, none older than *D* days), skips anything already seen, and queues the company apply links. A live feed shows each step, with a Stop button. Optional keyword searches |
| **Queue** | Paste links. Duplicates and already-applied jobs are dropped |
| **Live agents** | 1–4 parallel workers side by side, each with its current step, a live log you can scroll freely, and Stop / Show browser buttons. **Talk to the orchestrator** in plain language (“skip Workday jobs today”, “retry the Stripe one”, “what is worker 2 stuck on?”) |
| **Needs you** | Forms waiting for your review, captchas, missing email codes, and questions about you. An answer you give here is saved for next time |
| **Tracker** | Every job and its status, with search and CSV import/export |
| **Settings** | Auto-submit on/off, number of workers, browser, portal login, Gmail codes |

## Requirements
Works on **macOS, Linux and Windows 10/11** (native; no WSL needed).

| Need | Why | Check |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | installs Python 3.10+ and the dependencies, runs the dashboard | `uv --version` |
| Node.js 20+ | runs agent-browser | `node -v` |
| [agent-browser](https://www.npmjs.com/package/agent-browser) | lets the agents drive the browser | `agent-browser --version` |
| [Claude Code](https://docs.claude.com/en/docs/claude-code), logged in | runs the agents (Pro/Max plan or API key) | `claude --version` |
| Chrome, Brave, Chromium or Edge | the worker windows | — |
| `curl` | the browser wrapper scripts use it (built into macOS, Windows 10+ and Git Bash) | `curl --version` |
| **Windows only:** [Git for Windows](https://git-scm.com/download/win) | Claude Code runs the agents' shell commands in Git Bash | `git --version` |
| Optional: Gmail with 2-Step Verification | lets agents read verification codes automatically | — |

## Install

### macOS
```bash
# Homebrew (https://brew.sh) is the easiest route
brew install uv node
brew install --cask google-chrome          # skip if you already have Chrome, Brave, Chromium or Edge
npm install -g agent-browser
curl -fsSL https://claude.ai/install.sh | bash
claude                                     # log in once, then exit with /exit
```

### Linux (Debian/Ubuntu shown; use your package manager's equivalents elsewhere)
```bash
sudo apt update && sudo apt install -y curl git
curl -LsSf https://astral.sh/uv/install.sh | sh
# Node.js 20+ (distro packages are often too old). nvm needs no sudo:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.nvm/nvm.sh && nvm install 22
npm install -g agent-browser
curl -fsSL https://claude.ai/install.sh | bash
claude                                     # log in once, then exit with /exit
# A Chromium-family browser, e.g. Chromium:
sudo apt install -y chromium || sudo snap install chromium
```
Fedora: `sudo dnf install -y curl git chromium`. Arch: `sudo pacman -S curl git chromium nodejs npm`.
You need a desktop session: the worker windows are real browser windows.

### Windows 10/11 (PowerShell)
```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Google.Chrome -e       # skip if you already have Chrome, Brave or Edge (Edge is preinstalled)
# Close and reopen PowerShell so the new PATH entries load, then:
npm install -g agent-browser
irm https://claude.ai/install.ps1 | iex
claude                                     # log in once, then exit with /exit
```
Use the native Claude Code installer above rather than `npm i -g @anthropic-ai/claude-code`: it gives you
`claude.exe`, which handles long prompts reliably. If Git is installed somewhere unusual, set
`CLAUDE_CODE_GIT_BASH_PATH` to its `bin\bash.exe`.

### Then, on every OS
```bash
git clone https://github.com/chantya127/jobpilot.git
cd jobpilot
uv sync                    # creates .venv with Python 3.10+ and all dependencies
uv run jobpilot --check    # verifies every requirement; prints the fix for anything missing
uv run jobpilot            # starts the dashboard and opens http://127.0.0.1:8765
```
Add `--deep` to `--check` to also confirm the Claude Code login (uses a few tokens). Use `--port 9000` if 8765 is
taken, and `--no-browser` to not open a tab automatically.

Then follow the **Setup** page: upload your resume → **Draft from my resume** → check the fields → set preferences →
paste a few links into **Queue** → **Start**.

**Auto-submit is ON by default**: agents submit each application once every field is filled and checked. To review
forms first, turn it off in **Settings**. Agents then stop before the final Submit, a review lock in the page stops
any accidental submit, and each form waits in *Needs you* for you to check, unlock and submit.

### Updating
```bash
git pull && uv sync
```
Your data lives outside the repo (see below), so updates never touch it.

## Installing with an AI agent (Claude Code, etc.)
If you're an agent asked to install JobPilot for a user, follow these steps in order and stop at the first failure.
1. Detect the OS (`uname -s` on macOS/Linux; on Windows, PowerShell's `$env:OS` is `Windows_NT`).
2. Install the requirements with the commands for that OS in **Install** above. Skip anything already present (use the
   Check column of the Requirements table). Don't use `sudo npm`: on Linux use nvm, as shown. On Windows, open a new
   shell after `winget` installs so PATH updates load.
3. In the repo: `uv sync`, then `uv run jobpilot --check`. It exits 0 when everything is ready and 1 otherwise, and
   prints a `fix:` line for each missing item. Apply the fixes and run it again until it exits 0.
4. **Leave these to the user** (they need a person; don't attempt them, just tell the user):
   - logging in to Claude Code (`claude` in a terminal, then `/exit`);
   - logging in to LinkedIn and job portals in the worker browser (Settings → Open worker browser);
   - creating a Gmail app password (optional, for email codes);
   - entering personal details, the resume, and choosing auto-submit on/off.
5. Start the dashboard with `uv run jobpilot` (keeps running; stop with Ctrl-C) and tell the user to open
   http://127.0.0.1:8765 and follow the Setup page.

Do not put personal data, resumes or secrets in the repo. Everything personal goes in the data directory.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `uv: command not found` right after installing | Open a new terminal (PATH changed). Linux/macOS: `source ~/.local/bin/env` also works |
| `claude` / `agent-browser` not found | Open a new terminal. Check `npm prefix -g` is on your PATH |
| Setup shows *Chromium-based browser: none found* | Install one, or set its full path in **Settings → Browser** |
| Port 8765 already in use | `uv run jobpilot --port 9000` |
| Windows: agents fail with "bash not found" / Git Bash errors | Install Git for Windows, or set `CLAUDE_CODE_GIT_BASH_PATH` to `C:\Program Files\Git\bin\bash.exe` |
| Windows: `$'\r': command not found` in a worker log | Your checkout has CRLF line endings. Run `git config core.autocrlf false`, then `git rm --cached -r . && git reset --hard` (the repo's `.gitattributes` forces LF) |
| Linux: worker window doesn't appear | Run from a desktop session (X11/Wayland), not a bare SSH shell |
| Agents can't open the worker browser | Close any other window using the same worker profile, then **Settings → Open worker browser** |
| macOS: "Brave/Chrome is damaged" or a permissions prompt | Open the browser once by hand and approve it |

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
  trusted clicks), and portal notes written up from hundreds of real applications. On Windows the agents run these in
  Git Bash, which is why Git for Windows is required there.
- **Your data** (`~/.jobpilot/`, on Windows `%USERPROFILE%\.jobpilot\`, or wherever `JOBPILOT_HOME` points): `profile.json`, `profile.md`, `resumes/`, `settings.json`,
  `secrets.env` (owner-only on macOS/Linux), `jobpilot.db`, `browser-profiles/`, `logs/`. It is never inside the repo.
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
