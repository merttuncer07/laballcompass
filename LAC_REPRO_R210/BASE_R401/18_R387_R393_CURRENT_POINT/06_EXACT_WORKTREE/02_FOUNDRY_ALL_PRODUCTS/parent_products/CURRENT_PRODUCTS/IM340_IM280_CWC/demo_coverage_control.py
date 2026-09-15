"""Nonstationary forecast-width benchmark for CWC."""

from __future__ import annotations

import json

import numpy as np

from cwc import CalibrationWidthController, RawIntervalScoreController, summarize


def main() -> None:
    rng = np.random.default_rng(340280)
    scales = np.concatenate([np.full(800, 1.0), np.full(800, 2.5), np.full(800, 0.7)])
    centers = 0.35 * np.sin(np.arange(scales.size) / 37.0)
    outcomes = centers + rng.normal(0.0, scales)
    calibration = CalibrationWidthController()
    raw_score = RawIntervalScoreController()
    calibration_obs = []
    score_obs = []
    for outcome, center in zip(outcomes, centers):
        # The base scale is deliberately stale to force sequential width adaptation.
        calibration_obs.append(calibration.observe(float(outcome), float(center), 1.0))
        score_obs.append(raw_score.observe(float(outcome), float(center), 1.0))
    target = 0.9
    result = {
        "samples": int(scales.size),
        "target_coverage": target,
        "calibration_error_controller": summarize(calibration_obs, target),
        "raw_interval_score_gradient": summarize(score_obs, target),
        "phase_coverage": {
            "calibration_error_controller": [
                float(np.mean([item.covered for item in calibration_obs[start : start + 800]]))
                for start in (0, 800, 1600)
            ],
            "raw_interval_score_gradient": [
                float(np.mean([item.covered for item in score_obs[start : start + 800]]))
                for start in (0, 800, 1600)
            ],
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

