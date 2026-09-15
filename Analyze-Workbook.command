#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]] || ! .venv/bin/python -c 'import openpyxl' >/dev/null 2>&1; then
  ./bootstrap.command
fi
LAB_WORKBOOK="${1:-}"
if [[ -z "$LAB_WORKBOOK" ]]; then
  LAB_WORKBOOK="$(osascript -e 'POSIX path of (choose file with prompt "Kaynak bağlantıları incelenecek Excel dosyasını seç" of type {"xlsx", "xlsm"})')" || exit 0
fi
LAB_REPORT="$(.venv/bin/python lab.py workbench analyze "$LAB_WORKBOOK")"
open "$LAB_REPORT"
