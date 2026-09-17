"""Reproduce local context-volume and exact-lookup work measurements; no LLM calls."""
import ast
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
from maintenance.catalog import collect
from maintenance.focus import brief, load


def measure():
    record = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("before_catalog", record / "before/maintenance/catalog.py")
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    original_parse = ast.parse
    observations = {}
    for label, call in (("before", old.collect), ("after", lambda: collect(component="P083"))):
        with patch.object(ast, "parse", wraps=original_parse) as spy:
            result = call()
        parse_count = spy.call_count
        samples = []
        for _ in range(7):
            started = time.perf_counter()
            call()
            samples.append(time.perf_counter() - started)
        observations[label] = {"ast_parse_calls": parse_count, "seconds": samples,
                               "median_seconds": statistics.median(samples),
                               "entries_collected": len(result["components"])}
    paths = ("AGENTS.md", "CONTINUE_HERE.md", "LAB_STRATEGY.md")
    current = [((BASE / path).read_text(encoding="utf-8")) for path in paths]
    focus = brief(load())
    # Direct pre-edit measurement, recorded before normalizing text snapshots.
    before_bytes, before_words = 43784, 5060
    after_bytes = sum(len(text.encode("utf-8")) for text in current) + len(focus.encode("utf-8"))
    after_words = sum(len(text.split()) for text in current) + len(focus.split())
    return {
        "scope": "Local retrieval/context engineering only; no model-token billing or product-outcome measurement",
        "startup": {"before_files": list(paths), "before_utf8_bytes": before_bytes,
                    "before_words": before_words, "after_includes_focus_brief": True,
                    "after_utf8_bytes": after_bytes, "after_words": after_words,
                    "byte_reduction_percent": 100 * (1 - after_bytes / before_bytes),
                    "word_reduction_percent": 100 * (1 - after_words / before_words),
                    "limit": "Excludes system/tool instructions, relevant source/evidence reads and conversation history. UTF-8 bytes/words are proxies, not tokens."},
        "exact_lookup_P083": observations,
        "timing_limit": "Seven warm in-process samples per method on this machine; not end-to-end Codex latency. Both methods still inspect receipt metadata and directory layout."
    }


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2))
