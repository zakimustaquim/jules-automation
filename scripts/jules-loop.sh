#!/usr/bin/env bash
#
# Wrapper for the Python Jules loop implementation.
#
# Usage: ./scripts/jules-loop.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_ENTRY="$SCRIPT_DIR/jules-loop.py"

if [[ ! -f "$PYTHON_ENTRY" ]]; then
    echo "Error: Python entrypoint not found at $PYTHON_ENTRY" >&2
    exit 1
fi

exec python3 "$PYTHON_ENTRY" "$@"
