"""Extract the readable user/assistant message stream from the immutable Codex JSONL archive."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ORIGIN_ARCHIVE" / "CURRENT_CODEX_SESSION_RAW.jsonl"
TARGET = ROOT / "TRANSCRIPT_CURRENT_NORMALIZED.txt"


def main() -> None:
    parts: list[str] = []
    with SOURCE.open(encoding="utf-8") as stream:
        for line in stream:
            item = json.loads(line)
            payload = item.get("payload", {})
            if item.get("type") != "response_item" or payload.get("type") != "message":
                continue
            role = payload.get("role")
            if role not in {"user", "assistant"}:
                continue
            texts = []
            image_count = 0
            for block in payload.get("content", []):
                if block.get("type") in {"input_text", "output_text", "text"} and block.get("text"):
                    texts.append(block["text"])
                elif block.get("type") in {"input_image", "image"}:
                    image_count += 1
            if image_count:
                texts.append(f"[OMITTED_FROM_NORMALIZED_VIEW: {image_count} image block(s); preserved in raw JSONL]")
            if texts:
                parts.append(
                    f"\n===== {role.upper()} | {item.get('timestamp')} | ordinal {item.get('ordinal')} =====\n"
                    + "\n".join(texts)
                    + "\n"
                )
    TARGET.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {TARGET.name}: {len(parts)} messages")


if __name__ == "__main__":
    main()
