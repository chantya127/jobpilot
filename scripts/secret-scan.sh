#!/usr/bin/env bash
# Fails if tracked files contain obvious personal data. Add your own name/phone/email to PATTERNS locally.
PATTERNS=${JOBPILOT_SCAN:-'@gmail\.com|password=|app_password=|BEGIN [A-Z ]*PRIVATE KEY'}
cd "$(dirname "$0")/.." || exit 1
hits=$(git ls-files -z -- . ':!uv.lock' | xargs -0 grep -nIE "$PATTERNS" -- 2>/dev/null | grep -v 'scripts/secret-scan.sh' | grep -vE 'you@gmail\.com|you@example\.com|gmail_app_password=|password=\$|\$password')
if [ -n "$hits" ]; then echo "$hits"; echo "secret-scan: possible personal data found"; exit 1; fi
echo "secret-scan: clean"
