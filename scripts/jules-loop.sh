#!/usr/bin/env bash
#
# jules-loop.sh - Continuous Jules agent loop
#
# Creates Jules sessions with a prompt, waits for PR output,
# auto-merges via GitHub API, then starts the next session.
#
# Usage: ./scripts/jules-loop.sh
#
# Required env vars:
#   JULES_API_KEY   - Jules API key
#   GITHUB_TOKEN    - GitHub token with repo write access
#   GITHUB_REPO     - GitHub repo (owner/repo format)
#
# Optional env vars:
#   TARGET_BRANCH          - Branch to target (default: main)
#   PROMPT                 - Session prompt (default: "Do something interesting in this codebase")
#   EXECUTION_TIMEOUT_SECS - Max time per session (default: 1800)
#   RETRY_MAX              - Max retries for transient errors (default: 3)
#   RETRY_BASE_SECS        - Base retry delay (default: 5)
#   POLL_INTERVAL_SECS     - Polling interval (default: 15)
#   QUOTA_DAILY_LIMIT      - Optional daily session limit
#   DRY_RUN                - Skip actual API calls if "true"

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
JULES_DIR="$REPO_ROOT/.jules"
STATE_FILE="$JULES_DIR/state.json"
LOG_FILE="$JULES_DIR/log.jsonl"

JULES_API_BASE="https://jules.googleapis.com"

load_config() {
    # Load .env file if present
    if [[ -f "$REPO_ROOT/.env" ]]; then
        # shellcheck disable=SC1091
        set -a
        source "$REPO_ROOT/.env"
        set +a
    fi

    # Required env vars (validated later)
    JULES_API_KEY="${JULES_API_KEY:-}"
    GITHUB_TOKEN="${GITHUB_TOKEN:-}"
    GITHUB_REPO="${GITHUB_REPO:-}"

    # Optional env vars with defaults
    TARGET_BRANCH="${TARGET_BRANCH:-main}"
    PROMPT="${PROMPT:-Do something interesting in this codebase}"
    EXECUTION_TIMEOUT_SECS="${EXECUTION_TIMEOUT_SECS:-1800}"
    RETRY_MAX="${RETRY_MAX:-3}"
    RETRY_BASE_SECS="${RETRY_BASE_SECS:-5}"
    POLL_INTERVAL_SECS="${POLL_INTERVAL_SECS:-15}"
    QUOTA_DAILY_LIMIT="${QUOTA_DAILY_LIMIT:-}"
    DRY_RUN="${DRY_RUN:-false}"

    # Parse GITHUB_REPO into owner and repo
    if [[ -n "$GITHUB_REPO" ]]; then
        GITHUB_OWNER="${GITHUB_REPO%%/*}"
        GITHUB_REPO_NAME="${GITHUB_REPO##*/}"
    else
        GITHUB_OWNER=""
        GITHUB_REPO_NAME=""
    fi

    # Ensure .jules directory exists
    mkdir -p "$JULES_DIR"
}

# =============================================================================
# Logging
# =============================================================================

log_event() {
    local event="$1"
    local message="$2"
    local agent_id="${3:-}"
    local details="${4:-}"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    local entry
    if [[ -n "$details" ]]; then
        entry=$(jq -n \
            --arg ts "$timestamp" \
            --arg ev "$event" \
            --arg msg "$message" \
            --arg aid "$agent_id" \
            --argjson det "$details" \
            '{timestamp: $ts, event: $ev, message: $msg, agent_id: (if $aid == "" then null else $aid end), details: $det}')
    else
        entry=$(jq -n \
            --arg ts "$timestamp" \
            --arg ev "$event" \
            --arg msg "$message" \
            --arg aid "$agent_id" \
            '{timestamp: $ts, event: $ev, message: $msg, agent_id: (if $aid == "" then null else $aid end)}')
    fi

    echo "$entry" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$event] $message"
}

# =============================================================================
# State Management
# =============================================================================

init_state() {
    if [[ ! -f "$STATE_FILE" ]]; then
        echo '{}' > "$STATE_FILE"
    fi
}

read_state() {
    local key="$1"
    jq -r ".$key // empty" "$STATE_FILE"
}

