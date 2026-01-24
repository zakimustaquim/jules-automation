#!/usr/bin/env python3
"""
Continuous Jules agent loop (Python rewrite).

Uses only the Python 3.11 standard library.
"""

from __future__ import annotations

import json
import os
import random
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Tuple


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
JULES_DIR = REPO_ROOT / ".jules"
STATE_FILE = JULES_DIR / "state.json"
LOG_FILE = JULES_DIR / "log.jsonl"

JULES_API_BASE = "https://jules.googleapis.com"
GITHUB_API_BASE = "https://api.github.com"

SHUTDOWN_REQUESTED = False
LOOP_PAUSED = False


@dataclass
class LoopConfig:
    jules_api_key: str
    github_token: str
    github_repo: str
    github_owner: str
    github_repo_name: str
    target_branch: str
    prompt: str
    prompts: Optional[list[dict[str, Any]]]
    execution_timeout_secs: int
    retry_max: int
    retry_base_secs: int
    poll_interval_secs: int
    poll_initial_delay_secs: int
    quota_daily_limit: Optional[int]
    dry_run: bool


@dataclass
class HttpResponse:
    status: int
    body: str


def utc_iso_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event: str, message: str, agent_id: str = "", details: Any = None) -> None:
    entry: dict[str, Any] = {
        "timestamp": utc_iso_timestamp(),
        "event": event,
        "message": message,
    }
    if agent_id:
        entry["agent_id"] = agent_id
    if details is not None:
        entry["details"] = details

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")

    local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{local_ts}] [{event}] {message}")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith("'") and value.endswith("'")) or (
            value.startswith('"') and value.endswith('"')
        ):
            value = value[1:-1]
        os.environ[key] = value


def parse_int_env(name: str, default: Optional[int], minimum: int = 1) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        if default is None:
            raise ValueError(f"{name} is required")
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() == "true"


def load_config() -> LoopConfig:
    load_env_file(REPO_ROOT / ".env")

    jules_api_key = os.environ.get("JULES_API_KEY", "").strip()
    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    github_repo = os.environ.get("GITHUB_REPO", "").strip()

    target_branch = os.environ.get("TARGET_BRANCH", "main").strip() or "main"
    prompt = os.environ.get("PROMPT", "Do something interesting in this codebase").strip()
    prompts_raw = os.environ.get("PROMPTS", "").strip()

    execution_timeout_secs = parse_int_env("EXECUTION_TIMEOUT_SECS", 1800, minimum=1)
    retry_max = parse_int_env("RETRY_MAX", 3, minimum=1)
    retry_base_secs = parse_int_env("RETRY_BASE_SECS", 5, minimum=1)
    poll_interval_secs = parse_int_env("POLL_INTERVAL_SECS", 15, minimum=1)
    poll_initial_delay_secs = parse_int_env("POLL_INITIAL_DELAY_SECS", 0, minimum=0)

    quota_daily_limit_raw = os.environ.get("QUOTA_DAILY_LIMIT", "").strip()
    quota_daily_limit = None
    if quota_daily_limit_raw:
        quota_daily_limit = parse_int_env("QUOTA_DAILY_LIMIT", None, minimum=1)

    dry_run = parse_bool_env("DRY_RUN", default=False)

    if github_repo:
        owner, _, repo_name = github_repo.partition("/")
    else:
        owner, repo_name = "", ""

    prompts = None
    if prompts_raw:
        try:
            prompts_value = json.loads(prompts_raw)
        except json.JSONDecodeError as exc:
            raise ValueError("PROMPTS must be valid JSON") from exc
        if not isinstance(prompts_value, list):
            raise ValueError("PROMPTS must be a JSON array")
        prompts = prompts_value

    JULES_DIR.mkdir(parents=True, exist_ok=True)

    return LoopConfig(
        jules_api_key=jules_api_key,
        github_token=github_token,
        github_repo=github_repo,
        github_owner=owner,
        github_repo_name=repo_name,
        target_branch=target_branch,
        prompt=prompt,
        prompts=prompts,
        execution_timeout_secs=execution_timeout_secs,
        retry_max=retry_max,
        retry_base_secs=retry_base_secs,
        poll_interval_secs=poll_interval_secs,
        poll_initial_delay_secs=poll_initial_delay_secs,
        quota_daily_limit=quota_daily_limit,
        dry_run=dry_run,
    )


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state: dict[str, Any]) -> None:
    temp_path = STATE_FILE.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, STATE_FILE)


