import unittest

import numpy as np

from aicc import AdaptiveInformationController, InformationChannel


class AICCTests(unittest.TestCase):
    def build(self):
        channels = [
            InformationChannel("relevant", np.array([1.0, 0.0]), 0.01),
            InformationChannel("irrelevant", np.array([0.0, 1.0]), 0.001),
        ]
        return AdaptiveInformationController(
            np.zeros(2),
            np.diag([1.0, 10.0]),
            np.array([[0.0, 0.0], [1.0, 0.0]]),
            np.array([0.0, -0.2]),
            channels,
        )

    def test_decision_relevant_channel_beats_high_variance_nuisance(self):
        controller = self.build()
        self.assertEqual(controller.choose_channel().name, "relevant")

    def test_irrelevant_channel_has_zero_decision_value(self):
        controller = self.build()
        values = {item.name: item for item in controller.rank_channels()}
        self.assertAlmostEqual(values["irrelevant"].expected_decision_improvement, 0.0, places=10)

    def test_measurement_reduces_variance_in_its_direction(self):
        controller = self.build()
        before = controller.covariance[0, 0]
        controller.update(controller.channels[0], 0.5)
        self.assertLess(controller.covariance[0, 0], before)


if __name__ == "__main__":
    unittest.main()

