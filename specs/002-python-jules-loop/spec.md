# Feature Specification: Jules Loop Rewrite

**Feature Branch**: `002-python-jules-loop`  
**Created**: 2026-01-24  
**Status**: Draft  
**Input**: User description: "rewrite the jules loop in Python rather than Bash. Also, note that this is the second spec; please invoke the initial shell script to create the branch with the #2."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Continuous Jules Loop (Priority: P1)

As an operator, I want to start a continuous Jules session loop so that PRs are created, monitored, and merged automatically with minimal manual intervention.

**Why this priority**: This is the core value of the loop and the reason the script exists.

**Independent Test**: Can be fully tested by running the loop in a controlled environment and observing that a full iteration completes from session creation to PR merge.

**Acceptance Scenarios**:

1. **Given** valid credentials and repository settings, **When** I start the loop, **Then** a session is created, a PR is detected, and the PR is merged before the next iteration begins.
2. **Given** a merge conflict occurs, **When** the loop attempts to merge, **Then** the loop pauses and records the pause reason.

---

### User Story 2 - Configure Prompts and Limits (Priority: P2)

As an operator, I want to configure prompts, limits, and timing so that the loop behavior matches my desired cadence and scope.

**Why this priority**: Configuration flexibility is needed to safely run the loop in different environments and workloads.

**Independent Test**: Can be fully tested by setting configuration values and verifying the loop respects them in a short run.

**Acceptance Scenarios**:

1. **Given** custom prompt settings and polling intervals, **When** the loop starts, **Then** it uses the specified prompt selection and timing.

---

### User Story 3 - Observe Status and Resume Safely (Priority: P3)

As an operator, I want clear logs and state tracking so that I can understand what the loop is doing and recover after interruptions.

**Why this priority**: Observability and recoverability reduce operational risk during long-running automation.

**Independent Test**: Can be fully tested by interrupting the loop and validating that logs and state reflect the last known status.

**Acceptance Scenarios**:

1. **Given** the loop is interrupted, **When** I check recorded state and logs, **Then** I can see the last session status and reason for stopping.

---

### Edge Cases

- Missing or invalid credentials prevent startup and produce a clear error message.
- Prompt configuration is invalid (not a JSON array or probabilities do not sum to 1.0).
- Session times out without producing a PR.
- Transient API errors occur during session creation or merge.
- Daily quota limit is reached mid-run.
- Loop receives a shutdown signal during polling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a new loop runner that replaces the current script as the primary entrypoint.
- **FR-002**: System MUST support the same required configuration values and defaults as the existing loop.
- **FR-003**: System MUST support optional prompt selection, timing, retry, quota, and dry-run settings consistent with current behavior.
- **FR-004**: System MUST record loop events to a persistent log with timestamps and event types.
- **FR-005**: System MUST persist loop state so that the last known session and pause reason can be inspected after interruption.
- **FR-006**: System MUST pause the loop on merge conflicts and record the conflict context.
- **FR-007**: System MUST apply retry with backoff for transient failures during session creation and merge.
- **FR-008**: System MUST stop cleanly on shutdown signals without corrupting state.
- **FR-009**: System MUST preserve current loop behavior and outputs so existing operational workflows remain unchanged.

### Functional Requirement Acceptance Criteria

- **AC-FR-001**: Starting the loop with the documented command launches the new runner and begins initialization messages.
- **AC-FR-002**: Running the loop with only required configuration succeeds with documented defaults applied.
- **AC-FR-003**: When optional settings are provided, the loop behavior reflects those values in a short controlled run.
- **AC-FR-004**: Each major loop event writes a timestamped entry to the log file.
- **AC-FR-005**: After interruption, the state file contains the last known session identifiers and pause reason when applicable.
- **AC-FR-006**: A merge conflict results in a paused loop state and a recorded conflict reason.
- **AC-FR-007**: Transient failures trigger at least one retry with increasing delay before final failure.
- **AC-FR-008**: On shutdown signal, the loop exits without corrupting the state file.
- **AC-FR-009**: Outputs and user-visible behavior match the existing loop for equivalent inputs.

### Key Entities *(include if feature involves data)*

- **Loop Configuration**: Required and optional settings that control credentials, prompts, timing, limits, and dry-run mode.
- **Loop State**: Last known session identifiers, status, retry counts, and pause reason.
- **Log Entry**: Timestamped event record with event type, message, and optional details.
- **Session**: A single Jules session lifecycle including creation, PR discovery, and merge outcome.

## Assumptions

- The existing loop behavior is the source of truth for functional parity.
- Operators will continue to supply configuration values through the same environment variable names and .env file convention.
- The state and log files remain in the same locations and retain current formats.

## Dependencies

- Access to the Jules service for session creation and status updates.
- Access to the repository hosting service for pull request discovery and merging.

## Out of Scope

- Changes to the Jules service behavior or external integrations.
- New automation features beyond parity with the current loop.
- New user interfaces or dashboards.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can complete at least one full loop iteration (session create to merge) using the new implementation without manual intervention.
- **SC-002**: 100% of configuration options documented for the loop are accepted and honored by the new implementation.
- **SC-003**: When a merge conflict is encountered, the loop pauses and records the pause reason within 5 seconds of detection.
- **SC-004**: For at least 10 consecutive iterations in a controlled run, the loop completes without unexpected termination.
