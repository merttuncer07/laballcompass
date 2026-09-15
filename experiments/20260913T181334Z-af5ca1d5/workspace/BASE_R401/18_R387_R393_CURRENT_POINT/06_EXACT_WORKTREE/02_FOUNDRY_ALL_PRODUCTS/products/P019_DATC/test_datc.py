import unittest

import numpy as np

if __package__:
    from .datc import DamageAwareTriggerController
else:
    from datc import DamageAwareTriggerController


class DATCTests(unittest.TestCase):
    def fixture(self):
        rng = np.random.default_rng(5)
        residual = rng.normal(scale=0.35, size=400)
        event = np.zeros(400, dtype=bool)
        for start in (80, 200, 320):
            residual[start : start + 30] += 0.7
            event[start + 10 : start + 45] = True
        load = np.ones(400)
        return residual, load, event

    def test_sequential_signal_is_causal_and_nonnegative(self):
        residual, load, _ = self.fixture()
        controller = DamageAwareTriggerController()
        signal = controller.sequential_signal(residual, load)
        self.assertEqual(len(signal), len(residual))
        self.assertTrue(np.all(signal >= 0.0))
        changed = residual.copy()
        changed[-1] += 100.0
        changed_signal = controller.sequential_signal(changed, load)
        np.testing.assert_allclose(signal[:-1], changed_signal[:-1])

    def test_fit_keeps_both_candidates_visible(self):
        residual, load, event = self.fixture()
        controller = DamageAwareTriggerController()
        result = controller.fit(
            residuals=residual,
            load_amplitudes=load,
            protected_event=event,
            loss=np.abs(residual),
        )
        names = {row["candidate"] for row in result["design"]["ranking"]}
        self.assertEqual(names, {"raw_directed_residual", "sequential_damage_evidence"})

    def test_fresh_evaluation_uses_frozen_policy(self):
        residual, load, event = self.fixture()
        controller = DamageAwareTriggerController()
        fitted = controller.fit(
            residuals=residual[:200], load_amplitudes=load[:200],
            protected_event=event[:200], loss=np.abs(residual[:200]),
        )
        fresh = controller.evaluate(
            residuals=residual[200:], load_amplitudes=load[200:], protected_event=event[200:]
        )
        self.assertEqual(fresh["selected_threshold"], fitted["policy"].threshold)

    def test_evaluation_before_fit_rejected(self):
        with self.assertRaises(RuntimeError):
            DamageAwareTriggerController().evaluate(
                residuals=[0.0], load_amplitudes=[1.0], protected_event=[False]
            )


if __name__ == "__main__":
    unittest.main()
