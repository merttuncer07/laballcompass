import unittest

from srcd import design_reporting_contract


class SRCDTests(unittest.TestCase):
    def test_squared_error_elicits_mean(self) -> None:
        result = design_reporting_contract([0, 1, 2, 9], "MEAN", base_payment=100)
        self.assertAlmostEqual(result.elicited_report, 3.0)
        self.assertTrue(result.properness_verified_on_grid)

    def test_pinball_elicits_quantile(self) -> None:
        result = design_reporting_contract([1, 2, 3, 4, 100], "QUANTILE", level=0.8, base_payment=1000)
        self.assertAlmostEqual(result.elicited_report, 4.0)
        self.assertTrue(result.properness_verified_on_grid)

    def test_expectile_differs_from_mean_and_quantile(self) -> None:
        values = [0, 0, 0, 10]
        result = design_reporting_contract(values, "EXPECTILE", level=0.8, base_payment=100)
        self.assertGreater(result.elicited_report, 2.5)
        self.assertLess(result.elicited_report, 10.0)

    def test_payment_floor_can_destroy_strict_incentive(self) -> None:
        result = design_reporting_contract([0, 1, 2, 9], "MEAN", base_payment=0, payment_floor=0)
        self.assertTrue(result.properness_verified_on_grid)
        self.assertFalse(result.strict_incentive_preserved_after_payment_clipping)
        self.assertGreater(result.payment_optimal_max - result.payment_optimal_min, 5.0)


if __name__ == "__main__":
    unittest.main()
