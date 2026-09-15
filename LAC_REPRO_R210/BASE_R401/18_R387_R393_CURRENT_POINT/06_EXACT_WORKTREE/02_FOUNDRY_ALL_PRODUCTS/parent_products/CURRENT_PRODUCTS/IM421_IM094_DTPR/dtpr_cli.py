"""CSV-to-private-action command line adapter for DTPR.

The policy file is public configuration.  The input CSV remains local; the
default output contains actions and privacy-accounting metadata, never raw or
noisy scores.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from dtpr import DecisionSpec, DecisionTargetedPrivateRelease, allocate_budget


def _coerce(value: str, expected: Any) -> Any:
    if isinstance(expected, bool):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if isinstance(expected, int) and not isinstance(expected, bool):
        return int(value)
    if isinstance(expected, float):
        return float(value)
    return value


def _score_and_sensitivity(
    rows: Iterable[dict[str, str]], query: dict[str, Any], adjacency: str
) -> tuple[float, float]:
    query_type = query["type"]
    column = query["column"]
    rows = list(rows)
    if any(column not in row for row in rows):
        raise ValueError(f"CSV does not contain column: {column}")

    if query_type == "count_where":
        expected = query["equals"]
        score = sum(_coerce(row[column], expected) == expected for row in rows)
        return float(score), 1.0

    if query_type == "bounded_sum":
        lower = float(query["lower"])
        upper = float(query["upper"])
        if not (math.isfinite(lower) and math.isfinite(upper) and lower < upper):
            raise ValueError("bounded_sum requires finite lower < upper")
        values = [min(upper, max(lower, float(row[column]))) for row in rows]
        score = sum(values)
        if adjacency == "add_remove":
            sensitivity = max(abs(lower), abs(upper))
        elif adjacency == "replace_one":
            sensitivity = upper - lower
        else:
            raise ValueError("adjacency must be add_remove or replace_one")
        if sensitivity <= 0:
            raise ValueError("Derived sensitivity must be positive")
        return score, sensitivity

    raise ValueError(f"Unsupported query type: {query_type}")


class HashChainLedger:
    """Small tamper-evident ledger; it is not a remote signature service."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: list[dict[str, Any]] = []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.entries.append(json.loads(line))
            self._validate()

    @staticmethod
    def _hash(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _validate(self) -> None:
        previous = "GENESIS"
        for entry in self.entries:
            stored_hash = entry.get("entry_hash")
            payload = {key: value for key, value in entry.items() if key != "entry_hash"}
            if payload.get("previous_hash") != previous or self._hash(payload) != stored_hash:
                raise RuntimeError("Privacy ledger hash chain is invalid")
            previous = stored_hash

    @property
    def epsilon_spent(self) -> float:
        return sum(float(entry["epsilon"]) for entry in self.entries)

    def append(self, release: dict[str, Any]) -> dict[str, Any]:
        previous = self.entries[-1]["entry_hash"] if self.entries else "GENESIS"
        payload = {**release, "previous_hash": previous}
        payload["entry_hash"] = self._hash(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        self.entries.append(payload)
        return payload


def run_policy(
    policy_path: Path,
    csv_path: Path,
    ledger_path: Path,
    *,
    seed: int | None = None,
) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    total_epsilon = float(policy["total_epsilon"])
    adjacency = policy["adjacency"]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Input CSV has no data rows")

    specs: list[DecisionSpec] = []
    scores: dict[str, float] = {}
    for item in policy["decisions"]:
        score, sensitivity = _score_and_sensitivity(rows, item["query"], adjacency)
        spec = DecisionSpec(
            name=item["name"],
            thresholds=tuple(float(value) for value in item["thresholds"]),
            actions=tuple(item["actions"]),
            sensitivity=sensitivity,
            consequence_weight=float(item.get("consequence_weight", 1.0)),
        )
        specs.append(spec)
        scores[spec.name] = score

    ledger = HashChainLedger(ledger_path)
    remaining = total_epsilon - ledger.epsilon_spent
    if remaining <= 1e-12:
        raise RuntimeError("Policy lifetime privacy budget is exhausted")
    run_epsilon = min(float(policy.get("epsilon_per_run", remaining)), remaining)
    allocation = allocate_budget(specs, run_epsilon, policy.get("allocation", "decision_weighted"))
    engine = DecisionTargetedPrivateRelease(run_epsilon, seed=seed)
    releases = engine.release_plan(specs, scores, allocation)

    public_releases: list[dict[str, Any]] = []
    for release in releases:
        public = release.as_dict()
        public.pop("noisy_score", None)
        ledger.append(public)
        public_releases.append(public)

    return {
        "policy": policy.get("policy_name", policy_path.stem),
        "adjacency": adjacency,
        "input_rows_processed_locally": len(rows),
        "epsilon_spent_this_run": sum(item["epsilon"] for item in public_releases),
        "epsilon_spent_lifetime": ledger.epsilon_spent,
        "epsilon_remaining_lifetime": max(0.0, total_epsilon - ledger.epsilon_spent),
        "releases": public_releases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Release private actions from a local CSV")
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--seed", type=int, help="Reproducible test mode only; omit in production")
    args = parser.parse_args()
    print(json.dumps(run_policy(args.policy, args.input, args.ledger, seed=args.seed), indent=2))


if __name__ == "__main__":
    main()

