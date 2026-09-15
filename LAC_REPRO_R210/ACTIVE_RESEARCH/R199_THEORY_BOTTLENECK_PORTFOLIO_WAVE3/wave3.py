from __future__ import annotations

import itertools
import json
import math
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# HM-05: Tsetlin finite automata -> finite-state rank-coded response


class FiniteResponseAutomaton:
    def __init__(self, arms: int, response: str, rng: np.random.Generator):
        self.arms = arms
        self.response = response
        self.rng = rng
        self.state = np.full(arms, 127, dtype=np.int16)
        self.time = 0

    def choose(self) -> int:
        # Deterministic sparse exploration is also finite state.
        if self.time % 13 == 0:
            action = (self.time // 13) % self.arms
        else:
            best = np.flatnonzero(self.state == self.state.max())
            action = int(self.rng.choice(best))
        self.time += 1
        return action

    def update(self, action: int, reward: float):
        if self.response == "binary":
            target = 255 if reward > 0.0 else 0
        elif self.response == "rank":
            target = int(round(255 * float(np.clip(reward, 0.0, 1.0))))
        else:
            raise ValueError(self.response)
        difference = target - int(self.state[action])
        delta = int(np.clip(round(difference / 32.0), -8, 8))
        if delta == 0 and difference != 0:
            delta = 1 if difference > 0 else -1
        self.state[action] = int(np.clip(self.state[action] + delta, 0, 255))


class DiscountedUCB:
    def __init__(self, arms: int, gamma: float = 0.995):
        self.arms = arms
        self.gamma = gamma
        self.count = np.zeros(arms)
        self.total = np.zeros(arms)
        self.time = 0

    def choose(self) -> int:
        unseen = np.flatnonzero(self.count < 1e-9)
        if len(unseen):
            return int(unseen[0])
        mean = self.total / self.count
        bonus = np.sqrt(2.0 * math.log(max(2.0, float(self.count.sum()))) / self.count)
        return int(np.argmax(mean + bonus))

    def update(self, action: int, reward: float):
        self.count *= self.gamma
        self.total *= self.gamma
        self.count[action] += 1.0
        self.total[action] += reward
        self.time += 1


class EpsilonEWMA:
    def __init__(self, arms: int, alpha: float, epsilon: float, rng: np.random.Generator):
        self.arms = arms
        self.alpha = alpha
        self.epsilon = epsilon
        self.rng = rng
        self.value = np.full(arms, 0.5)
        self.visited = np.zeros(arms, dtype=bool)

    def choose(self) -> int:
        unseen = np.flatnonzero(~self.visited)
        if len(unseen):
            return int(unseen[0])
        if self.rng.random() < self.epsilon:
            return int(self.rng.integers(self.arms))
        best = np.flatnonzero(self.value == self.value.max())
        return int(self.rng.choice(best))

    def update(self, action: int, reward: float):
        self.visited[action] = True
        self.value[action] += self.alpha * (reward - self.value[action])


def _bandit_expectation(scenario: str, time_index: int, horizon: int) -> np.ndarray:
    if scenario == "bernoulli":
        return np.array([0.42, 0.48, 0.54, 0.60, 0.66])
    if scenario == "payout":
        return 0.55 * np.array([0.20, 0.38, 0.56, 0.74, 0.92])
    if scenario == "drift":
        left = np.array([0.76, 0.65, 0.54, 0.43, 0.32])
        right = left[::-1]
        return left if time_index < horizon // 2 else right
    if scenario == "rare_vs_steady":
        return np.array([0.40, 0.42, 0.44, 0.45, 0.46])
    raise ValueError(scenario)


def _bandit_reward(
    rng: np.random.Generator, scenario: str, action: int, time_index: int, horizon: int
) -> float:
    means = _bandit_expectation(scenario, time_index, horizon)
    if scenario == "bernoulli":
        return float(rng.random() < means[action])
    if scenario == "payout":
        amount = np.array([0.20, 0.38, 0.56, 0.74, 0.92])[action]
        return float(amount if rng.random() < 0.55 else 0.0)
    if scenario == "drift":
        return float(np.clip(rng.normal(means[action], 0.07), 0.0, 1.0))
    # All arms except the first expose a rare-reward/zero stream; arm 0 is steady.
    if action == 0:
        return 0.40
    probabilities = np.array([0.0, 0.42, 0.44, 0.45, 0.46])
    return float(rng.random() < probabilities[action])


def tsetlin_trial(seed: int, scenario: str, horizon: int = 2600) -> dict:
    methods = {
        "binary": FiniteResponseAutomaton(5, "binary", np.random.default_rng(100 + seed)),
        "rank": FiniteResponseAutomaton(5, "rank", np.random.default_rng(200 + seed)),
        "ucb_g1": DiscountedUCB(5, 1.0),
        "ucb_g0999": DiscountedUCB(5, 0.999),
        "ucb_g0995": DiscountedUCB(5, 0.995),
        "ucb_g098": DiscountedUCB(5, 0.98),
    }
    for alpha in (0.02, 0.08, 0.20):
        for epsilon in (0.02, 0.06, 0.12):
            name = f"ewma_a{alpha}_e{epsilon}"
            methods[name] = EpsilonEWMA(
                5, alpha, epsilon, np.random.default_rng(300 + seed + len(methods))
            )
    rngs = {
        name: np.random.default_rng(10000 + seed * 31 + i)
        for i, name in enumerate(methods)
    }
    regret = {name: 0.0 for name in methods}
    for t in range(horizon):
        expectation = _bandit_expectation(scenario, t, horizon)
        best = float(expectation.max())
        for name, method in methods.items():
            action = method.choose()
            reward = _bandit_reward(rngs[name], scenario, action, t, horizon)
            method.update(action, reward)
            regret[name] += best - float(expectation[action])
    return {"seed": seed, "scenario": scenario, **{f"{k}_regret": v for k, v in regret.items()}}


def run_tsetlin() -> dict:
    scenarios = ("bernoulli", "payout", "drift", "rare_vs_steady")
    cases = [tsetlin_trial(seed, scenario) for seed in range(24) for scenario in scenarios]
    baseline_names = [
        key
        for key in cases[0]
        if key.endswith("_regret") and key not in ("binary_regret", "rank_regret")
    ]
    by_scenario = {}
    selected_baseline = {}
    for scenario in scenarios:
        active = [c for c in cases if c["scenario"] == scenario]
        means = {
            "binary": float(np.mean([c["binary_regret"] for c in active])),
            "rank": float(np.mean([c["rank_regret"] for c in active])),
        }
        means.update(
            {name[:-7]: float(np.mean([c[name] for c in active])) for name in baseline_names}
        )
        best_name = min((name for name in means if name not in ("binary", "rank")), key=means.get)
        selected_baseline[scenario] = best_name
        means["best_tuned_baseline"] = {"name": best_name, "regret": means[best_name]}
        by_scenario[scenario] = means
    rank_binary = sum(c["rank_regret"] < c["binary_regret"] for c in cases)
    rank_best = sum(
        c["rank_regret"] < c[f"{selected_baseline[c['scenario']]}_regret"] for c in cases
    )
    competitive_scenarios = sum(
        by_scenario[s]["rank"] <= 1.10 * by_scenario[s]["best_tuned_baseline"]["regret"]
        for s in scenarios
    )
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "rank_beats_binary": rank_binary,
            "rank_beats_scenario_tuned_baseline": rank_best,
            "rank_within_10pct_of_best_tuned_scenarios": competitive_scenarios,
            "scenario_mean_regret": by_scenario,
            "finite_state_bits_per_arm": 8,
            "status": (
                "BINARY_RESPONSE_BROKEN_FINITE_STATE_MODERN_POLICY_EDGE_UNPROVEN"
                if rank_binary >= 70
                else "NOT_BROKEN"
            ),
        },
    }


