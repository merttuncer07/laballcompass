#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  ./bootstrap.command
fi
exec .venv/bin/python -m desktop "$@"
