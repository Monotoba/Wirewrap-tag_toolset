#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN=${PYTHON:-python3}
MODE=${1:---dev}

if [[ "$MODE" != "--dev" && "$MODE" != "--runtime" ]]; then
    echo "Usage: $0 [--dev|--runtime]" >&2
    exit 2
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo "Python 3.10 or newer is required." >&2
    exit 1
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "Creating local environment at ${VENV_DIR}"
    # Reuse system Qt packages when available; pip installs any missing packages.
    "$PYTHON_BIN" -m venv --system-site-packages "$VENV_DIR"
fi

if [[ "$MODE" == "--runtime" ]]; then
    INSTALL_TARGET="$PROJECT_ROOT"
else
    INSTALL_TARGET="${PROJECT_ROOT}[test]"
fi

echo "Installing Wire-Wrap Tag Designer (${MODE#--})"
"${VENV_DIR}/bin/python" -m pip install --no-build-isolation --editable "$INSTALL_TARGET"

echo
echo "Setup complete."
echo "  Run:  ${PROJECT_ROOT}/scripts/run.sh"
echo "  Test: ${PROJECT_ROOT}/scripts/test.sh"
echo "  Venv: source ${VENV_DIR}/bin/activate"
