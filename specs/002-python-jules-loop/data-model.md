# Data Model

## Entities

### LoopConfiguration
- **Required fields**: JULES_API_KEY, GITHUB_TOKEN, GITHUB_REPO
- **Optional fields**: TARGET_BRANCH, PROMPT, PROMPTS, EXECUTION_TIMEOUT_SECS, RETRY_MAX, RETRY_BASE_SECS, POLL_INTERVAL_SECS, POLL_INITIAL_DELAY_SECS, QUOTA_DAILY_LIMIT, DRY_RUN
- **Validation rules**:
  - Numeric fields are positive integers.
  - PROMPTS, when provided, is a JSON array with objects containing text and probability.
  - Sum of prompt probabilities is approximately 1.0.

### LoopState
- **Fields**: current_agent, quota_used, quota_reset_date, paused, pause_reason
- **current_agent fields**: id, name, prompt, status, start_time, retry_count
- **Validation rules**:
  - paused is boolean-like.
  - retry_count is a non-negative integer.

### LogEntry
- **Fields**: timestamp, event, message, agent_id (optional), details (optional)
- **Validation rules**:
  - timestamp is ISO-8601 UTC.
  - event is a known event type string.

### Session
- **Fields**: id, name, prompt, status, pr_url (optional), pr_number (optional)
- **Validation rules**:
  - status in {running, pr_found, merged, failed, paused, timeout}.

## Relationships
- LoopConfiguration drives LoopState initialization and runtime behavior.
- LoopState references a Session via current_agent.
- LogEntry references Session via agent_id when available.

## State Transitions
- Session: created -> running -> pr_found -> merged
- Session: created -> running -> timeout
- Session: created -> running -> failed
- Loop: running -> paused (on merge conflict or quota exhaustion)
