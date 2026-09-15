from __future__ import annotations

import json
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
R199 = HERE.parent / "R199_THEORY_BOTTLENECK_PORTFOLIO_WAVE3"
sys.path.insert(0, str(R199))

from wave3 import MooreAutomaton, random_observable_automaton  # noqa: E402


@dataclass
class XorDecision:
    distinguishable: bool
    word: tuple[int, ...] | None
    span_dimension: int
    explored_images: int


class XorDirectSumCompiler:
    """GF(2) direct-sum representation of a synchronized XOR-observed product."""

    def __init__(self, automata: list[MooreAutomaton]):
        if not automata:
            raise ValueError("at least one component is required")
        if len({automaton.alphabet for automaton in automata}) != 1:
            raise ValueError("components must share an alphabet")
        self.automata = automata
        self.alphabet = automata[0].alphabet
        self.offsets = []
        offset = 0
        for automaton in automata:
            self.offsets.append(offset)
            offset += automaton.states
        self.dimension = offset
        self.output_mask = 0
        self.symbol_images = [[0] * self.dimension for _ in range(self.alphabet)]
        for automaton, offset in zip(automata, self.offsets):
            for state in range(automaton.states):
                global_state = offset + state
                if automaton.output[state]:
                    self.output_mask |= 1 << global_state
                for symbol in range(self.alphabet):
                    destination = offset + int(automaton.transition[state, symbol])
                    self.symbol_images[symbol][global_state] = 1 << destination

    def difference_vector(self, left, right):
        vector = 0
        for automaton, offset, a, b in zip(self.automata, self.offsets, left, right):
            if not (0 <= a < automaton.states and 0 <= b < automaton.states):
                raise ValueError("invalid component state")
            vector ^= 1 << (offset + a)
            vector ^= 1 << (offset + b)
        return vector

    def apply_symbol(self, vector: int, symbol: int):
        result = 0
        active = vector
        images = self.symbol_images[symbol]
        while active:
            bit = active & -active
            index = bit.bit_length() - 1
            result ^= images[index]
            active ^= bit
        return result

    def observed_difference(self, vector: int):
        return (vector & self.output_mask).bit_count() & 1

    def decide(self, left, right) -> XorDecision:
        initial = self.difference_vector(left, right)
        if self.observed_difference(initial):
            return XorDecision(True, (), 1, 0)
        if initial == 0:
            return XorDecision(False, None, 0, 0)

        pivots: dict[int, int] = {}

        def insert(vector: int):
            reduced = vector
            while reduced:
                pivot = reduced.bit_length() - 1
                if pivot in pivots:
                    reduced ^= pivots[pivot]
                else:
                    pivots[pivot] = reduced
                    return True
            return False

        insert(initial)
        queue = deque([(initial, ())])
        explored = 0
        while queue:
            actual, word = queue.popleft()
            for symbol in range(self.alphabet):
                candidate = self.apply_symbol(actual, symbol)
                candidate_word = word + (symbol,)
                explored += 1
                if self.observed_difference(candidate):
                    return XorDecision(True, candidate_word, len(pivots), explored)
                if insert(candidate):
                    queue.append((candidate, candidate_word))
        return XorDecision(False, None, len(pivots), explored)

    def run_xor_output(self, global_state, word):
        output = 0
        for automaton, state in zip(self.automata, global_state):
            output ^= automaton.run_output(state, word)
        return output


def full_product_xor_decision(automata, left, right, state_cap=2_000_000):
    queue = deque([(tuple(left), tuple(right), ())])
    seen = {(tuple(left), tuple(right))}
    while queue:
        a, b, word = queue.popleft()
        out_a = 0
        out_b = 0
        for automaton, sa, sb in zip(automata, a, b):
            out_a ^= int(automaton.output[sa])
            out_b ^= int(automaton.output[sb])
        if out_a != out_b:
            return True, word, len(seen), False
        for symbol in range(automata[0].alphabet):
            na = tuple(int(auto.transition[state, symbol]) for auto, state in zip(automata, a))
            nb = tuple(int(auto.transition[state, symbol]) for auto, state in zip(automata, b))
            pair = (na, nb)
            if pair not in seen:
                seen.add(pair)
                if len(seen) > state_cap:
                    return None, None, len(seen), True
                queue.append((na, nb, word + (symbol,)))
    return False, None, len(seen), False


