"""Evaluate adaptive channel control against fixed and round-robin policies."""

from __future__ import annotations

import json

import numpy as np

from aicc import AdaptiveInformationController, InformationChannel


SLOPES = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.55, 0.55, 0.0]])
INTERCEPTS = np.array([0.0, -0.35, -0.35, -0.48])
CHANNELS = [
    InformationChannel("demand", np.array([1.0, 0.0, 0.0]), 0.12**2, 0.002),
    InformationChannel("failure", np.array([0.0, 1.0, 0.0]), 0.12**2, 0.002),
    InformationChannel("nuisance", np.array([0.0, 0.0, 1.0]), 0.04**2, 0.0005),
]


def episode(rng: np.random.Generator, policy: str, horizon: int = 5) -> tuple[float, int, list[str]]:
    prior_mean = np.zeros(3)
    prior_covariance = np.diag([0.75, 0.35, 2.0])
    true_state = rng.multivariate_normal(prior_mean, prior_covariance)
    controller = AdaptiveInformationController(prior_mean, prior_covariance, SLOPES, INTERCEPTS, CHANNELS)
    channel_names: list[str] = []
    total_cost = 0.0
    for step in range(horizon):
        if policy == "adaptive":
            channel = controller.choose_channel()
            if channel is None:
                break
        elif policy == "fixed_demand":
            channel = CHANNELS[0]
        elif policy == "round_robin":
            channel = CHANNELS[step % 2]
        else:
            raise ValueError(policy)
        observation = float(channel.measurement_vector @ true_state + rng.normal(0.0, np.sqrt(channel.noise_variance)))
        controller.update(channel, observation)
        total_cost += channel.cost
        channel_names.append(channel.name)
    chosen = controller.action()
    realized = SLOPES @ true_state + INTERCEPTS
    regret = float(np.max(realized) - realized[chosen] + total_cost)
    return regret, chosen, channel_names


def main() -> None:
    episodes = 3000
    results = {}
    for policy_index, policy in enumerate(("fixed_demand", "round_robin", "adaptive")):
        rng = np.random.default_rng(359014 + policy_index)
        regrets = []
        nuisance_pulls = 0
        channel_counts = {channel.name: 0 for channel in CHANNELS}
        for _ in range(episodes):
            regret, _, used = episode(rng, policy)
            regrets.append(regret)
            for name in used:
                channel_counts[name] += 1
                nuisance_pulls += int(name == "nuisance")
        results[policy] = {
            "mean_decision_regret_plus_cost": float(np.mean(regrets)),
            "p90_decision_regret_plus_cost": float(np.quantile(regrets, 0.9)),
            "channel_counts": channel_counts,
            "nuisance_pulls": nuisance_pulls,
        }
    results["adaptive_reduction_vs_fixed"] = 1.0 - (
        results["adaptive"]["mean_decision_regret_plus_cost"]
        / results["fixed_demand"]["mean_decision_regret_plus_cost"]
    )
    results["adaptive_reduction_vs_round_robin"] = 1.0 - (
        results["adaptive"]["mean_decision_regret_plus_cost"]
        / results["round_robin"]["mean_decision_regret_plus_cost"]
    )
    print(json.dumps({"episodes_per_policy": episodes, "results": results}, indent=2))


if __name__ == "__main__":
    main()

