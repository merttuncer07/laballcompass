import functools, importlib.util, pathlib, sys, unittest
import numpy as np
from scig import support_covariance_independence_guard

ROOT=pathlib.Path(__file__).resolve().parents[3]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m

SACPS=load('sacps_v2p050',ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R037_SUPPORT_COVARIANCE_SACPS/sacps.py')
CSID=load('csid_v2p050',ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM445_IM085_CSID/csid.py')
FAIL=[CSID.FailureMode('reporting_failure',.5,100.)]
SAFE=[
    CSID.Safeguard('A',5.,'feed_A',{'reporting_failure':.6}),
    CSID.Safeguard('B',5.,'feed_B',{'reporting_failure':.6}),
    CSID.Safeguard('C',7.,'governance',{'reporting_failure':.5}),
]

def evidence(correlated=True, seed=7, n=160, rho=.92):
    rng=np.random.default_rng(seed)
    z=rng.normal(size=n)
    if correlated:
        b=rho*z+np.sqrt(max(0.0,1-rho**2))*rng.normal(size=z.size)
    else:
        b=rng.normal(size=z.size)
    return np.column_stack((z,b,rng.normal(size=z.size)))

@functools.lru_cache(maxsize=None)
def case(correlated=True):
    support=np.eye(3,dtype=bool)
    if correlated:
        support[0,1]=support[1,0]=True
    return support_covariance_independence_guard(
        CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,evidence(correlated),support,
        budget=12.,correlation_threshold=.6,ambiguity_band=.05,shrinkage_grid=[0.]
    )

class T(unittest.TestCase):
    def test_covariance_merges_nominally_distinct_families(self):
        r=case(True)
        self.assertTrue(r['merged_cross_family'])
        self.assertEqual(r['dependence_adjusted_family_map']['A'],r['dependence_adjusted_family_map']['B'])

    def test_portfolio_changes(self):
        r=case(True)
        self.assertEqual(tuple(r['control_declared_partition']['selected']['safeguards']),('A','B'))
        self.assertNotEqual(tuple(r['candidate_dependence_adjusted_partition']['selected']['safeguards']),('A','B'))

    def test_candidate_beats_removal_control_under_adjusted_reality(self):
        self.assertGreater(case(True)['gain_vs_declared_family_removal_control_under_adjusted_reality'],5.)

    def test_candidate_does_not_exhaust_budget_blindly(self):
        self.assertLessEqual(case(True)['candidate_dependence_adjusted_partition']['selected']['total_cost'],12.)

    def test_no_supported_cross_family_edge_collapses(self):
        r=case(False)
        self.assertFalse(r['merged_cross_family'])
        self.assertEqual(r['status'],'SUPPORT_COVARIANCE_COLLAPSED_TO_DECLARED_FAMILIES')
        self.assertEqual(r['candidate_dependence_adjusted_partition']['selected']['safeguards'],r['control_declared_partition']['selected']['safeguards'])

    def test_strong_raw_dependence_without_declared_support_does_not_merge(self):
        s=np.eye(3,dtype=bool)
        r=support_covariance_independence_guard(
            CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,evidence(True,seed=17,n=400,rho=.95),s,
            budget=12.,correlation_threshold=.6,ambiguity_band=.05,shrinkage_grid=[0.]
        )
        self.assertFalse(r['merged_cross_family'])
        self.assertEqual(r['status'],'SUPPORT_COVARIANCE_COLLAPSED_TO_DECLARED_FAMILIES')

    def test_supported_but_clearly_weak_dependence_collapses(self):
        s=np.eye(3,dtype=bool); s[0,1]=s[1,0]=True
        r=support_covariance_independence_guard(
            CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,evidence(True,seed=19,n=1200,rho=.2),s,
            budget=12.,correlation_threshold=.6,ambiguity_band=.05,shrinkage_grid=[0.]
        )
        self.assertFalse(r['merged_cross_family'])
        self.assertEqual(r['status'],'SUPPORT_COVARIANCE_COLLAPSED_TO_DECLARED_FAMILIES')

    def test_already_declared_common_family_collapses_to_parent_semantics(self):
        safeguards=[
            CSID.Safeguard('A',5.,'shared_feed',{'reporting_failure':.6}),
            CSID.Safeguard('B',5.,'shared_feed',{'reporting_failure':.6}),
            CSID.Safeguard('C',7.,'governance',{'reporting_failure':.5}),
        ]
        s=np.eye(3,dtype=bool); s[0,1]=s[1,0]=True
        r=support_covariance_independence_guard(
            CSID,SACPS.estimate_support_aware_covariance,FAIL,safeguards,evidence(True,seed=23,n=400,rho=.95),s,
            budget=12.,correlation_threshold=.6,ambiguity_band=.05,shrinkage_grid=[0.]
        )
        self.assertFalse(r['merged_cross_family'])
        self.assertEqual(r['status'],'SUPPORT_COVARIANCE_COLLAPSED_TO_DECLARED_FAMILIES')
        self.assertEqual(r['candidate_dependence_adjusted_partition']['selected']['safeguards'],r['control_declared_partition']['selected']['safeguards'])
        self.assertAlmostEqual(r['gain_vs_declared_family_removal_control_under_adjusted_reality'],0.0,places=12)

    def test_ambiguous_dependence_abstains(self):
        rng=np.random.default_rng(4)
        z=rng.normal(size=300)
        b=.6*z+.8*rng.normal(size=300)
        e=np.column_stack((z,b,rng.normal(size=300)))
        s=np.eye(3,dtype=bool); s[0,1]=s[1,0]=True
        r=support_covariance_independence_guard(
            CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,e,s,
            budget=12.,correlation_threshold=.6,ambiguity_band=.12,shrinkage_grid=[0.]
        )
        self.assertEqual(r['status'],'ABSTAIN_DEPENDENCE_THRESHOLD_AMBIGUOUS')

    def test_permutation_preserves_selected_safeguard_set(self):
        base=case(True)
        perm=[2,0,1]
        saf=[SAFE[i] for i in perm]
        e=evidence(True)[:,perm]
        s=np.eye(3,dtype=bool); s[1,2]=s[2,1]=True
        r=support_covariance_independence_guard(
            CSID,SACPS.estimate_support_aware_covariance,FAIL,saf,e,s,
            budget=12.,correlation_threshold=.6,ambiguity_band=.05,shrinkage_grid=[0.]
        )
        self.assertEqual(set(r['candidate_dependence_adjusted_partition']['selected']['safeguards']),set(base['candidate_dependence_adjusted_partition']['selected']['safeguards']))
        self.assertAlmostEqual(r['gain_vs_declared_family_removal_control_under_adjusted_reality'],base['gain_vs_declared_family_removal_control_under_adjusted_reality'],places=12)

    def test_bad_dimension_rejected(self):
        with self.assertRaises(ValueError):
            support_covariance_independence_guard(CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,evidence()[:,:2],np.eye(2,dtype=bool),budget=12.)

    def test_bad_support_mask_rejected(self):
        bad=np.eye(3,dtype=bool); bad[0,1]=True
        with self.assertRaises(ValueError):
            support_covariance_independence_guard(CSID,SACPS.estimate_support_aware_covariance,FAIL,SAFE,evidence(),bad,budget=12.)

    def test_deterministic(self):
        self.assertEqual(case(True),case(True))

if __name__=='__main__': unittest.main()