write_state() {
    local key="$1"
    local value="$2"
    local tmp_file
    tmp_file=$(mktemp)
    jq --arg k "$key" --arg v "$value" '.[$k] = $v' "$STATE_FILE" > "$tmp_file"
    mv "$tmp_file" "$STATE_FILE"
}

write_state_json() {
    local key="$1"
    local json_value="$2"
    local tmp_file
    tmp_file=$(mktemp)
    jq --arg k "$key" --argjson v "$json_value" '.[$k] = $v' "$STATE_FILE" > "$tmp_file"
    mv "$tmp_file" "$STATE_FILE"
}

flush_state() {
    sync "$STATE_FILE" 2>/dev/null || true
}

# =============================================================================
# Retry with Exponential Backoff
# =============================================================================

retry_with_backoff() {
    local cmd="$1"
    local max_retries="${2:-$RETRY_MAX}"
    local base_delay="${3:-$RETRY_BASE_SECS}"
    local attempt=0

    while (( attempt < max_retries )); do
        if eval "$cmd"; then
            return 0
        fi

        attempt=$((attempt + 1))
        if (( attempt >= max_retries )); then
            return 1
        fi

        local delay=$(( base_delay * (3 ** (attempt - 1)) ))
        log_event "error" "Attempt $attempt failed, retrying in ${delay}s..."
        sleep "$delay"
    done

    return 1
}

# =============================================================================
# HTTP Helpers
# =============================================================================

LAST_HTTP_CODE=""

jules_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    local args=(
        -s
        -w "\n%{http_code}"
        -X "$method"
        -H "Authorization: Bearer $JULES_API_KEY"
        -H "Content-Type: application/json"
    )

    if [[ -n "$data" ]]; then
        args+=(-d "$data")
    fi

    local response
    response=$(curl "${args[@]}" "${JULES_API_BASE}${endpoint}")

    LAST_HTTP_CODE=$(echo "$response" | tail -1)
    echo "$response" | sed '$d'
}

github_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    local args=(
        -s
        -w "\n%{http_code}"
        -X "$method"
        -H "Authorization: Bearer $GITHUB_TOKEN"
        -H "Accept: application/vnd.github+json"
        -H "X-GitHub-Api-Version: 2022-11-28"
    )

    if [[ -n "$data" ]]; then
        args+=(-d "$data")
    fi

    local response
    response=$(curl "${args[@]}" "https://api.github.com${endpoint}")

    LAST_HTTP_CODE=$(echo "$response" | tail -1)
    echo "$response" | sed '$d'
}

is_transient_error() {
    local code="$1"
    [[ "$code" == "429" || "$code" == "500" || "$code" == "502" || "$code" == "503" || "$code" == "504" ]]
}

is_auth_error() {
    local code="$1"
    [[ "$code" == "401" || "$code" == "403" ]]
}

# =============================================================================
# Shutdown Handler
# =============================================================================

SHUTDOWN_REQUESTED=false

shutdown_handler() {
    if [[ "$SHUTDOWN_REQUESTED" == "true" ]]; then
        return
    fi
    SHUTDOWN_REQUESTED=true

    log_event "shutdown" "Graceful shutdown initiated"
    flush_state
    exit 0
}

trap shutdown_handler SIGINT SIGTERM

# =============================================================================
# Credential Validation
# =============================================================================

validate_credentials() {
    local errors=0

    if [[ -z "$JULES_API_KEY" ]]; then
        log_event "error" "JULES_API_KEY is not set"
        errors=$((errors + 1))
    fi

    if [[ -z "$GITHUB_TOKEN" ]]; then
        log_event "error" "GITHUB_TOKEN is not set"
        errors=$((errors + 1))
    fi

    if [[ -z "$GITHUB_REPO" ]]; then
        log_event "error" "GITHUB_REPO is not set"
        errors=$((errors + 1))
    fi

    if (( errors > 0 )); then
        return 1
    fi

    # Validate Jules API key
    log_event "info" "Validating Jules API credentials..."
    local jules_response
    jules_response=$(jules_api GET "/v1alpha/sources")

    if is_auth_error "$LAST_HTTP_CODE"; then
        log_event "error" "Jules API authentication failed (HTTP $LAST_HTTP_CODE)"
        return 1
    fi

    if [[ "$LAST_HTTP_CODE" != "200" ]]; then
        log_event "error" "Jules API validation failed (HTTP $LAST_HTTP_CODE)"
        return 1
    fi

    log_event "info" "Jules API credentials validated"

    # Validate GitHub token
    log_event "info" "Validating GitHub credentials..."
    local gh_response
    gh_response=$(github_api GET "/repos/$GITHUB_OWNER/$GITHUB_REPO_NAME")

    if is_auth_error "$LAST_HTTP_CODE"; then
        log_event "error" "GitHub authentication failed (HTTP $LAST_HTTP_CODE)"
        return 1
    fi

    if [[ "$LAST_HTTP_CODE" != "200" ]]; then
        log_event "error" "GitHub validation failed - repo not found or inaccessible (HTTP $LAST_HTTP_CODE)"
        return 1
    fi

    log_event "info" "GitHub credentials validated for $GITHUB_REPO"

    return 0
}

