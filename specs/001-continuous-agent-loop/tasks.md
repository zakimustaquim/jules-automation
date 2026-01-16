---

description: "Task list for Continuous Agent Loop"
---

# Tasks: Continuous Agent Loop

**Input**: Design documents from `/specs/001-continuous-agent-loop/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in spec; omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create scripts/jules-loop.sh with a minimal bash skeleton and executable bit
- [x] T002 Add .jules/ to .gitignore (create .gitignore if missing)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T003 Implement config loading (.env + env vars) with defaults in scripts/jules-loop.sh
- [x] T004 Implement JSON log writer to .jules/log.jsonl in scripts/jules-loop.sh
- [x] T005 Implement state read/write helpers for .jules/state.json in scripts/jules-loop.sh
- [x] T006 Implement HTTP helper (curl + jq) with Jules/GitHub headers in scripts/jules-loop.sh
- [x] T007 Implement graceful shutdown trap and state flush in scripts/jules-loop.sh
- [x] T008 Implement Jules source discovery (GET /v1alpha/sources) in scripts/jules-loop.sh

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Autonomous Agent Generation Loop (Priority: P1) 🎯 MVP

**Goal**: Continuously create a Jules session, wait for a PR, merge it, then start the next session.

**Independent Test**: Start the script with valid credentials and confirm a session is created, a PR appears, and the PR is merged, after which a new session is created.

### Implementation for User Story 1

- [x] T009 [US1] Create session (POST /v1alpha/sessions) with prompt in scripts/jules-loop.sh
- [x] T010 [US1] Poll session (GET /v1alpha/sessions/{id}) and extract PR URL/number in scripts/jules-loop.sh
- [x] T011 [US1] Merge PR via GitHub API (PUT /repos/{owner}/{repo}/pulls/{number}/merge) in scripts/jules-loop.sh
- [x] T012 [US1] Implement main loop sequence create → poll → merge → repeat in scripts/jules-loop.sh

**Checkpoint**: User Story 1 is functional and can run the basic loop end-to-end

---

## Phase 4: User Story 2 - Error Handling and Recovery (Priority: P2)

**Goal**: Handle transient errors, auth failures, conflicts, and timeouts without crashing.

**Independent Test**: Simulate API failures and verify the script logs, waits/retries, and either resumes or pauses safely without infinite loops.

### Implementation for User Story 2

- [x] T013 [US2] Add retry with exponential backoff for transient API errors in scripts/jules-loop.sh
- [x] T014 [US2] Validate Jules + GitHub credentials on startup in scripts/jules-loop.sh
- [x] T015 [US2] Detect merge conflicts and pause loop with PR ID logged in scripts/jules-loop.sh
- [x] T016 [US2] Implement execution timeout handling and skip to next session in scripts/jules-loop.sh
- [x] T017 [US2] Implement optional quota tracking/pause when QUOTA_DAILY_LIMIT is exceeded in scripts/jules-loop.sh
- [x] T018 [US2] Add fatal-error pause/alert behavior with clear logging in scripts/jules-loop.sh

**Checkpoint**: User Story 2 error handling behaviors operate without breaking the US1 loop

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Light documentation and alignment

- [x] T019 Update README.md with usage, env vars, and expected outputs
- [x] T020 Validate and align specs/001-continuous-agent-loop/quickstart.md with script behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **US1 (Phase 3)** → **US2 (Phase 4)** → **Polish (Phase 5)**

### User Story Dependencies

- **US1** depends on Foundational completion
- **US2** depends on US1 completion (extends behavior in the same script)

### Parallel Opportunities

Because nearly all work is in a single file (scripts/jules-loop.sh), tasks are mostly sequential. Parallel work is limited to documentation-only tasks.

---

## Parallel Execution Examples

### User Story 1

No safe parallel tasks: T009–T012 all modify scripts/jules-loop.sh and should be done sequentially.

### User Story 2

No safe parallel tasks: T013–T018 all modify scripts/jules-loop.sh and should be done sequentially.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the loop once end-to-end

### Incremental Delivery

1. Deliver US1 basic loop
2. Add US2 error handling and recovery
3. Finish with documentation polish
