"""Benchmark accumulated subcritical evidence against a one-shot threshold."""

from __future__ import annotations

import json

import numpy as np

from dsda import DirectionalSubcriticalDamageAccumulator


def episode(rng: np.random.Generator, fatigues: bool, horizon: int = 900) -> tuple[int | None, int | None, int | None]:
    # Give the one-shot comparator a reachable threshold; it can now gain lead
    # time from rare extremes, but must pay the corresponding false-alarm cost.
    monitor = DirectionalSubcriticalDamageAccumulator(one_shot_threshold=3.2)
    sequential_alarm = None
    one_shot_alarm = None
    failure = None
    true_damage = 0.0
    for time in range(horizon):
        load = float(np.clip(rng.normal(0.76, 0.08), 0.35, 0.95))
        if fatigues and time >= 100:
            true_damage += (load**4) / 220.0
            signal = 0.13 + 0.48 * min(true_damage, 1.2)
        else:
            signal = 0.0
        # Instrument saturation reflects the product's subcritical-signal setting.
        residual = float(np.clip(rng.normal(signal, 1.0), -3.45, 3.45))
        state = monitor.update(residual, load)
        if state.alarm and sequential_alarm is None:
            sequential_alarm = time
        if state.one_shot_alarm and one_shot_alarm is None:
            one_shot_alarm = time
        if true_damage >= 1.0 and failure is None:
            failure = time
            break
    return sequential_alarm, one_shot_alarm, failure


def main() -> None:
    episodes = 1600
    summary = {}
    for fatigues in (False, True):
        rng = np.random.default_rng(374272 + int(fatigues))
        sequential = []
        one_shot = []
        failures = []
        for _ in range(episodes):
            seq, shot, failure = episode(rng, fatigues)
            sequential.append(seq)
            one_shot.append(shot)
            failures.append(failure)
        if fatigues:
            valid = [index for index, failure in enumerate(failures) if failure is not None]
            seq_detected = [index for index in valid if sequential[index] is not None and sequential[index] < failures[index]]
            shot_detected = [index for index in valid if one_shot[index] is not None and one_shot[index] < failures[index]]
            summary["fatigue"] = {
                "failure_episodes": len(valid),
                "sequential_detection_rate": len(seq_detected) / len(valid),
                "one_shot_detection_rate": len(shot_detected) / len(valid),
                "median_sequential_lead_cycles": float(
                    np.median([failures[index] - sequential[index] for index in seq_detected])
                ) if seq_detected else 0.0,
                "median_one_shot_lead_cycles": float(
                    np.median([failures[index] - one_shot[index] for index in shot_detected])
                ) if shot_detected else 0.0,
            }
        else:
            summary["healthy"] = {
                "sequential_false_alarm_rate": sum(item is not None for item in sequential) / episodes,
                "one_shot_false_alarm_rate": sum(item is not None for item in one_shot) / episodes,
            }
    print(json.dumps({"episodes_per_class": episodes, "results": summary}, indent=2))


if __name__ == "__main__":
    main()