# =============================================================================
# Quota Tracking
# =============================================================================

QUOTA_USED=0
QUOTA_RESET_DATE=""

init_quota() {
    if [[ -z "$QUOTA_DAILY_LIMIT" ]]; then
        return 0
    fi

    local today
    today=$(date -u +%Y-%m-%d)

    local stored_date
    stored_date=$(read_state "quota_reset_date")

    if [[ "$stored_date" != "$today" ]]; then
        QUOTA_USED=0
        QUOTA_RESET_DATE="$today"
        write_state "quota_used" "0"
        write_state "quota_reset_date" "$today"
        log_event "info" "Quota reset for $today (limit: $QUOTA_DAILY_LIMIT)"
    else
        QUOTA_USED=$(read_state "quota_used")
        QUOTA_USED="${QUOTA_USED:-0}"
        QUOTA_RESET_DATE="$today"
    fi

    log_event "info" "Quota: $QUOTA_USED / $QUOTA_DAILY_LIMIT used"
}

check_quota() {
    if [[ -z "$QUOTA_DAILY_LIMIT" ]]; then
        return 0
    fi

    if (( QUOTA_USED >= QUOTA_DAILY_LIMIT )); then
        log_event "quota_exhausted" "Daily quota limit ($QUOTA_DAILY_LIMIT) reached"
        return 1
    fi

    return 0
}

increment_quota() {
    if [[ -z "$QUOTA_DAILY_LIMIT" ]]; then
        return 0
    fi

    QUOTA_USED=$((QUOTA_USED + 1))
    write_state "quota_used" "$QUOTA_USED"
    log_event "info" "Quota: $QUOTA_USED / $QUOTA_DAILY_LIMIT used"
}

# =============================================================================
# Fatal Error Handling
# =============================================================================

LOOP_PAUSED=false

pause_loop() {
    local reason="$1"
    LOOP_PAUSED=true
    log_event "paused" "Loop paused: $reason"
    write_state "paused" "true"
    write_state "pause_reason" "$reason"
    flush_state
}

# =============================================================================
# Jules Source Discovery
# =============================================================================

JULES_SOURCE=""

discover_source() {
    log_event "info" "Discovering Jules source for $GITHUB_REPO..."

    local response
    response=$(jules_api GET "/v1alpha/sources")

    local source_name
    source_name=$(echo "$response" | jq -r --arg owner "$GITHUB_OWNER" --arg repo "$GITHUB_REPO_NAME" \
        '.sources[]? | select(.githubRepo.owner == $owner and .githubRepo.repo == $repo) | .name' | head -1)

    if [[ -z "$source_name" ]]; then
        log_event "error" "No Jules source found for $GITHUB_REPO"
        return 1
    fi

    JULES_SOURCE="$source_name"
    log_event "info" "Found Jules source: $JULES_SOURCE"
}

# =============================================================================
# Session Management
# =============================================================================

CURRENT_SESSION_NAME=""
CURRENT_SESSION_ID=""
CURRENT_PR_URL=""
CURRENT_PR_NUMBER=""

