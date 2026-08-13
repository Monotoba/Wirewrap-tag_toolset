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
exec "$VENV_PYTHON" -m pytest "$@"
