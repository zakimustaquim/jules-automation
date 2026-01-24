# Quickstart

## Prerequisites

- Python 3.11 installed
- Valid `JULES_API_KEY`, `GITHUB_TOKEN`, and `GITHUB_REPO`

## Run the Loop

```bash
python3 /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
```

## Optional Configuration

Set any of the optional environment variables to adjust prompt selection, polling intervals, retries, quota limits, or dry-run behavior.

## Verify

- Check `.jules/log.jsonl` for recent events.
- Check `.jules/state.json` for current loop state.