# ---------------------------------------------------------------------------
# HM-06: Glushkov experiments -> separability-certified composition fingerprints


@dataclass
class MooreAutomaton:
    transition: np.ndarray
    output: np.ndarray

    @property
    def states(self):
        return len(self.output)

    @property
    def alphabet(self):
        return self.transition.shape[1]

    def run_output(self, state: int, word: tuple[int, ...]) -> int:
        for symbol in word:
            state = int(self.transition[state, symbol])
        return int(self.output[state])


def random_observable_automaton(rng: np.random.Generator, states: int = 6, alphabet: int = 2):
    for _ in range(500):
        automaton = MooreAutomaton(
            rng.integers(0, states, size=(states, alphabet)),
            rng.integers(0, 2, size=states),
        )
        if all(
            shortest_distinguishing_word(automaton, i, j) is not None
            for i in range(states)
            for j in range(i + 1, states)
        ):
            return automaton
    raise RuntimeError("could not sample observable automaton")


def shortest_distinguishing_word(automaton: MooreAutomaton, left: int, right: int):
    queue = deque([(left, right, ())])
    seen = {(left, right)}
    while queue:
        a, b, word = queue.popleft()
        if automaton.output[a] != automaton.output[b]:
            return word
        for symbol in range(automaton.alphabet):
            na = int(automaton.transition[a, symbol])
            nb = int(automaton.transition[b, symbol])
            pair = (na, nb)
            if pair not in seen:
                seen.add(pair)
                queue.append((na, nb, word + (symbol,)))
    return None


