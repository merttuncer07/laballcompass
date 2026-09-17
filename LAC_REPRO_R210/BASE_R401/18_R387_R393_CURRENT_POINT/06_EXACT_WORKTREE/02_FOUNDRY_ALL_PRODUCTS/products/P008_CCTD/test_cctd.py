import unittest

import numpy as np

if __package__:
    from .cctd import ConfidenceCalibratedTriggerDesigner, TriggerDeployment, evaluate_deployment
else:
    from cctd import ConfidenceCalibratedTriggerDesigner, TriggerDeployment, evaluate_deployment


class CCTDTests(unittest.TestCase):
    def test_requires_calibration_before_design(self):
        model = ConfidenceCalibratedTriggerDesigner()
        with self.assertRaises(RuntimeError):
            model.build_signal_views([0.0, 1.0], [1.0, 1.0])

    def test_calibration_and_signal_contract(self):
        model = ConfidenceCalibratedTriggerDesigner(target_coverage=0.8)
        result = model.calibrate(
            outcomes=[0.0, 1.0, 2.0, 3.0, 4.0],
            centers=[0.1, 0.9, 2.1, 2.9, 4.1],
            base_scales=[0.5] * 5,
        )
        views = model.build_signal_views([1.0, 2.0], [0.5, 0.5])
        self.assertGreater(result["calibrated_multiplier"], 0.0)
        np.testing.assert_allclose(
            views["upper"] - views["center"],
            views["center"] - views["lower"],
        )

    def test_design_returns_frozen_deployment(self):
        model = ConfidenceCalibratedTriggerDesigner(
            target_coverage=0.8,
            false_negative_cost=3.0,
            false_positive_cost=1.0,
        )
        model.calibrate([0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0.5] * 5)
        centers = np.linspace(-1.0, 1.0, 30)
        scales = np.where(centers > 0, 0.4, 0.2)
        events = centers + 0.25 * scales > 0.25
        designed = model.design(centers, scales, events, np.ones(30))
        deployment = designed["deployment"]
        self.assertIn(deployment.signal_view, {"center", "lower", "upper"})
        self.assertEqual(deployment.predict(centers, scales).shape, events.shape)
        self.assertTrue(all(row["correlation_with_loss"] is None for row in designed["design"]["ranking"]))

    def test_protected_gate_can_retain_incumbent(self):
        model = ConfidenceCalibratedTriggerDesigner(target_coverage=0.8)
        model.calibrate([0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [1.0] * 5)
        centers = np.linspace(-1.0, 1.0, 40)
        scales = np.ones(40) * 0.2
        events = centers >= 0.0
        out = model.design_with_protected_audit(
            design_centers=centers,
            design_base_scales=scales,
            design_event=events,
            design_loss=np.ones(40),
            protected_centers=centers,
            protected_base_scales=scales,
            protected_event=events,
            bootstrap_samples=100,
            material_regret=1.0,
        )
        self.assertFalse(out["promotion_gate"]["promoted"])
        self.assertEqual(out["stable_deployment"].signal_view, "center")

    def test_evaluation_uses_declared_costs(self):
        deployment = TriggerDeployment(
            signal_view="center",
            threshold=0.5,
            calibrated_multiplier=1.0,
            target_coverage=0.9,
            objective_on_design=0.0,
            false_negative_cost=3.0,
            false_positive_cost=2.0,
        )
        result = evaluate_deployment(
            deployment,
            centers=[0.0, 1.0, 0.0, 1.0],
            base_scales=[1.0] * 4,
            protected_event=[False, True, True, False],
        )
        self.assertAlmostEqual(result["objective"], 1.25)


if __name__ == "__main__":
    unittest.main()
