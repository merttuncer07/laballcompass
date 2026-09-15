import unittest
import numpy as np
from reicapl import learn_relational_evidence_constrained_policy, _heterogeneous_capped_simplex

POSTERIOR = {'A': .9725, 'B': .02649, 'C': .02649}
CONSEQUENCE = {'A': 1.7464, 'B': 132.212, 'C': .6021}
COST = {'A': 1., 'B': 1., 'C': 1.}
ALIGN = {'A': 'asset_A', 'B': 'asset_B', 'C': 'asset_C'}
ASSETS = ('asset_A', 'asset_B', 'asset_C')


def data(seed=0, adverse_shift=-.015):
    rng = np.random.default_rng(seed)
    x_train = rng.normal(size=(100, 2))
    x_val = rng.normal(size=(160, 2))
    train_returns = np.column_stack((
        .002 + .012*x_train[:, 0] + rng.normal(scale=.004, size=len(x_train)),
        .003 + .020*x_train[:, 1] + rng.normal(scale=.004, size=len(x_train)),
        .001 - .006*x_train[:, 0] + .006*x_train[:, 1] + rng.normal(scale=.004, size=len(x_train)),
    ))
    val_returns = np.column_stack((
        .002 + .012*x_val[:, 0] + rng.normal(scale=.005, size=len(x_val)),
        .003 + .020*x_val[:, 1] + adverse_shift + rng.normal(scale=.005, size=len(x_val)),
        .001 - .006*x_val[:, 0] + .006*x_val[:, 1] + rng.normal(scale=.005, size=len(x_val)),
    ))
    return x_train, train_returns, x_val, val_returns


def case(seed=0, adverse_shift=-.015, budget=1., base_cap=.8, protected_cap=.34, alignment=None):
    return learn_relational_evidence_constrained_policy(
        *data(seed, adverse_shift), posterior_culprit=POSTERIOR,
        empirical_consequence=CONSEQUENCE, safeguard_cost=COST,
        record_to_asset=ALIGN if alignment is None else alignment, asset_names=ASSETS,
        safeguard_budget=budget, base_asset_cap=base_cap, protected_asset_cap=protected_cap,
        maximum_turnover=.8, risk_aversion=2., transaction_cost=.0004,
        population_size=24, generations=6, seed=4,
    )


class REICAPLTests(unittest.TestCase):
    def test_reis_consequence_selection_differs_from_posterior_only(self):
        r = case(); self.assertEqual(r.selected_safeguards, ('B',)); self.assertEqual(r.posterior_only_safeguards, ('A',))
    def test_reis_changes_asset_specific_feasible_caps(self):
        r = case(); self.assertEqual(r.candidate_asset_caps, (.8, .34, .8)); self.assertEqual(r.control_asset_caps, (.8, .8, .8))
    def test_working_region_beats_mechanism_removed_control(self): self.assertGreater(case().gain_vs_removed_mechanism, 0)
    def test_working_region_beats_posterior_only_ablation(self): self.assertGreater(case().gain_vs_posterior_only, 0)
    def test_candidate_constraints_are_certified(self):
        a=case().candidate_audit; self.assertEqual((a.sum_violations,a.lower_bound_violations,a.cap_violations,a.turnover_violations),(0,0,0,0))
    def test_control_constraints_are_certified(self):
        a=case().control_audit; self.assertEqual((a.sum_violations,a.lower_bound_violations,a.cap_violations,a.turnover_violations),(0,0,0,0))
    def test_zero_budget_collapses_exactly_to_control(self):
        r=case(budget=0); self.assertEqual(r.candidate_asset_caps,r.control_asset_caps); self.assertAlmostEqual(r.gain_vs_removed_mechanism,0.,places=14); self.assertEqual(r.candidate_validation_weights,r.control_validation_weights)
    def test_protected_cap_equal_base_collapses_exactly_to_control(self):
        r=case(protected_cap=.8); self.assertEqual(r.candidate_asset_caps,r.control_asset_caps); self.assertAlmostEqual(r.gain_vs_removed_mechanism,0.,places=14); self.assertEqual(r.candidate_validation_weights,r.control_validation_weights)
    def test_missing_record_asset_alignment_fails_closed(self):
        bad={'A':'asset_A','B':'asset_B'}
        with self.assertRaises(ValueError): case(alignment=bad)
    def test_unknown_mapped_asset_fails_closed(self):
        bad=dict(ALIGN); bad['B']='not_an_asset'
        with self.assertRaises(ValueError): case(alignment=bad)
    def test_infeasible_protected_cap_is_rejected(self):
        with self.assertRaises(ValueError): case(protected_cap=.2)
    def test_heterogeneous_projection_respects_each_cap(self):
        w=_heterogeneous_capped_simplex(np.array([.05,.9,.05]),np.array([.8,.34,.8])); self.assertAlmostEqual(w.sum(),1.); self.assertLessEqual(w[1],.34+1e-12)

if __name__ == '__main__': unittest.main()
