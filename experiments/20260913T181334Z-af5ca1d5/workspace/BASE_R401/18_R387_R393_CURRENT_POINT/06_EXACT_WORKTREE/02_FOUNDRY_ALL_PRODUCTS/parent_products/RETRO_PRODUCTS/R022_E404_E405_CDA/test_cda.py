import unittest

import numpy as np

from cda import audit_channels, decision_value


class CDATests(unittest.TestCase):
    def test_known_garbling_is_certified(self):
        source = np.array([[0.9, 0.1], [0.1, 0.9]])
        garbling = np.array([[0.75, 0.25], [0.25, 0.75]])
        target = source @ garbling
        audit = audit_channels(source, target)
        self.assertEqual(audit.relation, "FIRST_STRICTLY_MORE_INFORMATIVE")
        self.assertLess(audit.first_to_second.maximum_reconstruction_error, 1e-9)

    def test_signal_relabeling_is_equivalent(self):
        first = np.array([[0.8, 0.2], [0.3, 0.7]])
        second = first[:, ::-1]
        self.assertEqual(audit_channels(first, second).relation, "BLACKWELL_EQUIVALENT")

    def test_channels_revealing_different_state_partitions_are_incomparable(self):
        first = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]])
        second = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(audit_channels(first, second).relation, "INCOMPARABLE")

    def test_garbling_cannot_raise_decision_value(self):
        source = np.array([[0.9, 0.1], [0.1, 0.9]])
        target = source @ np.array([[0.7, 0.3], [0.3, 0.7]])
        prior = np.array([0.5, 0.5])
        utility = np.eye(2)
        self.assertGreaterEqual(
            decision_value(source, prior, utility)["with_channel"],
            decision_value(target, prior, utility)["with_channel"],
        )


if __name__ == "__main__":
    unittest.main()

