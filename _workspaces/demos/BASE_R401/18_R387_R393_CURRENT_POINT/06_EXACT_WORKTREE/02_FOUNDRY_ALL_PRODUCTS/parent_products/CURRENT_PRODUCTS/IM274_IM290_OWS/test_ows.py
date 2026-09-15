from __future__ import annotations

import unittest

from ows import OverlapAwareWeightStabilizer


class OverlapAwareWeightStabilizerTests(unittest.TestCase):
    def test_uniform_weights_have_full_effective_sample(self) -> None:
        audit = OverlapAwareWeightStabilizer().audit([1, 1, 1, 1])
        self.assertAlmostEqual(audit.effective_sample_size, 4.0)
        self.assertEqual(audit.status, "SUPPORT_USABLE")

    def test_extreme_weight_is_flagged_fragile(self) -> None:
        audit = OverlapAwareWeightStabilizer(0.5).audit([1, 1, 1, 1000])
        self.assertEqual(audit.status, "SUPPORT_FRAGILE")

    def test_stabilization_increases_effective_sample_size(self) -> None:
        result = OverlapAwareWeightStabilizer().fit(
            [1, 1, 1, 100], [0, 0.2, 0.4, 1.0], (0.0, 1.0)
        )
        self.assertGreaterEqual(
            result.effective_sample_size_after, result.effective_sample_size_before
        )

    def test_outcome_shell_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            OverlapAwareWeightStabilizer().fit([1, 1], [0, 2], (0, 1))


if __name__ == "__main__":
    unittest.main()