def flush_state() -> None:
    if not STATE_FILE.exists():
        return
    with STATE_FILE.open("r+", encoding="utf-8") as handle:
        handle.flush()
        os.fsync(handle.fileno())


def update_state_value(state: dict[str, Any], key: str, value: Any) -> None:
    state[key] = value
    save_state(state)


def update_current_agent(state: dict[str, Any], updates: dict[str, Any]) -> None:
    current = state.get("current_agent") or {}
    current.update(updates)
    state["current_agent"] = current
    save_state(state)


def parse_json_details(body: str) -> Any:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body}


def http_request(method: str, url: str, headers: dict[str, str], data: Optional[str] = None) -> HttpResponse:
    payload = data.encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return HttpResponse(status=response.status, body=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return HttpResponse(status=exc.code, body=body)
    except urllib.error.URLError as exc:
        return HttpResponse(status=0, body=str(exc))


def is_transient_error(code: int) -> bool:
    return code in {0, 429, 500, 502, 503, 504}


def is_auth_error(code: int) -> bool:
    return code in {401, 403}


def jules_api(config: LoopConfig, method: str, endpoint: str, data: Optional[str] = None) -> HttpResponse:
    headers = {
        "x-goog-api-key": config.jules_api_key,
        "Content-Type": "application/json",
    }
    return http_request(method, f"{JULES_API_BASE}{endpoint}", headers, data)


def github_api(config: LoopConfig, method: str, endpoint: str, data: Optional[str] = None) -> HttpResponse:
    headers = {
        "Authorization": f"Bearer {config.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return http_request(method, f"{GITHUB_API_BASE}{endpoint}", headers, data)


def shutdown_handler(signum: int, _frame: Any) -> None:
    global SHUTDOWN_REQUESTED
    if SHUTDOWN_REQUESTED:
        return
    SHUTDOWN_REQUESTED = True
    log_event("shutdown", f"Graceful shutdown initiated (signal {signum})")
    flush_state()


def validate_credentials(config: LoopConfig) -> bool:
    errors = 0
    if not config.jules_api_key:
        log_event("error", "JULES_API_KEY is not set")
        errors += 1
    if not config.github_token:
        log_event("error", "GITHUB_TOKEN is not set")
        errors += 1
    if not config.github_repo:
        log_event("error", "GITHUB_REPO is not set")
        errors += 1
    if errors:
        return False

    log_event("info", "Validating Jules API credentials...")
    response = jules_api(config, "GET", "/v1alpha/sessions")
    if is_auth_error(response.status):
        log_event("error", f"Jules API authentication failed (HTTP {response.status})")
        return False
    if response.status != 200:
        log_event("error", f"Jules API validation failed (HTTP {response.status})")
        return False
    log_event("info", "Jules API credentials validated")

    log_event("info", "Validating GitHub credentials...")
    response = github_api(
        config, "GET", f"/repos/{config.github_owner}/{config.github_repo_name}"
    )
    if is_auth_error(response.status):
        log_event("error", f"GitHub authentication failed (HTTP {response.status})")
        return False
    if response.status != 200:
        log_event(
            "error",
            f"GitHub validation failed - repo not found or inaccessible (HTTP {response.status})",
        )
        return False
    log_event("info", f"GitHub credentials validated for {config.github_repo}")
    return True


def validate_prompts(config: LoopConfig) -> bool:
    if not config.prompts:
        log_event("info", f"Using single prompt: {config.prompt}")
        return True

    if not isinstance(config.prompts, list) or len(config.prompts) == 0:
        log_event("error", "PROMPTS array is empty")
        return False

    for prompt in config.prompts:
        if not isinstance(prompt, dict) or "text" not in prompt or "probability" not in prompt:
            log_event("error", "Each prompt must have 'text' and 'probability' fields")
            return False
        if not isinstance(prompt["probability"], (int, float)):
            log_event("error", "Prompt probabilities must be numeric")
            return False

    prob_sum = sum(float(prompt["probability"]) for prompt in config.prompts)
    if not 0.99 <= prob_sum <= 1.01:
        log_event("error", f"Probabilities must sum to 1.0 (current sum: {prob_sum})")
        return False

    log_event("info", f"Using {len(config.prompts)} prompts with probability-based selection")
    return True


def choose_prompt(config: LoopConfig) -> str:
    if not config.prompts:
        return config.prompt

    random_value = random.random()
    cumulative = 0.0
    for prompt in config.prompts:
        cumulative += float(prompt["probability"])
        if random_value <= cumulative:
            selected = str(prompt["text"])
            log_event("info", f"Selected prompt (p={random_value:.6f}): {selected[:50]}...")
            return selected

    selected = str(config.prompts[0]["text"])
    log_event("warning", "Prompt selection failed, using first prompt as fallback")
    return selected


def pause_loop(state: dict[str, Any], reason: str, session_id: str = "") -> None:
    global LOOP_PAUSED
    LOOP_PAUSED = True
    log_event("paused", f"Loop paused: {reason}", session_id)
    update_state_value(state, "paused", True)
    update_state_value(state, "pause_reason", reason)
    if state.get("current_agent"):
        update_current_agent(state, {"status": "paused"})


def init_quota(state: dict[str, Any], config: LoopConfig) -> Tuple[int, Optional[str]]:
    if config.quota_daily_limit is None:
        return 0, None

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stored_date = state.get("quota_reset_date")

    if stored_date != today:
        state["quota_used"] = 0
        state["quota_reset_date"] = today
        save_state(state)
        log_event("info", f"Quota reset for {today} (limit: {config.quota_daily_limit})")
        return 0, today

    quota_used = int(state.get("quota_used") or 0)
    log_event("info", f"Quota: {quota_used} / {config.quota_daily_limit} used")
    return quota_used, today


def check_quota(quota_used: int, config: LoopConfig) -> bool:
    if config.quota_daily_limit is None:
        return True
    if quota_used >= config.quota_daily_limit:
        log_event("quota_exhausted", f"Daily quota limit ({config.quota_daily_limit}) reached")
        return False
    return True


def increment_quota(state: dict[str, Any], quota_used: int, config: LoopConfig) -> int:
    if config.quota_daily_limit is None:
        return quota_used
    quota_used += 1
    state["quota_used"] = quota_used
    save_state(state)
    log_event("info", f"Quota: {quota_used} / {config.quota_daily_limit} used")
    return quota_used


def discover_source(config: LoopConfig) -> Optional[str]:
    log_event("info", f"Discovering Jules source for {config.github_repo}...")
    response = jules_api(config, "GET", "/v1alpha/sources")
    if response.status != 200:
        log_event("error", f"Failed to list Jules sources (HTTP {response.status})")
        return None
    try:
        payload = json.loads(response.body or "{}")
    except json.JSONDecodeError:
        log_event("error", "Failed to parse Jules source response")
        return None

    for source in payload.get("sources", []):
        repo = source.get("githubRepo", {})
        if repo.get("owner") == config.github_owner and repo.get("repo") == config.github_repo_name:
            name = source.get("name")
            if name:
                log_event("info", f"Found Jules source: {name}")
                return name

    log_event("error", f"No Jules source found for {config.github_repo}")
    return None


def create_session(
    config: LoopConfig,
    state: dict[str, Any],
    source_name: str,
) -> Tuple[bool, bool, Optional[Tuple[str, str, str]]]:
    prompt = choose_prompt(config)
    log_event("agent_created", "Creating new Jules session...")

    if config.dry_run:
        log_event("info", "DRY_RUN: Skipping session creation")
        session_name = f"sessions/dry-run-{int(time.time())}"
        session_id = f"dry-run-{int(time.time())}"
        update_current_agent(
            state,
            {
                "id": session_id,
                "name": session_name,
                "prompt": prompt,
                "status": "running",
                "start_time": utc_iso_timestamp(),
                "retry_count": 0,
            },
        )
        return True, False, (session_name, session_id, prompt)

    payload = {
        "prompt": prompt,
        "title": f"Jules auto-session {utc_iso_timestamp()}",
        "automationMode": "AUTO_CREATE_PR",
        "sourceContext": {
            "source": source_name,
            "githubRepoContext": {"startingBranch": config.target_branch},
        },
    }
    response = jules_api(config, "POST", "/v1alpha/sessions", json.dumps(payload))

    if response.status != 200:
        log_event(
            "error",
            f"Failed to create session (HTTP {response.status})",
            details=parse_json_details(response.body),
        )
        return False, is_transient_error(response.status), None

    try:
        payload = json.loads(response.body or "{}")
    except json.JSONDecodeError:
        log_event(
            "error",
            "Failed to parse session creation response",
            details=parse_json_details(response.body),
        )
        return False, False, None

    session_name = payload.get("name")
    session_id = payload.get("id")
    if not session_name:
        log_event("error", "Failed to create session", details=payload)
        return False, False, None

    log_event("agent_created", f"Session created: {session_name}", session_id)
    update_current_agent(
        state,
        {
            "id": session_id,
            "name": session_name,
            "prompt": prompt,
            "status": "running",
            "start_time": utc_iso_timestamp(),
            "retry_count": 0,
        },
    )
    return True, False, (session_name, session_id, prompt)


def poll_session(config: LoopConfig, session_name: str, session_id: str) -> Tuple[bool, Optional[str]]:
    if config.dry_run:
        log_event("info", "DRY_RUN: Simulating PR found", session_id)
        return True, f"https://github.com/{config.github_repo}/pull/999"

    response = jules_api(config, "GET", f"/v1alpha/{session_name}")
    if response.status != 200:
        log_event("error", f"Failed to poll session (HTTP {response.status})", session_id)
        return False, None
    try:
        payload = json.loads(response.body or "{}")
    except json.JSONDecodeError:
        log_event("error", "Failed to parse session poll response", session_id)
        return False, None

    outputs = payload.get("outputs", []) or []
    for output in outputs:
        pr_url = output.get("pullRequest", {}).get("url")
        if pr_url:
            log_event("pr_found", f"PR found: {pr_url}", session_id)
            return True, pr_url

    return False, None


def wait_for_pr(
    config: LoopConfig,
    state: dict[str, Any],
    session_name: str,
    session_id: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    start_time = time.time()

    if config.poll_initial_delay_secs > 0:
        log_event(
            "info",
            f"Waiting {config.poll_initial_delay_secs}s before initial polling...",
            session_id,
        )
        time.sleep(config.poll_initial_delay_secs)

    log_event("session_polled", f"Waiting for PR from session {session_name}...", session_id)

    while True:
        if SHUTDOWN_REQUESTED:
            return False, None, None

        found, pr_url = poll_session(config, session_name, session_id)
        if found and pr_url:
            update_current_agent(state, {"status": "pr_found"})
            pr_number = pr_url.rstrip("/").split("/")[-1]
            return True, pr_url, pr_number

        elapsed = int(time.time() - start_time)
        if elapsed >= config.execution_timeout_secs:
            log_event("timeout", f"Session timed out after {config.execution_timeout_secs}s", session_id)
            update_current_agent(state, {"status": "timeout"})
            return False, None, None

        log_event(
            "session_polled",
            f"No PR yet, polling again in {config.poll_interval_secs}s (elapsed: {elapsed}s)",
            session_id,
        )
        time.sleep(config.poll_interval_secs)


def merge_pr(
    config: LoopConfig,
    session_id: str,
    pr_number: str,
) -> Tuple[bool, bool, str]:
    if config.dry_run:
        log_event("info", f"DRY_RUN: Skipping PR merge for #{pr_number}", session_id)
        return True, False, "merged"

    log_event("info", f"Merging PR #{pr_number}...", session_id)

    payload = json.dumps({"merge_method": "squash"})
    response = github_api(
        config,
        "PUT",
        f"/repos/{config.github_owner}/{config.github_repo_name}/pulls/{pr_number}/merge",
        payload,
    )

    try:
        body = json.loads(response.body or "{}")
    except json.JSONDecodeError:
        body = {}

    if response.status == 200 and body.get("merged") is True:
        sha = body.get("sha", "")
        log_event("pr_merged", f"PR #{pr_number} merged successfully (sha: {sha})", session_id)
        return True, False, "merged"

    message = body.get("message", "Unknown error")
    if response.status in {405, 409}:
        log_event(
            "error",
            f"Merge conflict detected for PR #{pr_number}: {message}",
            session_id,
        )
        return False, False, "conflict"

    if is_transient_error(response.status):
        log_event(
            "error",
            f"Transient error merging PR #{pr_number} (HTTP {response.status}): {message}",
            session_id,
        )
        return False, True, "retryable"

    log_event(
        "error",
        f"Failed to merge PR #{pr_number} (HTTP {response.status}): {message}",
        session_id,
    )
    return False, False, "failed"


def retry_with_backoff(
    operation: Callable[[], Tuple[bool, bool, str]],
    max_retries: int,
    base_delay: int,
) -> Tuple[bool, str]:
    attempt = 0
    while True:
        success, retryable, result = operation()
        if success:
            return True, result
        attempt += 1
        if not retryable or attempt >= max_retries:
            return False, result
        delay = base_delay * (3 ** (attempt - 1))
        log_event("error", f"Attempt {attempt} failed, retrying in {delay}s...")
        time.sleep(delay)


def run_loop(config: LoopConfig) -> None:
    state = load_state()
    if not state:
        save_state(state)

    quota_used, _ = init_quota(state, config)

    if not validate_prompts(config):
        log_event("error", "Prompt initialization failed. Exiting.")
        sys.exit(1)

    source_name = discover_source(config)
    if not source_name:
        log_event("error", "Source discovery failed. Exiting.")
        sys.exit(1)

    log_event("info", "Initialization complete. Starting agent loop...")

    iteration = 0
    consecutive_failures = 0
    max_consecutive_failures = 5

    while True:
        if SHUTDOWN_REQUESTED:
            break
        if LOOP_PAUSED:
            log_event("info", "Loop is paused. Exiting.")
            break

        if not check_quota(quota_used, config):
            pause_loop(state, "Daily quota limit reached")
            break

        iteration += 1
        log_event("info", f"=== Loop iteration {iteration} ===")

        def create_op() -> Tuple[bool, bool, str]:
            ok, retryable, result = create_session(config, state, source_name)
            return ok, retryable, "created" if ok else "failed"

        created, _ = retry_with_backoff(create_op, config.retry_max, config.retry_base_secs)
        if not created:
            consecutive_failures += 1
            update_current_agent(state, {"status": "failed"})
            if consecutive_failures >= max_consecutive_failures:
                pause_loop(state, f"Too many consecutive session creation failures ({consecutive_failures})")
                break
            log_event("error", "Failed to create session after retries, continuing to next iteration")
            continue

        quota_used = increment_quota(state, quota_used, config)

        current_agent = state.get("current_agent") or {}
        session_name = current_agent.get("name") or ""
        session_id = current_agent.get("id") or ""
        if not session_name or not session_id:
            log_event("error", "Session state missing identifiers, pausing loop")
            pause_loop(state, "Missing session identifiers")
            break

        found, pr_url, pr_number = wait_for_pr(config, state, session_name, session_id)
        if not found or not pr_number:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                pause_loop(state, f"Too many consecutive failures ({consecutive_failures})", session_id)
                break
            log_event("timeout", "Session timed out or failed, continuing to next iteration", session_id)
            continue

        def merge_op() -> Tuple[bool, bool, str]:
            return merge_pr(config, session_id, pr_number)

        merged, merge_result = retry_with_backoff(
            merge_op, config.retry_max, config.retry_base_secs
        )

        if not merged:
            consecutive_failures += 1
            if merge_result == "conflict":
                pause_loop(state, f"Merge conflict on PR #{pr_number} ({pr_url})", session_id)
                break
            if consecutive_failures >= max_consecutive_failures:
                pause_loop(state, f"Too many consecutive merge failures ({consecutive_failures})", session_id)
                break
            log_event("error", "Failed to merge PR after retries, continuing to next iteration", session_id)
            continue

        update_current_agent(state, {"status": "merged"})
        consecutive_failures = 0
        log_event("info", f"Iteration {iteration} complete. Starting next session...")
        time.sleep(2)

    if LOOP_PAUSED:
        log_event("info", "Loop paused. Check state file for details.")
    else:
        log_event("info", "Loop terminated.")


def main() -> None:
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        config = load_config()
    except ValueError as exc:
        log_event("error", str(exc))
        sys.exit(1)

    log_event("info", "jules-loop.py starting")
    log_event("info", f"Repository: {config.github_repo}, Branch: {config.target_branch}")

    if config.dry_run:
        log_event("info", "DRY_RUN mode enabled")

    if not validate_credentials(config):
        log_event("error", "Credential validation failed. Exiting.")
        sys.exit(1)

    run_loop(config)


if __name__ == "__main__":
    main()
