#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]] || ! .venv/bin/python -c 'import openpyxl' >/dev/null 2>&1; then
  ./bootstrap.command
fi
LAB_FOLDER="${1:-}"
if [[ -z "$LAB_FOLDER" ]]; then
  LAB_FOLDER="$(osascript -e 'POSIX path of (choose folder with prompt "Birlikte incelenecek Excel dosyalarının klasörünü seç")')" || exit 0
fi
LAB_REPORT="$(.venv/bin/python lab.py workbench analyze "$LAB_FOLDER")"
open "$LAB_REPORT"
