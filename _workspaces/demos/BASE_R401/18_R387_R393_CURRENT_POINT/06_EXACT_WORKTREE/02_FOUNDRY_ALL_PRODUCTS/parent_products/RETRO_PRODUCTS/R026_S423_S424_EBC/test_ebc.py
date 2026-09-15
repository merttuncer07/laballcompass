import unittest

from ebc import HistoricalEstimate, borrow_evidence


class EBCTests(unittest.TestCase):
    def test_compatible_history_reduces_uncertainty(self) -> None:
        result = borrow_evidence(
            1.0, 0.3, [HistoricalEstimate("old", 1.05, 0.2)], borrowing_cap_ratio=3.0
        )
        self.assertLess(result.posterior_standard_error, 0.3)
        self.assertGreater(result.contributions[0].final_power, 0.9)

    def test_conflicting_precise_history_is_downweighted(self) -> None:
        result = borrow_evidence(
            0.0, 0.2, [HistoricalEstimate("conflict", 3.0, 0.05)], compatibility_scale=1.0
        )
        self.assertLess(result.contributions[0].final_power, 1e-10)
        self.assertAlmostEqual(result.posterior_estimate, 0.0, places=6)

    def test_total_borrowed_precision_obeys_cap(self) -> None:
        history = [HistoricalEstimate(str(i), 1.0, 0.01) for i in range(5)]
        result = borrow_evidence(1.0, 0.5, history, borrowing_cap_ratio=1.5)
        self.assertLessEqual(result.borrowing_precision_ratio, 1.5 + 1e-12)
        self.assertLess(result.cap_scale, 1.0)

    def test_zero_cap_equals_current_only(self) -> None:
        result = borrow_evidence(
            2.0, 0.4, [HistoricalEstimate("old", 1.0, 0.1)], borrowing_cap_ratio=0.0
        )
        self.assertAlmostEqual(result.posterior_estimate, 2.0)
        self.assertAlmostEqual(result.posterior_standard_error, 0.4)


if __name__ == "__main__":
    unittest.main()
