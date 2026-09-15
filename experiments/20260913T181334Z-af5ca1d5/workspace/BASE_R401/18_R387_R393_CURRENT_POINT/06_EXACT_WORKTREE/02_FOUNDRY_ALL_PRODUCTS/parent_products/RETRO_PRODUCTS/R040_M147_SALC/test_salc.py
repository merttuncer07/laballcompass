import unittest

from salc import audit_lumpability


class SALCTests(unittest.TestCase):
    def setUp(self) -> None:
        self.p = [
            [0.60, 0.20, 0.10, 0.10], [0.30, 0.50, 0.15, 0.05],
            [0.10, 0.10, 0.50, 0.30], [0.05, 0.15, 0.20, 0.60],
        ]
        self.partition = ["A", "A", "B", "B"]

    def test_exact_lumpability_produces_two_state_chain(self) -> None:
        result = audit_lumpability(self.p, self.partition)
        self.assertTrue(result.exact_lumpability)
        self.assertEqual(result.aggregate_transition_matrix, ((0.8, 0.2), (0.2, 0.8)))
        self.assertLess(result.maximum_horizon_total_variation, 1e-10)

    def test_violation_is_localized(self) -> None:
        p = [row[:] for row in self.p]; p[1] = [0.25, 0.50, 0.20, 0.05]
        result = audit_lumpability(p, self.partition)
        self.assertFalse(result.exact_lumpability)
        self.assertEqual(result.worst_source_block, "A")
        self.assertGreater(result.maximum_block_transition_deviation, 0.04)

    def test_error_budget_status_is_reported(self) -> None:
        p = [row[:] for row in self.p]; p[1] = [0.10, 0.50, 0.35, 0.05]
        result = audit_lumpability(p, self.partition, allowed_horizon_tv=0.001)
        self.assertEqual(result.status, "DECLARED_ERROR_BUDGET_EXCEEDED")

    def test_non_stochastic_matrix_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            audit_lumpability([[0.5, 0.6], [0.2, 0.8]], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
