# Implementation Plan: Continuous Agent Loop

**Branch**: `001-continuous-agent-loop` | **Date**: 2026-01-16 | **Spec**: [specs/001-continuous-agent-loop/spec.md](specs/001-continuous-agent-loop/spec.md)
**Input**: Feature specification from `/specs/001-continuous-agent-loop/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a minimal, single-file bash loop that uses the Jules API to create sessions with the prompt “Do something interesting in this codebase,” waits for a PR output, auto-merges the PR via GitHub API, then immediately starts the next session. State is persisted locally in JSON so the loop can recover across restarts.

## Technical Context

**Language/Version**: Bash (POSIX-ish) on macOS 13+ / Linux  
**Primary Dependencies**: `curl`, `jq` (optional but recommended), `git` (for repo validation only)  
**Storage**: Local JSON files (state + logs)  
**Testing**: Manual run + dry-run flag (no automated tests)  
**Target Platform**: macOS/Linux terminal  
**Project Type**: Single-script automation  
**Performance Goals**: Low throughput; one session at a time  
**Constraints**: Long-running loop; handle network failures; avoid overengineering  
**Scale/Scope**: One repository, single agent loop

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ Single-file bash script (no services, no frameworks).
- ✅ Minimal dependencies (`curl` + `jq`) and local JSON files.
- ✅ No premature abstraction; straightforward procedural loop.
- ✅ Fun/learning oriented; no production-grade infra.

**Post-Phase 1 Re-check**: Still compliant. No added complexity beyond a single script and local files.

## Project Structure

### Documentation (this feature)

```text
specs/001-continuous-agent-loop/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
└── jules-loop.sh          # Single entrypoint script

.jules/
├── state.json             # Persisted state (agent/session, retries, timers)
└── log.jsonl              # Append-only event log
```

**Structure Decision**: Single-script automation with a small `.jules/` state/log directory.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations.
