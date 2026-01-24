---

description: "Task list template for feature implementation"
---

# Tasks: Jules Loop Rewrite

**Input**: Design documents from `/specs/002-python-jules-loop/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in spec; no automated tests included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `scripts/`, `.jules/` at repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create Python entrypoint file at /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T002 Update /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.sh to hand off to the Python entrypoint (or mark as deprecated)
- [ ] T003 [P] Add executable permissions and shebang in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement configuration loader (.env + environment defaults) in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T005 [P] Implement state file helpers for .jules/state.json in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T006 [P] Implement logging helper for .jules/log.jsonl in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T007 [P] Implement HTTP helpers (Jules + GitHub) using urllib in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T008 Implement retry with exponential backoff in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T009 Implement shutdown handling and graceful exit in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Run Continuous Jules Loop (Priority: P1) 🎯 MVP

**Goal**: Run a full Jules loop iteration end-to-end with session creation, PR discovery, and merge.

**Independent Test**: Run the loop with valid credentials and confirm a session is created, a PR is found, and merge is attempted before the next iteration.

### Implementation for User Story 1

- [ ] T010 [US1] Implement prompt selection logic (single prompt and weighted prompts) in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T011 [US1] Implement source discovery against the Jules API in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T012 [US1] Implement session creation payload and response handling in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T013 [US1] Implement PR polling loop with timeout in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T014 [US1] Implement PR merge flow and conflict detection in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T015 [US1] Implement main run loop orchestration in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T016 [US1] Implement DRY_RUN behavior for session, polling, and merge in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py

**Checkpoint**: User Story 1 should be functional and testable independently

---

## Phase 4: User Story 2 - Configure Prompts and Limits (Priority: P2)

**Goal**: Allow operators to customize prompts, timing, retries, and quota limits safely.

**Independent Test**: Run with custom PROMPTS, polling intervals, and quota limit to verify behavior changes.

### Implementation for User Story 2

- [ ] T017 [US2] Validate PROMPTS JSON schema and probability sum in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T018 [US2] Apply polling interval, initial delay, and execution timeout settings in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T019 [US2] Implement quota tracking and enforcement using .jules/state.json in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T020 [US2] Wire retry configuration values into retry logic in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py

**Checkpoint**: User Story 2 should be functional and testable independently

---

## Phase 5: User Story 3 - Observe Status and Resume Safely (Priority: P3)

**Goal**: Provide clear logs and persistent state for inspection and recovery.

**Independent Test**: Interrupt the loop and confirm logs and state show last known session status and pause reason.

### Implementation for User Story 3

- [ ] T021 [US3] Record state transitions for current session lifecycle in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T022 [US3] Record pause reasons for merge conflicts and quota exhaustion in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py
- [ ] T023 [US3] Emit structured log entries for key events (create, poll, merge, pause, shutdown) in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py

**Checkpoint**: User Story 3 should be functional and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and alignment with docs

- [ ] T024 [P] Update /Users/zm/Documents/GitHub/jules-interesting-app-automation/README.md to reference the Python entrypoint
- [ ] T025 [P] Align /Users/zm/Documents/GitHub/jules-interesting-app-automation/example.env with any clarified defaults
- [ ] T026 [P] Validate quickstart steps against /Users/zm/Documents/GitHub/jules-interesting-app-automation/specs/002-python-jules-loop/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Core helpers before orchestration
- Configuration validation before using values in flow
- Logging/state writes after core behavior is in place

### Parallel Opportunities

- Setup task T003 can run in parallel with T001/T002 once file is created
- Foundational tasks T005, T006, T007 can run in parallel
- User stories can proceed in parallel after foundational completion

---

## Parallel Example: User Story 1

```bash
Task: "Implement source discovery against the Jules API in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py"
Task: "Implement session creation payload and response handling in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "Validate PROMPTS JSON schema and probability sum in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py"
Task: "Apply polling interval, initial delay, and execution timeout settings in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py"
```

---

## Parallel Example: User Story 3

```bash
Task: "Record state transitions for current session lifecycle in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py"
Task: "Emit structured log entries for key events (create, poll, merge, pause, shutdown) in /Users/zm/Documents/GitHub/jules-interesting-app-automation/scripts/jules-loop.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational
2. Add User Story 1 → Validate independently
3. Add User Story 2 → Validate independently
4. Add User Story 3 → Validate independently
5. Finish with Polish tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Avoid vague tasks or cross-story dependencies that break independence
