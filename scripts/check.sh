#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Local environment not found. Run ${PROJECT_ROOT}/scripts/setup.sh first." >&2
    exit 1
fi

cd -- "$PROJECT_ROOT"
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-offscreen}
"$VENV_PYTHON" -m pytest
"$VENV_PYTHON" -m compileall -q src tests
"$VENV_PYTHON" -m wirewrap_tag_designer.cli --help >/dev/null

echo "Tests, byte-compilation, and CLI smoke check passed."
