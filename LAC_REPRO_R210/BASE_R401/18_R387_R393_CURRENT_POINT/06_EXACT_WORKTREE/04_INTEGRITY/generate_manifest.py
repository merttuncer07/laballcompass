from __future__ import annotations

import hashlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "04_INTEGRITY" / "MANIFEST_SHA256.tsv"


def included(path: Path) -> bool:
    return path != TARGET


def filesystem_path(path: Path) -> Path:
    """Use the Win32 long-path prefix so deep product evidence is not silently omitted."""
    if os.name == "nt" and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path.resolve()))
    return path


def main() -> None:
    rows = ["sha256\tbytes\tpath"]
    paths = (p for p in ROOT.rglob("*") if filesystem_path(p).is_file() and included(p))
    for path in sorted(paths, key=lambda p: p.as_posix()):
        accessible = filesystem_path(path)
        digest = hashlib.sha256(accessible.read_bytes()).hexdigest()
        rows.append(f"{digest}\t{accessible.stat().st_size}\t{path.relative_to(ROOT).as_posix()}")
    TARGET.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Wrote {TARGET.name}: {len(rows) - 1} files")


if __name__ == "__main__":
    main()
