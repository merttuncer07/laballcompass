import unittest

import numpy as np

if __package__:
    from .catr import CalibrationAwareTriggerRouter
else:
    from catr import CalibrationAwareTriggerRouter


class CATRTests(unittest.TestCase):
    def test_uncertainty_endpoint_can_win_without_being_forced(self):
        rng = np.random.default_rng(4)
        calibration_center = rng.normal(size=200)
        calibration_scale = np.where(np.arange(200) % 3 == 0, 0.8, 0.2)
        calibration_y = calibration_center + rng.normal(scale=calibration_scale)
        design_center = rng.normal(size=500)
        design_scale = np.where(np.arange(500) % 3 == 0, 0.8, 0.2)
        latent = design_center + 0.8 * design_scale
        design_y = design_center + rng.normal(scale=design_scale)
        event = latent > 1.0
        router = CalibrationAwareTriggerRouter(false_negative_cost=8.0, false_positive_cost=1.0)
        result = router.fit(
            calibration_outcomes=calibration_y,
            calibration_centers=calibration_center,
            calibration_scales=calibration_scale,
            design_outcomes=design_y,
            design_centers=design_center,
            design_scales=design_scale,
            design_event=event,
            design_loss=np.abs(latent),
        )
        self.assertIn(result["policy"].candidate, {"center", "calibrated_upper"})
        self.assertEqual(result["policy"].candidate, result["design"]["selected"]["candidate"])

    def test_fresh_evaluation_uses_frozen_threshold(self):
        router = CalibrationAwareTriggerRouter(false_negative_cost=3.0)
        x = np.linspace(-1, 1, 40)
        result = router.fit(
            calibration_outcomes=x,
            calibration_centers=x,
            calibration_scales=np.ones(40) * 0.2,
            design_outcomes=x,
            design_centers=x,
            design_scales=np.ones(40) * 0.2,
            design_event=x > 0,
            design_loss=np.abs(x),
        )
        threshold = result["policy"].threshold
        fresh = router.evaluate_prequential(
            outcomes=x,
            centers=x,
            scales=np.ones(40) * 0.2,
            event=x > 0,
        )
        self.assertEqual(fresh["selected_threshold"], threshold)

    def test_evaluation_before_fit_rejected(self):
        with self.assertRaises(RuntimeError):
            CalibrationAwareTriggerRouter().evaluate_prequential(
                outcomes=[0.0], centers=[0.0], scales=[1.0], event=[False]
            )

    def test_nonpositive_scale_rejected(self):
        with self.assertRaises(ValueError):
            CalibrationAwareTriggerRouter().fit(
                calibration_outcomes=[0.0], calibration_centers=[0.0], calibration_scales=[0.0],
                design_outcomes=[0.0], design_centers=[0.0], design_scales=[1.0],
                design_event=[False], design_loss=[0.0],
            )


if __name__ == "__main__":
    unittest.main()
