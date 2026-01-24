# jules-interesting-app-automation Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-24

## Active Technologies

- Python 3.11 + Python standard library only (no third-party dependencies) (002-python-jules-loop)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes

- 002-python-jules-loop: Added Python 3.11 + Python standard library only (no third-party dependencies)

<!-- MANUAL ADDITIONS START -->
## Overview

- Continuous agent loop that creates Jules sessions, waits for PRs, and merges them via GitHub API.
- Primary entrypoint: `scripts/jules-loop.py` (Python 3.11 stdlib only). Wrapper: `scripts/jules-loop.sh`.

## Key Files

- `scripts/jules-loop.py`: main loop, env parsing, API calls, state/log handling.
- `example.env`: environment variable template.

## Runtime Artifacts

- `.jules/state.json`: persistent loop state (current agent, quota, pause info).
- `.jules/log.jsonl`: append-only event log (JSON lines).

## Environment

Required: `JULES_API_KEY`, `GITHUB_TOKEN`, `GITHUB_REPO`.

Optional: `TARGET_BRANCH`, `PROMPT`, `PROMPTS` (JSON array), `EXECUTION_TIMEOUT_SECS`, `RETRY_MAX`,
`RETRY_BASE_SECS`, `POLL_INTERVAL_SECS`, `POLL_INITIAL_DELAY_SECS`, `QUOTA_DAILY_LIMIT`, `DRY_RUN`.

## Local Run

- `python3 scripts/jules-loop.py`

## Behavior Notes

- Retries transient HTTP errors with exponential backoff (base * 3^n).
- Pauses the loop on merge conflicts, quota exhaustion, or repeated failures; see `.jules/state.json`.
<!-- MANUAL ADDITIONS END -->