create_session() {
    log_event "agent_created" "Creating new Jules session..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_event "info" "DRY_RUN: Skipping session creation"
        CURRENT_SESSION_NAME="sessions/dry-run-$(date +%s)"
        CURRENT_SESSION_ID="dry-run-$(date +%s)"
        return 0
    fi

    local payload
    payload=$(jq -n \
        --arg prompt "$PROMPT" \
        --arg title "Jules auto-session $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg source "$JULES_SOURCE" \
        --arg branch "$TARGET_BRANCH" \
        '{
            prompt: $prompt,
            title: $title,
            automationMode: "AUTO_CREATE_PR",
            sourceContext: {
                source: $source,
                githubRepoContext: {
                    startingBranch: $branch
                }
            }
        }')

    local response
    response=$(jules_api POST "/v1alpha/sessions" "$payload")

    CURRENT_SESSION_NAME=$(echo "$response" | jq -r '.name // empty')
    CURRENT_SESSION_ID=$(echo "$response" | jq -r '.id // empty')

    if [[ -z "$CURRENT_SESSION_NAME" ]]; then
        log_event "error" "Failed to create session" "" "$response"
        return 1
    fi

    log_event "agent_created" "Session created: $CURRENT_SESSION_NAME" "$CURRENT_SESSION_ID"

    # Save to state
    local agent_state
    agent_state=$(jq -n \
        --arg id "$CURRENT_SESSION_ID" \
        --arg name "$CURRENT_SESSION_NAME" \
        --arg prompt "$PROMPT" \
        --arg status "running" \
        --arg start "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{id: $id, name: $name, prompt: $prompt, status: $status, start_time: $start, retry_count: 0}')

    write_state_json "current_agent" "$agent_state"
}

poll_session() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_event "info" "DRY_RUN: Simulating PR found"
        CURRENT_PR_URL="https://github.com/$GITHUB_REPO/pull/999"
        CURRENT_PR_NUMBER="999"
        return 0
    fi

    local response
    response=$(jules_api GET "/v1alpha/$CURRENT_SESSION_NAME")

    local pr_url
    pr_url=$(echo "$response" | jq -r '.outputs[]?.pullRequest?.url // empty' | head -1)

    if [[ -n "$pr_url" ]]; then
        CURRENT_PR_URL="$pr_url"
        # Extract PR number from URL (last path segment)
        CURRENT_PR_NUMBER=$(echo "$pr_url" | grep -oE '[0-9]+$')

        log_event "pr_found" "PR found: $CURRENT_PR_URL" "$CURRENT_SESSION_ID"
        return 0
    fi

    return 1
}

wait_for_pr() {
    local start_time
    start_time=$(date +%s)
    local timeout=$EXECUTION_TIMEOUT_SECS

    log_event "session_polled" "Waiting for PR from session $CURRENT_SESSION_NAME..." "$CURRENT_SESSION_ID"

    while true; do
        if [[ "$SHUTDOWN_REQUESTED" == "true" ]]; then
            return 1
        fi

        if poll_session; then
            return 0
        fi

        local elapsed=$(( $(date +%s) - start_time ))
        if (( elapsed >= timeout )); then
            log_event "timeout" "Session timed out after ${timeout}s" "$CURRENT_SESSION_ID"
            return 1
        fi

        log_event "session_polled" "No PR yet, polling again in ${POLL_INTERVAL_SECS}s (elapsed: ${elapsed}s)" "$CURRENT_SESSION_ID"
        sleep "$POLL_INTERVAL_SECS"
    done
}

# =============================================================================
# PR Merge
# =============================================================================

MERGE_CONFLICT=false

merge_pr() {
    MERGE_CONFLICT=false

    if [[ -z "$CURRENT_PR_NUMBER" ]]; then
        log_event "error" "No PR number to merge" "$CURRENT_SESSION_ID"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_event "info" "DRY_RUN: Skipping PR merge for #$CURRENT_PR_NUMBER"
        return 0
    fi

    log_event "info" "Merging PR #$CURRENT_PR_NUMBER..." "$CURRENT_SESSION_ID"

    local payload
    payload='{"merge_method": "squash"}'

    local response
    response=$(github_api PUT "/repos/$GITHUB_OWNER/$GITHUB_REPO_NAME/pulls/$CURRENT_PR_NUMBER/merge" "$payload")

    local merged
    merged=$(echo "$response" | jq -r '.merged // false')

    if [[ "$merged" == "true" ]]; then
        local sha
        sha=$(echo "$response" | jq -r '.sha // empty')
        log_event "pr_merged" "PR #$CURRENT_PR_NUMBER merged successfully (sha: $sha)" "$CURRENT_SESSION_ID"
        return 0
    fi

    local message
    message=$(echo "$response" | jq -r '.message // "Unknown error"')

    # Check for merge conflict (HTTP 405 or 409)
    if [[ "$LAST_HTTP_CODE" == "405" || "$LAST_HTTP_CODE" == "409" ]]; then
        MERGE_CONFLICT=true
        log_event "error" "Merge conflict detected for PR #$CURRENT_PR_NUMBER: $message" "$CURRENT_SESSION_ID"
        return 2
    fi

    # Check for transient errors
    if is_transient_error "$LAST_HTTP_CODE"; then
        log_event "error" "Transient error merging PR #$CURRENT_PR_NUMBER (HTTP $LAST_HTTP_CODE): $message" "$CURRENT_SESSION_ID"
        return 1
    fi

    log_event "error" "Failed to merge PR #$CURRENT_PR_NUMBER (HTTP $LAST_HTTP_CODE): $message" "$CURRENT_SESSION_ID"
    return 1
}

