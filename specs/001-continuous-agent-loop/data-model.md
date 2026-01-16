# Data Model

## AgentInstance
Represents one Jules session execution.

Fields:
- `id` (string): Jules session ID (e.g., `sessions/123...`).
- `prompt` (string): Always "Do something interesting in this codebase".
- `status` (string enum): `pending` | `running` | `completed` | `timed_out` | `failed`.
- `start_time` (ISO-8601 string)
- `end_time` (ISO-8601 string, nullable)
- `pr_url` (string, nullable)
- `pr_number` (number, nullable)
- `commit_sha` (string, nullable)
- `retry_count` (number): For current operation.

## QuotaState
Tracks Jules API quota and pacing.

Fields:
- `daily_limit` (number)
- `used` (number)
- `remaining` (number)
- `reset_at` (ISO-8601 string)
- `last_updated` (ISO-8601 string)

## ExecutionLog (append-only)
Each log entry is one JSON object in `.jules/log.jsonl`.

Fields:
- `timestamp` (ISO-8601 string)
- `event` (string enum): `agent_created` | `session_polled` | `pr_found` | `pr_merged` | `error` | `timeout` | `quota_exhausted` | `paused` | `shutdown`.
- `agent_id` (string, nullable)
- `message` (string)
- `details` (object, optional)

## Configuration
Configurable settings via env vars or a simple `.env` file.

Fields:
- `JULES_API_KEY` (string)
- `GITHUB_TOKEN` (string)
- `GITHUB_REPO` (string, `owner/repo`)
- `TARGET_BRANCH` (string, default `main`)
- `PROMPT` (string, fixed default)
- `EXECUTION_TIMEOUT_SECS` (number, default 1800)
- `RETRY_MAX` (number, default 3)
- `RETRY_BASE_SECS` (number, default 5)
- `POLL_INTERVAL_SECS` (number, default 15)
- `QUOTA_DAILY_LIMIT` (number, optional)
- `DRY_RUN` (boolean, optional)
