import unittest

from dsda import DirectionalSubcriticalDamageAccumulator


class DSDATests(unittest.TestCase):
    def test_repeated_subcritical_signal_accumulates_to_alarm(self):
        monitor = DirectionalSubcriticalDamageAccumulator(evidence_threshold=3.0)
        state = None
        for _ in range(120):
            state = monitor.update(0.8, 0.8)
        self.assertTrue(state.alarm)
        self.assertFalse(state.one_shot_alarm)

    def test_single_extreme_cycle_cannot_trigger_sequential_alarm(self):
        monitor = DirectionalSubcriticalDamageAccumulator(evidence_threshold=0.5, minimum_contributing_cycles=12)
        state = monitor.update(100.0, 1.0)
        self.assertFalse(state.alarm)
        self.assertTrue(state.one_shot_alarm)

    def test_opposite_direction_does_not_accumulate(self):
        monitor = DirectionalSubcriticalDamageAccumulator(evidence_threshold=2.0)
        for _ in range(100):
            state = monitor.update(-0.5, 0.8)
        self.assertFalse(state.alarm)
        self.assertAlmostEqual(state.sequential_evidence, 0.0)

    def test_damage_proxy_grows_with_load_cycles(self):
        monitor = DirectionalSubcriticalDamageAccumulator()
        before = monitor.damage_proxy
        state = monitor.update(0.0, 0.8)
        self.assertGreater(state.damage_proxy, before)


if __name__ == "__main__":
    unittest.main()

