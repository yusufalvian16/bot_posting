#!/usr/bin/env bash
# ==============================================================================
# E2E Test Suite Runner for Bot-Posting Ecosystem
# ==============================================================================

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON="$(command -v python3 || command -v python)"
fi

echo "=============================================================================="
echo "  RUNNING 4-TIER END-TO-END TEST SUITE"
echo "  Project Root: $PROJECT_ROOT"
echo "  Python Interpreter: $PYTHON ($("$PYTHON" --version))"
echo "=============================================================================="

# Run test suite
"$PYTHON" -m unittest discover tests -v
EXIT_CODE=$?

echo ""
echo "=============================================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "  [PASS] ALL 4-TIER E2E TESTS PASSED SUCCESSFULLY!"
else
    echo "  [FAIL] E2E TEST SUITE REPORTED DEFECTS (Exit Code: $EXIT_CODE)"
fi
echo "=============================================================================="

exit $EXIT_CODE
