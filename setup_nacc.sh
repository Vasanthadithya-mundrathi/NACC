#!/usr/bin/env bash
set -euo pipefail

# Simple setup script for NACC on macOS with Homebrew Python 3.12.
# It will:
# 1. Ensure python@3.12 is installed via Homebrew
# 2. Create/refresh a .venv using python3.12
# 3. Install the project in editable mode
# 4. Run tests

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "[setup_nacc] Using project root: $PROJECT_ROOT"

if ! command -v brew >/dev/null 2>&1; then
  echo "[setup_nacc] Homebrew not found. Please install Homebrew first: https://brew.sh" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON:-python3.12}"

# Prefer the Homebrew python@3.12 path when PYTHON is not explicitly provided
if [ "$PYTHON_BIN" = "python3.12" ]; then
  if brew --prefix python@3.12 >/dev/null 2>&1; then
    BREW_PY="$(brew --prefix python@3.12)/bin/python3.12"
    if [ -x "$BREW_PY" ]; then
      PYTHON_BIN="$BREW_PY"
    fi
  fi
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if [ "$PYTHON_BIN" = "python3.12" ]; then
    echo "[setup_nacc] Installing python@3.12 via Homebrew..."
    brew install python@3.12
    PYTHON_BIN="$(brew --prefix python@3.12)/bin/python3.12"
  else
    echo "[setup_nacc] Specified PYTHON=$PYTHON_BIN not found on PATH." >&2
    exit 1
  fi
fi

PYTHON_BIN="$(command -v "$PYTHON_BIN")"

if [[ "$PYTHON_BIN" == "$PROJECT_ROOT/.venv/"* ]]; then
  echo "[setup_nacc] Detected python3.12 inside the existing .venv; looking for Homebrew python@3.12..."
  if brew --prefix python@3.12 >/dev/null 2>&1; then
    ALT_PY="$(brew --prefix python@3.12)/bin/python3.12"
  else
    echo "[setup_nacc] Installing python@3.12 via Homebrew..."
    brew install python@3.12
    ALT_PY="$(brew --prefix python@3.12)/bin/python3.12"
  fi
  if [ -x "$ALT_PY" ]; then
    PYTHON_BIN="$ALT_PY"
  else
    echo "[setup_nacc] ERROR: Could not locate Homebrew python@3.12 even after installation." >&2
    echo "             Please run with PYTHON=/full/path/to/python3.12" >&2
    exit 1
  fi
fi
PY_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$PY_VERSION" != "3.12" ]; then
  echo "[setup_nacc] ERROR: Selected interpreter ($PYTHON_BIN) is Python $PY_VERSION. Please point PYTHON to a 3.12 interpreter." >&2
  exit 1
fi

echo "[setup_nacc] Using Python: $PYTHON_BIN"

# Recreate venv if missing or wrong python version
if [ -d .venv ]; then
  VENV_PY=".venv/bin/python"
  if [ ! -x "$VENV_PY" ] || ! "$VENV_PY" -V 2>&1 | grep -q "3\.12"; then
    echo "[setup_nacc] Existing .venv uses a different Python. Recreating..."
    rm -rf .venv
  fi
fi

if [ ! -d .venv ]; then
  echo "[setup_nacc] Creating virtualenv in .venv using $PYTHON_BIN..."
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest

echo "[setup_nacc] Running tests..."
python -m pytest || {
  echo "[setup_nacc] pytest failed. Check the output above for details." >&2
  exit 1
}

echo "[setup_nacc] Setup complete. To use this environment now, run:"
echo "  source .venv/bin/activate"
echo "Then you can run commands like:"
echo "  nacc-node --port 8765 --config node-config.yml"
echo "  nacc-orchestrator --config orchestrator-config.yml"
echo "  nacc-ui --config ui-config.yml"
