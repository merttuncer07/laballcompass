import unittest

from mcris import Intervention, MonthlyTransitionRates, simulate_mortgage_intervention


BASE = MonthlyTransitionRates(.003, .01, .008, .06, .004, .15)


class Tests(unittest.TestCase):
    def test_probability_mass_is_conserved(self):
        result = simulate_mortgage_intervention(
            cohort_size=1000, horizon_months=24, baseline_rates=BASE,
            intervention=Intervention(), balance_per_loan=100_000, recovery_fraction=.5,
        )
        self.assertAlmostEqual(result.baseline.probability_mass, 1000)
        self.assertAlmostEqual(result.intervention.probability_mass, 1000)

    def test_competing_prepayment_reduces_later_defaults(self):
        result = simulate_mortgage_intervention(
            cohort_size=1000, horizon_months=60, baseline_rates=BASE,
            intervention=Intervention(performing_prepay_multiplier=3),
            balance_per_loan=100_000, recovery_fraction=.5,
        )
        self.assertLess(result.intervention.cumulative_default, result.baseline.cumulative_default)
        self.assertGreater(result.intervention.cumulative_prepay, result.baseline.cumulative_prepay)

    def test_default_reduction_is_valued_net_of_cost(self):
        result = simulate_mortgage_intervention(
            cohort_size=1000, horizon_months=48, baseline_rates=BASE,
            intervention=Intervention(delinquent_default_multiplier=.4, performing_delinquency_multiplier=.5, one_time_cost_per_loan=100),
            balance_per_loan=150_000, recovery_fraction=.5,
        )
        self.assertGreater(result.defaults_avoided, 0)
        self.assertGreater(result.net_value, 0)

    def test_impossible_competing_rates_are_rejected(self):
        with self.assertRaises(ValueError):
            simulate_mortgage_intervention(
                cohort_size=10, horizon_months=12,
                baseline_rates=MonthlyTransitionRates(.6, .6, 0, 0, 0, 0),
                intervention=Intervention(), balance_per_loan=1, recovery_fraction=.5,
            )


if __name__ == "__main__":
    unittest.main()
