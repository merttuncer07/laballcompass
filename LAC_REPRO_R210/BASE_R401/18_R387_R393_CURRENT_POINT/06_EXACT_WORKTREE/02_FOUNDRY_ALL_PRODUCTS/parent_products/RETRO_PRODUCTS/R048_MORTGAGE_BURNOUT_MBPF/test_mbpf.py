import unittest

from mbpf import forecast_burnout_prepayment


class Tests(unittest.TestCase):
    def test_high_propensity_exit_creates_burnout(self):
        result = forecast_burnout_prepayment(
            cohort_size=1000, base_monthly_prepayment_rates=[.03] * 36,
            propensity_multipliers=[.2, 1, 3], initial_class_weights=[.4, .4, .2],
        )
        self.assertLess(result.effective_prepayment_rates[-1], result.effective_prepayment_rates[0])
        self.assertLess(result.surviving_average_propensity[-1], result.surviving_average_propensity[0])
        self.assertGreater(result.naive_overprediction_fraction, 0)

    def test_homogeneous_pool_matches_naive_forecast(self):
        result = forecast_burnout_prepayment(
            cohort_size=1000, base_monthly_prepayment_rates=[.02] * 24,
            propensity_multipliers=[1], initial_class_weights=[1], monthly_default_rates=.001,
        )
        self.assertAlmostEqual(result.cumulative_prepayments, result.naive_homogeneous_cumulative_prepayments)
        self.assertAlmostEqual(result.naive_overprediction_fraction, 0)

    def test_mass_is_conserved_with_competing_defaults(self):
        result = forecast_burnout_prepayment(
            cohort_size=500, base_monthly_prepayment_rates=[.02] * 12,
            propensity_multipliers=[.5, 2], initial_class_weights=[.7, .3], monthly_default_rates=.01,
        )
        final_active = result.active_loans[-1]
        self.assertAlmostEqual(final_active + result.cumulative_prepayments + result.cumulative_defaults, 500)

    def test_impossible_class_rate_is_rejected(self):
        with self.assertRaises(ValueError):
            forecast_burnout_prepayment(
                cohort_size=10, base_monthly_prepayment_rates=[.6],
                propensity_multipliers=[2], initial_class_weights=[1], monthly_default_rates=0,
            )


if __name__ == "__main__":
    unittest.main()
