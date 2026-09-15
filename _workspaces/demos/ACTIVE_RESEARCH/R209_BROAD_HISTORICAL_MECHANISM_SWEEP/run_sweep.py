from __future__ import annotations

import json
from pathlib import Path

from surface_sweep import run_all


if __name__ == "__main__":
    output = Path(__file__).with_name("R209_RESULT.json")
    result = run_all()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(output)

