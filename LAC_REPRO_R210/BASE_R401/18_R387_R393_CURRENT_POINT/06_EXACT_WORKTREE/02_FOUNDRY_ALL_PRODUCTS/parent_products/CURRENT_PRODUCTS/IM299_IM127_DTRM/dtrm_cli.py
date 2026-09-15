from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtrm import run_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute finite-horizon decision-flip risk from a linearized system"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_file(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
