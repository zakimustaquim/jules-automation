# jules-interesting-app-automation

A continuous agent loop that uses the Jules API to create coding sessions, waits for PRs, and auto-merges them.

## Quick Start

1. **Prerequisites**
   - Jules API key (from https://jules.google.com/settings#api)
   - GitHub token with repo write access
   - `curl` and `jq` installed

2. **Setup**

   Create a `.env` file in the repository root:
   ```bash
   JULES_API_KEY=your_jules_api_key
   GITHUB_TOKEN=your_github_token
   GITHUB_REPO=owner/repo
   ```

3. **Run**
   ```bash
   ./scripts/jules-loop.sh
   ```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `JULES_API_KEY` | Your Jules API key |
| `GITHUB_TOKEN` | GitHub token with repo write access |
| `GITHUB_REPO` | Target repository in `owner/repo` format |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_BRANCH` | `main` | Branch to target for PRs |
| `PROMPT` | `Do something interesting in this codebase` | Prompt sent to Jules |
| `EXECUTION_TIMEOUT_SECS` | `1800` | Max time to wait for a session to produce a PR (30 min) |
| `RETRY_MAX` | `3` | Max retries for transient API errors |
| `RETRY_BASE_SECS` | `5` | Base delay for exponential backoff (5s, 15s, 45s) |
| `POLL_INTERVAL_SECS` | `15` | Interval between session status polls |
| `QUOTA_DAILY_LIMIT` | (none) | Optional daily session limit |
| `DRY_RUN` | `false` | If `true`, skip actual API calls |

## Output

The script creates a `.jules/` directory with:

- **`state.json`** - Current state (session info, quota, pause status)
- **`log.jsonl`** - Append-only event log (JSON lines format)

### Log Events

| Event | Description |
|-------|-------------|
| `info` | General information |
| `agent_created` | New Jules session created |
| `session_polled` | Session status checked |
| `pr_found` | PR URL discovered |
| `pr_merged` | PR successfully merged |
| `timeout` | Session timed out |
| `error` | Error occurred |
| `quota_exhausted` | Daily quota limit reached |
| `paused` | Loop paused (requires manual intervention) |
| `shutdown` | Graceful shutdown initiated |

## Error Handling

- **Transient errors** (429, 5xx): Retried with exponential backoff
- **Auth errors** (401, 403): Loop exits immediately
- **Merge conflicts** (405, 409): Loop pauses with PR details logged
- **Consecutive failures**: Loop pauses after 5 consecutive failures
- **Quota exhausted**: Loop pauses when daily limit reached

## Graceful Shutdown

Send `SIGINT` (Ctrl+C) or `SIGTERM` to gracefully stop the loop. State is flushed before exit.