def characterization_set(automaton: MooreAutomaton):
    state_pairs = [(i, j) for i in range(automaton.states) for j in range(i + 1, automaton.states)]
    candidates = set()
    for i, j in state_pairs:
        word = shortest_distinguishing_word(automaton, i, j)
        if word is None:
            raise ValueError("automaton is not observable")
        candidates.add(word)
    unresolved = set(state_pairs)
    chosen = []
    while unresolved:
        best_word, best_cover = max(
            (
                (
                    word,
                    {
                        pair
                        for pair in unresolved
                        if automaton.run_output(pair[0], word)
                        != automaton.run_output(pair[1], word)
                    },
                )
                for word in candidates
            ),
            key=lambda item: len(item[1]),
        )
        if not best_cover:
            raise RuntimeError("characterization stalled")
        chosen.append(best_word)
        unresolved -= best_cover
    return tuple(chosen)


def component_fingerprint(automata, global_state, words):
    return tuple(
        tuple(automaton.run_output(state, word) for automaton, state in zip(automata, global_state))
        for word in words
    )


def glushkov_trial(seed: int, components: int) -> dict:
    rng = np.random.default_rng(40000 + seed * 13 + components)
    automata = [random_observable_automaton(rng) for _ in range(components)]
    words = sorted(set(itertools.chain.from_iterable(characterization_set(a) for a in automata)))
    exact = True
    for _ in range(15000):
        left = tuple(int(rng.integers(a.states)) for a in automata)
        right = tuple(int(rng.integers(a.states)) for a in automata)
        if left == right:
            continue
        exact &= component_fingerprint(automata, left, words) != component_fingerprint(
            automata, right, words
        )
    full_states = int(np.prod([a.states for a in automata], dtype=np.int64))
    full_transition_cells = full_states * automata[0].alphabet
    factor_transition_cells = sum(a.states * a.alphabet for a in automata)

    # XOR aggregation destroys separability: swapping two states in duplicated
    # components is invisible for every common input word.
    duplicate = automata[0]
    xor_left, xor_right = (0, 1), (1, 0)
    xor_indistinguishable = all(
        (
            duplicate.run_output(xor_left[0], word)
            ^ duplicate.run_output(xor_left[1], word)
        )
        == (
            duplicate.run_output(xor_right[0], word)
            ^ duplicate.run_output(xor_right[1], word)
        )
        for word in words
    )
    vector_distinguishable = component_fingerprint(
        [duplicate, duplicate], xor_left, words
    ) != component_fingerprint([duplicate, duplicate], xor_right, words)
    return {
        "seed": seed,
        "components": components,
        "characterization_words": len(words),
        "random_pair_exact": bool(exact),
        "full_product_states": full_states,
        "full_transition_cells": full_transition_cells,
        "factor_transition_cells": factor_transition_cells,
        "transition_representation_reduction": full_transition_cells / factor_transition_cells,
        "xor_stress_rejects_vector_certificate": bool(
            xor_indistinguishable and vector_distinguishable
        ),
    }


def run_glushkov() -> dict:
    cases = [glushkov_trial(seed, components) for seed in range(8) for components in (2, 4, 6, 8)]
    exact = sum(c["random_pair_exact"] for c in cases)
    xor_reject = sum(c["xor_stress_rejects_vector_certificate"] for c in cases)
    largest = [c for c in cases if c["components"] == 8]
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "vector_output_exact": exact,
            "xor_aggregation_rejected": xor_reject,
            "median_characterization_words": float(
                np.median([c["characterization_words"] for c in cases])
            ),
            "eight_component_median_full_states": float(
                np.median([c["full_product_states"] for c in largest])
            ),
            "eight_component_median_representation_reduction": float(
                np.median([c["transition_representation_reduction"] for c in largest])
            ),
            "status": (
                "VECTOR_OBSERVATION_COMPOSITION_EXACTLY_FACTORIZED_AGGREGATION_OPEN"
                if exact == len(cases) and xor_reject == len(cases)
                else "NOT_BROKEN"
            ),
        },
    }


# ---------------------------------------------------------------------------
# HM-13: discrete extremal moment problem -> threshold + atomic witness compiler


def feasible_three_atom_representations(grid: np.ndarray, mean: float, second: float):
    triples = np.array(list(itertools.combinations(range(len(grid)), 3)), dtype=int)
    x0, x1, x2 = grid[triples[:, 0]], grid[triples[:, 1]], grid[triples[:, 2]]
    w0 = (second - mean * (x1 + x2) + x1 * x2) / ((x0 - x1) * (x0 - x2))
    w1 = (second - mean * (x0 + x2) + x0 * x2) / ((x1 - x0) * (x1 - x2))
    w2 = (second - mean * (x0 + x1) + x0 * x1) / ((x2 - x0) * (x2 - x1))
    weights = np.column_stack([w0, w1, w2])
    feasible = np.all(weights >= -1e-9, axis=1) & np.all(weights <= 1.0 + 1e-9, axis=1)
    return triples[feasible], np.clip(weights[feasible], 0.0, 1.0)


