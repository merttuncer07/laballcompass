from __future__ import annotations

import json
from pathlib import Path

from second_pass import run_all


if __name__ == "__main__":
    target = Path(__file__).with_name("R210_RESULT.json")
    target.write_text(json.dumps(run_all(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(target)

