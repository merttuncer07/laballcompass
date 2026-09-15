#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  LAB_PYTHON="${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  if [[ ! -x "$LAB_PYTHON" ]]; then
    LAB_PYTHON="$(command -v python3.12 || command -v python3)"
  fi
  "$LAB_PYTHON" -c 'import sys; sys.exit("Python 3.12+ is required; Python 3.12 was tested." if sys.version_info < (3,12) else 0)'
  "$LAB_PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python lab.py doctor
