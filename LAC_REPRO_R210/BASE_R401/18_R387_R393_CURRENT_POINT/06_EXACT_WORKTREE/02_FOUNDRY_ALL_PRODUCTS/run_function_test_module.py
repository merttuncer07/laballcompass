from __future__ import annotations

import importlib
import inspect
import sys
import traceback


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_function_test_module.py MODULE")
    module = importlib.import_module(sys.argv[1])
    tests = [
        (name, value)
        for name, value in vars(module).items()
        if name.startswith("test_") and inspect.isfunction(value)
    ]
    failures = 0
    for name, test in sorted(tests):
        try:
            test()
        except Exception:
            failures += 1
            print(f"FAILED {module.__name__}.{name}")
            traceback.print_exc()
    print(f"Ran {len(tests)} tests")
    if failures:
        print(f"FAILED (failures={failures})")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
