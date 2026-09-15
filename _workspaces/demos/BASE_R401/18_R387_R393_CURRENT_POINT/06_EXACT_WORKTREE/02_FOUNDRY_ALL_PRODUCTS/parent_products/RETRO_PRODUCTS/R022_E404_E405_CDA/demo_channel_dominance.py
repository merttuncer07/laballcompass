"""Construct a garbled channel and audit its decision value."""

from __future__ import annotations

import json

import numpy as np

from cda import audit_channels, decision_value


def main() -> None:
    detailed = np.array([[0.85, 0.10, 0.05], [0.10, 0.80, 0.10], [0.05, 0.15, 0.80]])
    imposed_garbling = np.array([[0.80, 0.20], [0.30, 0.70], [0.50, 0.50]])
    coarse = detailed @ imposed_garbling
    audit = audit_channels(detailed, coarse)
    prior = np.array([0.30, 0.40, 0.30])
    correct_action_utility = np.eye(3)
    detailed_value = decision_value(detailed, prior, correct_action_utility)
    coarse_value = decision_value(coarse, prior, correct_action_utility)
    output = {
        "relation": audit.relation,
        "recovered_garbling": audit.first_to_second.garbling_matrix.tolist(),
        "forward_reconstruction_error": audit.first_to_second.maximum_reconstruction_error,
        "reverse_best_error": audit.second_to_first.maximum_reconstruction_error,
        "detailed_channel_decision_value": detailed_value,
        "coarse_channel_decision_value": coarse_value,
        "value_lost_to_garbling": detailed_value["with_channel"] - coarse_value["with_channel"],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

