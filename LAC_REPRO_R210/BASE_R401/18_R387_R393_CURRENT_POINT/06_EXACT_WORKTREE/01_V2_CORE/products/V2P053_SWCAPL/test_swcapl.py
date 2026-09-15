import unittest
import numpy as np
from swcapl import learn_support_weighted_policy


def data(seed=0, target_share=0.80):
    rng=np.random.default_rng(seed)
    n=80
    source_regime=np.array([0]*64+[1]*16); rng.shuffle(source_regime)
    x_train=np.zeros((n,1))
    r_train=np.empty((n,2))
    for i,g in enumerate(source_regime):
        mu=np.array([.030,.005]) if g==0 else np.array([.005,.040])
        r_train[i]=mu+rng.normal(0,.002,size=2)
    # Exact source->declared-target density ratios for 80/20 -> 20/80.
    importance=np.where(source_regime==0,.25,4.0)

    nv=100
    n1=int(round(nv*target_share)); target_regime=np.array([0]*(nv-n1)+[1]*n1); rng.shuffle(target_regime)
    x_val=np.zeros((nv,1)); r_val=np.empty((nv,2))
    for i,g in enumerate(target_regime):
        mu=np.array([.030,.005]) if g==0 else np.array([.005,.040])
        r_val[i]=mu+rng.normal(0,.002,size=2)
    return x_train,r_train,x_val,r_val,importance


def case(seed=0,target_share=.80,importance=None,fragile=.10):
    xtr,rtr,xv,rv,iw=data(seed,target_share)
    return learn_support_weighted_policy(
        xtr,rtr,xv,rv,target_importance_weights=iw if importance is None else importance,
        fragile_ess_fraction=fragile,maximum_asset_weight=.9,maximum_turnover=2.0,
        risk_aversion=0.,transaction_cost=0.,population_size=40,generations=12,
        elite_fraction=.2,seed=seed,
    )


class SWCAPLTests(unittest.TestCase):
    def test_support_gate_is_usable_in_declared_working_region(self):
        r=case(); self.assertEqual(r.support_status,'SUPPORT_USABLE'); self.assertGreater(r.effective_sample_fraction,.30)
    def test_target_weighting_changes_policy_actions(self):
        r=case(); self.assertNotEqual(r.candidate_validation_weights,r.control_validation_weights)
    def test_working_region_beats_mechanism_removed_control(self):
        self.assertGreater(case().target_validation_gain_vs_removed_mechanism,.01)
    def test_candidate_concentrates_on_target_favored_asset(self):
        r=case(); self.assertGreater(np.mean(np.asarray(r.candidate_validation_weights)[:,1]),.85)
    def test_control_concentrates_on_source_favored_asset(self):
        r=case(); self.assertGreater(np.mean(np.asarray(r.control_validation_weights)[:,0]),.85)
    def test_uniform_weights_collapse_exactly_to_control(self):
        xtr,rtr,xv,rv,_=data(); r=learn_support_weighted_policy(
            xtr,rtr,xv,rv,target_importance_weights=np.ones(len(xtr)),fragile_ess_fraction=.10,
            maximum_asset_weight=.9,maximum_turnover=2.,risk_aversion=0.,transaction_cost=0.,
            population_size=40,generations=12,elite_fraction=.2,seed=0)
        self.assertEqual(r.candidate_validation_weights,r.control_validation_weights)
        self.assertAlmostEqual(r.target_validation_gain_vs_removed_mechanism,0.,places=14)
        self.assertEqual(r.status,'TARGET_WEIGHTING_COLLAPSED_TO_CAPL_CONTROL')
    def test_fragile_importance_weights_fail_closed(self):
        xtr,_,_,_,_=data(); bad=np.zeros(len(xtr)); bad[0]=1.
        with self.assertRaises(ValueError): case(importance=bad,fragile=.10)
    def test_negative_importance_weight_rejected(self):
        _,_,_,_,iw=data(); iw=iw.copy(); iw[0]=-1
        with self.assertRaises(ValueError): case(importance=iw)
    def test_wrong_length_importance_weight_rejected(self):
        with self.assertRaises(ValueError): case(importance=np.ones(7))
    def test_candidate_action_constraints_are_certified(self):
        a=case().candidate_action_audit
        self.assertEqual((a['sum_violations'],a['lower_bound_violations'],a['upper_bound_violations'],a['turnover_violations']),(0,0,0,0))
    def test_control_action_constraints_are_certified(self):
        a=case().control_action_audit
        self.assertEqual((a['sum_violations'],a['lower_bound_violations'],a['upper_bound_violations'],a['turnover_violations']),(0,0,0,0))
    def test_source_like_validation_is_explicit_failure_region(self):
        self.assertLess(case(target_share=.20).target_validation_gain_vs_removed_mechanism,0.)

if __name__=='__main__': unittest.main()
