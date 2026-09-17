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

    def test_class_stocks_survive_cure_in_competing_risk_baseline(self):
        rates = MonthlyTransitionRates(0.2, 0.0, 0.1, 0.0, 0.0, 0.5)
        result = simulate_burnout_aware_intervention(
            cohort_size=100, base_monthly_prepayment_rates=[0.2, 0.2], propensity_multipliers=[0.0, 2.0],
            initial_class_weights=[0.5, 0.5], baseline_rates=rates, intervention=Intervention(),
            balance_per_loan=1.0, recovery_fraction=0.0,
        )
        states = result.burnout_aware.baseline.monthly_states
        self.assertEqual(states, ((100.0, 0.0, 0.0, 0.0), (50.0, 10.0, 20.0, 20.0), (34.0, 10.0, 30.0, 26.0)))

    def test_delinquent_pool_keeps_class_propensity_for_prepayment(self):
        rates = MonthlyTransitionRates(0.0, 0.0, 0.5, 0.0, 0.4, 0.0)
        result = simulate_burnout_aware_intervention(
            cohort_size=100, base_monthly_prepayment_rates=[0.2], propensity_multipliers=[0.0, 1.0],
            initial_class_weights=[0.5, 0.5], baseline_rates=rates, intervention=Intervention(),
            balance_per_loan=1.0, recovery_fraction=0.0,
        )
        states = result.burnout_aware.baseline.monthly_states
        self.assertEqual(states, ((100.0, 0.0, 0.0, 0.0), (40.0, 50.0, 0.0, 10.0)))

    def test_intervention_applies_competing_risk_multipliers_per_class(self):
        rates = MonthlyTransitionRates(0.2, 0.2, 0.1, 0.5, 0.0, 0.1)
        intervention = Intervention(
            performing_default_multiplier=0.5, performing_prepay_multiplier=0.5,
            performing_delinquency_multiplier=1.0, delinquent_default_multiplier=0.4,
            delinquent_cure_multiplier=2.0, one_time_cost_per_loan=10.0,
        )
        result = simulate_burnout_aware_intervention(
            cohort_size=100, base_monthly_prepayment_rates=[0.2], propensity_multipliers=[1.0],
            initial_class_weights=[1.0], baseline_rates=rates, intervention=intervention,
            balance_per_loan=1.0, recovery_fraction=0.0,
        )
        states = result.burnout_aware.intervention.monthly_states
        self.assertEqual(states, ((100.0, 0.0, 0.0, 0.0), (70.0, 10.0, 10.0, 10.0)))
        self.assertEqual(result.burnout_aware.baseline.monthly_states, ((100.0, 0.0, 0.0, 0.0), (50.0, 10.0, 20.0, 20.0)))

    def test_homogeneous_reduction_matches_parent_mcris_with_zero_default_hazard(self):
        result = simulate_burnout_aware_intervention(
            cohort_size=1000, base_monthly_prepayment_rates=np.full(12, 0.02), propensity_multipliers=[1.0],
            initial_class_weights=[1.0],
            baseline_rates=MonthlyTransitionRates(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), intervention=Intervention(),
            balance_per_loan=1000, recovery_fraction=0.5,
        )
        self.assertAlmostEqual(
            result.burnout_forecast.cumulative_prepayments,
            result.homogeneous_parent.baseline.cumulative_prepay, places=6,
        )

    def test_competing_exits_change_burnout_composition_vs_zero_default_forecast(self):
        rates = MonthlyTransitionRates(0.2, 0.0, 0.0, 0.0, 0.0, 0.0)
        result = simulate_burnout_aware_intervention(
            cohort_size=100, base_monthly_prepayment_rates=[0.2, 0.2], propensity_multipliers=[0.0, 2.0],
            initial_class_weights=[0.5, 0.5], baseline_rates=rates, intervention=Intervention(),
            balance_per_loan=1.0, recovery_fraction=0.0,
        )
        self.assertAlmostEqual(result.burnout_forecast.cumulative_prepayments, 32.0, places=10)
        self.assertAlmostEqual(result.burnout_aware.baseline.cumulative_prepay, 28.0, places=10)

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

    def test_class_paths_match_independent_transition_matrix_oracle(self):
        # A separate four-state Markov calculation, including cure and
        # time-varying hazards. These are software cases, not mortgage data.
        rng = np.random.default_rng(717)
        rates = MonthlyTransitionRates(.04, .02, .08, .07, .03, .12)
        intervention = Intervention(performing_default_multiplier=.7,
            performing_prepay_multiplier=1.4, performing_delinquency_multiplier=.9,
            delinquent_default_multiplier=.8, delinquent_cure_multiplier=1.2)
        for _ in range(40):
            weights = rng.dirichlet([1, 1, 1])
            props = rng.uniform(.1, 2, 3)
            base = rng.uniform(.01, .12, 12)
            result = simulate_burnout_aware_intervention(cohort_size=1000,
                base_monthly_prepayment_rates=base, propensity_multipliers=props,
                initial_class_weights=weights, baseline_rates=rates,
                intervention=intervention, balance_per_loan=100, recovery_fraction=.4)
            for scenario, change in [(result.burnout_aware.baseline, Intervention()),
                                     (result.burnout_aware.intervention, intervention)]:
                expected = np.zeros((13, 4))
                for weight, propensity in zip(weights, props):
                    state = np.array([1000*weight, 0, 0, 0])
                    expected[0] += state
                    for t, rate in enumerate(base):
                        pd = .04*change.performing_default_multiplier
                        pp = rate*propensity*change.performing_prepay_multiplier
                        dl = .08*change.performing_delinquency_multiplier
                        dd = .07*change.delinquent_default_multiplier
                        dp = .03*change.delinquent_prepay_multiplier
                        dc = .12*change.delinquent_cure_multiplier
                        matrix = np.array([[1-pd-pp-dl, dl, pd, pp],
                            [dc, 1-dc-dd-dp, dd, dp], [0, 0, 1, 0], [0, 0, 0, 1]])
                        state = state @ matrix
                        expected[t+1] += state
                np.testing.assert_allclose(scenario.monthly_states, expected, rtol=0, atol=1e-10)

    def test_invalid_competing_hazard_is_rejected(self):
        bad_rates = MonthlyTransitionRates(0.8, 0.0, 0.4, 0.05, 0.005, 0.2)
        with self.assertRaises(ValueError):
            simulate_burnout_aware_intervention(
                cohort_size=100, base_monthly_prepayment_rates=[0.1], propensity_multipliers=[1], initial_class_weights=[1],
                baseline_rates=bad_rates, intervention=Intervention(), balance_per_loan=100000, recovery_fraction=0.5,
            )


if __name__ == '__main__': unittest.main()
