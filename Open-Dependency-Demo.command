#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  ./bootstrap.command
fi
LAB_REPORT="$(.venv/bin/python lab.py workbench demo)"
open "$LAB_REPORT"
