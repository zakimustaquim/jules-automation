# Research

## Decision: Use Python 3.11 with standard library only
- Rationale: Keeps the rewrite lightweight, avoids adding dependencies, and matches the project constitution.
- Alternatives considered: Python 3.9/3.10 for broader compatibility; adding requests/python-dotenv for convenience.

## Decision: Use urllib for HTTP requests
- Rationale: Standard library is sufficient for the small set of API calls and avoids external packages.
- Alternatives considered: requests for simpler syntax.

## Decision: Preserve current file locations and formats
- Rationale: Operational parity requires no changes to `.jules/state.json` and `.jules/log.jsonl` paths or schema.
- Alternatives considered: New state schema or additional metadata (rejected to avoid breaking tooling).

## Decision: Keep single-script structure
- Rationale: Maintains simplicity and readability; avoids unnecessary modules or packages.
- Alternatives considered: Splitting into modules or packages (rejected as over-engineering).