# =============================================================================
# Main Loop
# =============================================================================

run_loop() {
    local iteration=0
    local consecutive_failures=0
    local max_consecutive_failures=5

    while true; do
        if [[ "$SHUTDOWN_REQUESTED" == "true" ]]; then
            break
        fi

        if [[ "$LOOP_PAUSED" == "true" ]]; then
            log_event "info" "Loop is paused. Exiting."
            break
        fi

        # Check quota before starting new session
        if ! check_quota; then
            pause_loop "Daily quota limit reached"
            break
        fi

        iteration=$((iteration + 1))
        log_event "info" "=== Loop iteration $iteration ===" ""

        # Reset session state
        CURRENT_SESSION_NAME=""
        CURRENT_SESSION_ID=""
        CURRENT_PR_URL=""
        CURRENT_PR_NUMBER=""

        # Create session with retry
        if ! retry_with_backoff "create_session"; then
            consecutive_failures=$((consecutive_failures + 1))
            if (( consecutive_failures >= max_consecutive_failures )); then
                pause_loop "Too many consecutive session creation failures ($consecutive_failures)"
                break
            fi
            log_event "error" "Failed to create session after retries, continuing to next iteration"
            continue
        fi

        # Increment quota after successful session creation
        increment_quota

        # Wait for PR (timeout is handled inside wait_for_pr)
        if ! wait_for_pr; then
            log_event "timeout" "Session timed out or failed, continuing to next iteration" "$CURRENT_SESSION_ID"
            consecutive_failures=$((consecutive_failures + 1))
            if (( consecutive_failures >= max_consecutive_failures )); then
                pause_loop "Too many consecutive failures ($consecutive_failures)"
                break
            fi
            continue
        fi

        # Merge PR with retry
        local merge_result=0
        retry_with_backoff "merge_pr" || merge_result=$?

        if (( merge_result == 2 )); then
            # Merge conflict - pause loop
            pause_loop "Merge conflict on PR #$CURRENT_PR_NUMBER ($CURRENT_PR_URL)"
            break
        elif (( merge_result != 0 )); then
            consecutive_failures=$((consecutive_failures + 1))
            if (( consecutive_failures >= max_consecutive_failures )); then
                pause_loop "Too many consecutive merge failures ($consecutive_failures)"
                break
            fi
            log_event "error" "Failed to merge PR after retries, continuing to next iteration"
            continue
        fi

        # Success - reset failure counter
        consecutive_failures=0
        log_event "info" "Iteration $iteration complete. Starting next session..."

        # Brief pause between iterations
        sleep 2
    done
}

# =============================================================================
# Main
# =============================================================================

main() {
    load_config
    init_state

    log_event "info" "jules-loop.sh starting"
    log_event "info" "Repository: $GITHUB_REPO, Branch: $TARGET_BRANCH"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_event "info" "DRY_RUN mode enabled"
    fi

    # Validate credentials before proceeding
    if ! validate_credentials; then
        log_event "error" "Credential validation failed. Exiting."
        exit 1
    fi

    # Initialize quota tracking
    init_quota

    # Discover Jules source (credentials already validated, so this uses cached data)
    discover_source

    log_event "info" "Initialization complete. Starting agent loop..."

    run_loop

    if [[ "$LOOP_PAUSED" == "true" ]]; then
        log_event "info" "Loop paused. Check state file for details."
    else
        log_event "info" "Loop terminated."
    fi
}

main "$@"
