#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  ./bootstrap.command
fi
.venv/bin/python lab.py doctor
open "$PWD/index.html"
