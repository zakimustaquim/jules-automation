# Quickstart

## Prereqs
- Jules API key (from https://jules.google.com/settings#api)
- GitHub token with repo write access
- `curl` and `jq` installed

## Setup
1. Create a `.env` file or export environment variables:
   - `JULES_API_KEY=...`
   - `GITHUB_TOKEN=...`
   - `GITHUB_REPO=owner/repo`
   - `TARGET_BRANCH=main`

2. Run the loop script:
   - `./scripts/jules-loop.sh`

## Optional env vars
- `PROMPT` (default: "Do something interesting in this codebase")
- `EXECUTION_TIMEOUT_SECS` (default: 1800)
- `RETRY_MAX` (default: 3)
- `RETRY_BASE_SECS` (default: 5)
- `POLL_INTERVAL_SECS` (default: 15)
- `QUOTA_DAILY_LIMIT` (optional)
- `DRY_RUN=true` (skip merge and session creation)

## Output
- State file: `.jules/state.json`
- Log file: `.jules/log.jsonl`