def compile_extremal_threshold(
    grid: np.ndarray, mean: float, variance: float, alpha: float
):
    triples, weights = feasible_three_atom_representations(grid, mean, mean**2 + variance)
    if not len(triples):
        raise ValueError("moment vector is infeasible on supplied support grid")
    best = None
    bounds = []
    candidate_thresholds = list(grid) + [float(grid[-1] + (grid[-1] - grid[-2]))]
    for threshold in candidate_thresholds:
        tail_mask = grid[triples] >= threshold
        tail = np.sum(weights * tail_mask, axis=1)
        witness_index = int(np.argmax(tail))
        bound = float(tail[witness_index])
        bounds.append((float(threshold), bound))
        if bound <= alpha + 1e-10 and best is None:
            best = {
                "threshold": float(threshold),
                "worst_tail_probability": bound,
                "atoms": grid[triples[witness_index]].tolist(),
                "weights": weights[witness_index].tolist(),
            }
    if best is None:
        raise RuntimeError("no safe threshold")
    best["bound_curve"] = bounds
    return best


def moment_trial(seed: int, alpha: float = 0.15, regime: str = "interior") -> dict:
    rng = np.random.default_rng(70000 + seed)
    grid = np.linspace(0.0, 1.0, 61)
    if regime == "interior":
        ids = rng.choice(np.arange(3, len(grid) - 3), 5, replace=False)
        true_weights = rng.dirichlet(np.ones(5))
    elif regime == "boundary_skew":
        probability = rng.uniform(0.04, 0.14)
        ids = np.array([0, len(grid) - 1])
        true_weights = np.array([1.0 - probability, probability])
    else:
        raise ValueError(regime)
    mean = float(np.sum(true_weights * grid[ids]))
    second = float(np.sum(true_weights * grid[ids] ** 2))
    variance = second - mean**2
    compiled = compile_extremal_threshold(grid, mean, variance, alpha)
    threshold = compiled["threshold"]
    true_tail = float(np.sum(true_weights[grid[ids] >= threshold]))
    cantelli = mean + math.sqrt(max(variance, 0.0) * (1.0 - alpha) / alpha)
    spacing = grid[1] - grid[0]
    cantelli_safe = min(float(grid[-1] + spacing), float(math.ceil(cantelli / spacing) * spacing))
    return {
        "seed": seed,
        "regime": regime,
        "mean": mean,
        "variance": variance,
        "compiled_threshold": threshold,
        "compiled_worst_tail": compiled["worst_tail_probability"],
        "true_tail": true_tail,
        "cantelli_grid_threshold": cantelli_safe,
        "threshold_improvement": cantelli_safe - threshold,
        "witness_atoms": compiled["atoms"],
        "witness_weights": compiled["weights"],
    }


def run_moments() -> dict:
    cases = [
        moment_trial(seed, regime=regime)
        for seed in range(18)
        for regime in ("interior", "boundary_skew")
    ]
    safe = sum(c["true_tail"] <= 0.15 + 1e-9 for c in cases)
    improved = sum(c["threshold_improvement"] > 1e-9 for c in cases)
    witnesses = sum(c["compiled_worst_tail"] <= 0.15 + 1e-9 for c in cases)
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "true_distributions_safe": safe,
            "atomic_witnesses_at_or_below_alpha": witnesses,
            "less_conservative_than_cantelli": improved,
            "mean_threshold_improvement": float(
                np.mean([c["threshold_improvement"] for c in cases])
            ),
            "improvement_by_regime": {
                regime: {
                    "improved": sum(
                        c["threshold_improvement"] > 1e-9
                        for c in cases
                        if c["regime"] == regime
                    ),
                    "mean_threshold_improvement": float(
                        np.mean(
                            [
                                c["threshold_improvement"]
                                for c in cases
                                if c["regime"] == regime
                            ]
                        )
                    ),
                }
                for regime in ("interior", "boundary_skew")
            },
            "status": (
                "FINITE_SUPPORT_DECISION_AND_EXTREMAL_WITNESS_COMPILED_PRIOR_ART"
                if safe == len(cases) and witnesses == len(cases) and improved >= 18
                else "NOT_BROKEN"
            ),
        },
    }


def run_all():
    started = time.perf_counter()
    result = {
        "tsetlin": run_tsetlin(),
        "glushkov": run_glushkov(),
        "extremal_moments": run_moments(),
    }
    result["elapsed_seconds"] = time.perf_counter() - started
    return result


if __name__ == "__main__":
    result = run_all()
    path = HERE / "R199_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v["summary"] for k, v in result.items() if isinstance(v, dict)}, indent=2))
    print(f"wrote {path}")