def small_exact_trial(seed: int, components: int):
    rng = np.random.default_rng(510000 + seed + 29 * components)
    automata = [random_observable_automaton(rng, states=5) for _ in range(components)]
    compiler = XorDirectSumCompiler(automata)
    agreements = 0
    witness_valid = 0
    equivalent_cases = 0
    max_span = 0
    full_seen = []
    for _ in range(180):
        left = tuple(int(rng.integers(a.states)) for a in automata)
        right = tuple(int(rng.integers(a.states)) for a in automata)
        direct = compiler.decide(left, right)
        full, full_word, seen, capped = full_product_xor_decision(automata, left, right)
        if capped:
            raise RuntimeError("small oracle unexpectedly capped")
        agreements += direct.distinguishable == full
        equivalent_cases += not direct.distinguishable
        max_span = max(max_span, direct.span_dimension)
        full_seen.append(seen)
        if direct.word is not None:
            witness_valid += (
                compiler.run_xor_output(left, direct.word)
                != compiler.run_xor_output(right, direct.word)
            )

    # Exact cancellation stress: identical components and swapped local states.
    duplicated = [automata[0], automata[0]]
    duplicate_compiler = XorDirectSumCompiler(duplicated)
    swapped = duplicate_compiler.decide((0, 1), (1, 0))
    return {
        "seed": seed,
        "components": components,
        "queries": 180,
        "full_product_agreements": agreements,
        "valid_witnesses": witness_valid,
        "equivalent_cases": equivalent_cases,
        "maximum_span_dimension": max_span,
        "direct_sum_dimension": compiler.dimension,
        "mean_full_pair_states_seen": float(np.mean(full_seen)),
        "swapped_duplicate_proved_equivalent": not swapped.distinguishable,
    }


def scale_trial(seed: int, components: int = 64, states: int = 8):
    rng = np.random.default_rng(610000 + seed)
    automata = [random_observable_automaton(rng, states=states) for _ in range(components)]
    compiler = XorDirectSumCompiler(automata)
    decisions = []
    elapsed = []
    for _ in range(40):
        while True:
            left = tuple(int(rng.integers(states)) for _ in automata)
            right = tuple(int(rng.integers(states)) for _ in automata)
            if compiler.run_xor_output(left, ()) == compiler.run_xor_output(right, ()):
                break
        started = time.perf_counter()
        decision = compiler.decide(left, right)
        elapsed.append(time.perf_counter() - started)
        decisions.append(decision)
        if decision.word is not None and (
            compiler.run_xor_output(left, decision.word)
            == compiler.run_xor_output(right, decision.word)
        ):
            raise AssertionError("invalid distinguishing word")
    full_product_states = states**components
    return {
        "seed": seed,
        "components": components,
        "states_per_component": states,
        "direct_sum_dimension": compiler.dimension,
        "full_product_states_decimal_digits": len(str(full_product_states)),
        "max_span_dimension": max(d.span_dimension for d in decisions),
        "max_witness_length": max(len(d.word or ()) for d in decisions),
        "median_decision_microseconds": 1e6 * float(np.median(elapsed)),
        "all_witnesses_valid": True,
    }


def run_all():
    small = [
        small_exact_trial(seed, components)
        for seed in range(8)
        for components in (2, 3, 4)
    ]
    scale = [scale_trial(seed) for seed in range(6)]
    total_queries = sum(c["queries"] for c in small)
    summary = {
        "small_query_count": total_queries,
        "full_product_agreements": sum(c["full_product_agreements"] for c in small),
        "all_returned_witnesses_valid": all(c["valid_witnesses"] == c["queries"] - c["equivalent_cases"] for c in small),
        "swapped_duplicate_equivalence_proofs": sum(
            c["swapped_duplicate_proved_equivalent"] for c in small
        ),
        "scale_components": 64,
        "scale_states_per_component": 8,
        "scale_direct_sum_dimension": 512,
        "scale_full_product_state_digits": scale[0]["full_product_states_decimal_digits"],
        "scale_max_span_dimension": max(c["max_span_dimension"] for c in scale),
        "scale_max_witness_length": max(c["max_witness_length"] for c in scale),
        "scale_median_decision_microseconds": float(
            np.median([c["median_decision_microseconds"] for c in scale])
        ),
    }
    summary["status"] = (
        "XOR_AGGREGATED_PRODUCT_EQUIVALENCE_EXACTLY_REDUCED_TO_GF2_DIRECT_SUM_PRIOR_ART_COLLISION"
        if summary["full_product_agreements"] == total_queries
        and summary["all_returned_witnesses_valid"]
        and summary["swapped_duplicate_equivalence_proofs"] == len(small)
        else "NOT_BROKEN"
    )
    return {"summary": summary, "small_cases": small, "scale_cases": scale}


if __name__ == "__main__":
    started = time.perf_counter()
    result = run_all()
    result["elapsed_seconds"] = time.perf_counter() - started
    path = HERE / "R201_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote {path}")
