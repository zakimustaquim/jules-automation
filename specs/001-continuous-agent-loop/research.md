# Research

## Decision: Use Jules REST API `v1alpha` sessions for agent loop
- **Decision**: Create new sessions via `POST https://jules.googleapis.com/v1alpha/sessions` using `automationMode: "AUTO_CREATE_PR"` and the repo source context.
- **Rationale**: Jules docs show sessions are the unit of work and support auto PR creation with `automationMode`. Sessions can be polled via `GET /v1alpha/sessions/{session}` to find PR output.
- **Alternatives considered**: Using Activities polling only. Rejected because session `outputs.pullRequest` is the simplest signal for a ready PR.

## Decision: Discover repo source via `GET /v1alpha/sources`
- **Decision**: On startup, list sources and pick the matching GitHub `owner/repo` for `sourceContext.source`.
- **Rationale**: Jules requires a `source` name; listing sources is the canonical way to map to the repo.
- **Alternatives considered**: Hardcode a source name. Rejected because source IDs are not obvious and may differ between users.

## Decision: Use GitHub REST API to merge PRs
- **Decision**: Merge with `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` once PR exists.
- **Rationale**: Standard GitHub REST API; returns merge status and errors for conflicts.
- **Alternatives considered**: Use GitHub CLI (`gh pr merge`). Rejected to avoid extra dependency.

## Decision: Simple local JSON state and logs
- **Decision**: Persist state in `.jules/state.json` and append events to `.jules/log.jsonl`.
- **Rationale**: Fits bash, supports restart recovery, and meets logging requirement with minimal overhead.
- **Alternatives considered**: SQLite or external DB. Rejected as unnecessary for a single-script loop.

## Decision: Bash + curl + jq
- **Decision**: Implement the loop in bash with `curl` for HTTP and `jq` for JSON parsing.
- **Rationale**: Minimal overhead, matches project constitution, and easy to run.
- **Alternatives considered**: Python or Node. Rejected for extra runtime/dependencies.

## Decision: Exponential backoff with capped retries
- **Decision**: Retry transient API errors up to 3 times with backoff (e.g., 5s, 15s, 45s) and then pause or fail per requirement.
- **Rationale**: Matches FR-007 and prevents tight retry loops.
- **Alternatives considered**: Infinite retries. Rejected due to requirement to avoid infinite loops.
