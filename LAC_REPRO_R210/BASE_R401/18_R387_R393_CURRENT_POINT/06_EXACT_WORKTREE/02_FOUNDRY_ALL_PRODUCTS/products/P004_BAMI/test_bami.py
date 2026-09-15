import math
import unittest
import numpy as np
if __package__:
    from .bami import borrow_default_multiplier, simulate_burnout_aware_intervention, explore_intervention_net_value_surface
else:
    from bami import borrow_default_multiplier, simulate_burnout_aware_intervention, explore_intervention_net_value_surface
if __package__:
    from .parents.ebc import HistoricalEstimate
else:
    from parents.ebc import HistoricalEstimate
if __package__:
    from .parents.mcris import Intervention, MonthlyTransitionRates, simulate_mortgage_intervention
else:
    from parents.mcris import Intervention, MonthlyTransitionRates, simulate_mortgage_intervention


class BAMITests(unittest.TestCase):
    def test_joint_covariance_survives_default_multiplier_adapter(self):
        histories=[HistoricalEstimate('a',0,1),HistoricalEstimate('b',0,1)]
        result=borrow_default_multiplier(0,1,histories,covariance=.8*np.ones((3,3))+.2*np.eye(3),covariance_names=['current','a','b'])
        self.assertAlmostEqual(result.borrowing.posterior_standard_error,np.sqrt(2.6/3))
        self.assertEqual(result.posterior_default_multiplier,1)

    def test_copying_one_effect_does_not_change_default_multiplier(self):
        one=borrow_default_multiplier(0,1,[HistoricalEstimate('a',-.5,1,observation_id='effect')])
        copies=borrow_default_multiplier(0,1,[HistoricalEstimate(str(i),-.5,1,observation_id='effect') for i in range(10)])
        self.assertEqual(one.posterior_default_multiplier,copies.posterior_default_multiplier)
        self.assertEqual(copies.borrowing.duplicate_history_count,9)

    def test_current_observation_identity_survives_bami_adapter(self):
        result=borrow_default_multiplier(-.5,1,[HistoricalEstimate('copy',-.5,1,observation_id='current')],current_observation_id='current')
        self.assertEqual(result.borrowing.borrowed_precision,0)

    def setUp(self):
        self.rates = MonthlyTransitionRates(0.002, 0.0, 0.01, 0.05, 0.005, 0.20)
        self.base = np.full(36, 0.025)
        self.multipliers = [0.25, 0.75, 1.5, 3.0]
        self.weights = [0.2, 0.3, 0.3, 0.2]
        self.intervention = Intervention(
            performing_default_multiplier=0.55, performing_delinquency_multiplier=0.9,
            delinquent_default_multiplier=0.55, delinquent_cure_multiplier=1.1,
            one_time_cost_per_loan=3150.0,
        )

    def test_constant_propensity_reduces_exactly_to_parent_mcris(self):
        base = np.full(12, 0.02)
        rates = MonthlyTransitionRates(0.002, 0.02, 0.01, 0.05, 0.005, 0.2)
        intervention = Intervention(performing_default_multiplier=0.8, delinquent_default_multiplier=0.8, one_time_cost_per_loan=50)
        result = simulate_burnout_aware_intervention(
            cohort_size=1000, base_monthly_prepayment_rates=base, propensity_multipliers=[1.0], initial_class_weights=[1.0],
            baseline_rates=rates, intervention=intervention, balance_per_loan=200000, recovery_fraction=0.5,
            prepayment_cost_fraction=0.001,
        )
        parent = simulate_mortgage_intervention(
            cohort_size=1000, horizon_months=12, baseline_rates=rates, intervention=intervention,
            balance_per_loan=200000, recovery_fraction=0.5, prepayment_cost_fraction=0.001,
        )
        self.assertAlmostEqual(result.burnout_aware.net_value, parent.net_value, places=6)
        self.assertAlmostEqual(result.burnout_aware.defaults_avoided, parent.defaults_avoided, places=9)

    def test_burnout_path_declines_and_changes_intervention_value(self):
        result = simulate_burnout_aware_intervention(
            cohort_size=100000, base_monthly_prepayment_rates=self.base, propensity_multipliers=self.multipliers,
            initial_class_weights=self.weights, baseline_rates=self.rates, intervention=self.intervention,
            balance_per_loan=250000, recovery_fraction=0.6, prepayment_cost_fraction=0.002,
        )
        path = result.burnout_forecast.effective_prepayment_rates
        self.assertGreater(path[0], path[-1])
        self.assertGreater(result.burnout_minus_homogeneous_defaults_avoided, 0)
        self.assertNotAlmostEqual(result.burnout_aware.net_value, result.homogeneous_parent.net_value)

    def test_burnout_can_flip_intervention_decision_relative_to_homogeneous_parent(self):
        # Put intervention cost inside the empirically established disagreement interval:
        # homogeneous gross benefit ~= $348.0M vs burnout-aware ~= $371.0M for 100k loans.
        # $3,650/loan therefore makes the homogeneous model reject while BAMI accepts.
        flip_intervention = Intervention(
            performing_default_multiplier=0.55, performing_delinquency_multiplier=0.9,
            delinquent_default_multiplier=0.55, delinquent_cure_multiplier=1.1,
            one_time_cost_per_loan=3650.0,
        )
        result = simulate_burnout_aware_intervention(
            cohort_size=100000, base_monthly_prepayment_rates=self.base, propensity_multipliers=self.multipliers,
            initial_class_weights=self.weights, baseline_rates=self.rates, intervention=flip_intervention,
            balance_per_loan=250000, recovery_fraction=0.6, prepayment_cost_fraction=0.002,
        )
        self.assertLess(result.homogeneous_parent.net_value, 0)
        self.assertGreater(result.burnout_aware.net_value, 0)

    def test_ebc_downweights_conflicting_historical_effect(self):
        effect = borrow_default_multiplier(
            math.log(0.55), 0.10,
            [HistoricalEstimate("similar", math.log(0.52), 0.08, 0.7), HistoricalEstimate("conflict", math.log(0.90), 0.05, 0.8)],
            borrowing_cap_ratio=1.0,
        )
        by_name = {item.name: item for item in effect.borrowing.contributions}
        self.assertLess(by_name["conflict"].final_power, by_name["similar"].final_power)
        self.assertGreater(effect.posterior_default_multiplier, 0)
        self.assertLess(effect.borrowing.borrowing_precision_ratio, 1.0000001)

    def test_tdsx_finds_net_value_flip(self):
        surface = explore_intervention_net_value_surface(
            cohort_size=20000, base_monthly_prepayment_rates=self.base, propensity_multipliers=self.multipliers,
            initial_class_weights=self.weights, baseline_rates=self.rates, intervention_template=self.intervention,
            balance_per_loan=250000, recovery_fraction=0.6,
            parameter_grids={
                "default_multiplier": [0.45, 0.55, 0.70, 0.85],
                "cost_per_loan": [2000, 3150, 4500, 6000],
                "prepayment_cost_fraction": [0.0, 0.002, 0.005],
            },
            baseline_parameters={"default_multiplier": 0.55, "cost_per_loan": 3150.0, "prepayment_cost_fraction": 0.002},
        )
        self.assertIsNotNone(surface.tipping_point)
        self.assertEqual(surface.status, "TIPPING_POINT_FOUND")
        self.assertGreater(surface.metric_maximum, 0)
        self.assertLess(surface.metric_minimum, 0)

    def test_invalid_competing_hazard_is_rejected(self):
        bad_rates = MonthlyTransitionRates(0.8, 0.0, 0.4, 0.05, 0.005, 0.2)
        with self.assertRaises(ValueError):
            simulate_burnout_aware_intervention(
                cohort_size=100, base_monthly_prepayment_rates=[0.1], propensity_multipliers=[1], initial_class_weights=[1],
                baseline_rates=bad_rates, intervention=Intervention(), balance_per_loan=100000, recovery_fraction=0.5,
            )


if __name__ == '__main__': unittest.main()
