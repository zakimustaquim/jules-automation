# Implementation Plan: Jules Loop Rewrite

**Branch**: `002-python-jules-loop` | **Date**: 2026-01-24 | **Spec**: /Users/zm/Documents/GitHub/jules-interesting-app-automation/specs/002-python-jules-loop/spec.md
**Input**: Feature specification from `/specs/002-python-jules-loop/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Rewrite the Jules loop as a Python runner while preserving existing behavior, configuration surface, and log/state outputs to keep operational workflows unchanged.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Python standard library only (no third-party dependencies)  
**Storage**: Local files in `.jules/state.json` and `.jules/log.jsonl`  
**Testing**: Manual smoke runs (no automated tests planned)  
**Target Platform**: macOS/Linux shell environment  
**Project Type**: single script  
**Performance Goals**: No additional overhead beyond configured polling intervals  
**Constraints**: Behavior parity with existing loop; minimal dependencies  
**Scale/Scope**: Single operator, single repo, sequential sessions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Keep it fun and simple; avoid "production grade" infrastructure. PASS
- Favor pragmatism and minimal dependencies. PASS
- No mandatory tests or heavy process. PASS
- Avoid abstraction creep; keep a single readable script. PASS

**Post-Design Check**: PASS (single-script plan, no extra infrastructure, minimal dependencies)

## Project Structure

### Documentation (this feature)

```text
specs/002-python-jules-loop/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── jules-loop.py     # New primary entrypoint
└── jules-loop.sh     # Legacy wrapper or deprecated

.jules/
├── state.json
└── log.jsonl
```

**Structure Decision**: Single-script implementation in `scripts/jules-loop.py` to match the current operational pattern while keeping files readable and easy to run.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations.
