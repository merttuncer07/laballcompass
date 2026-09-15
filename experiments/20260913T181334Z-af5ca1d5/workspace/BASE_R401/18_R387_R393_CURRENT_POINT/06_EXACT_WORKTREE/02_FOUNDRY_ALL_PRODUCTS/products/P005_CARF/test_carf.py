import unittest
import numpy as np
if __package__:
    from .carf import Requirement, route_requirement, audit_action_reduction_for_causal_target, compare_linear_reductions, certify_markov_dynamics, certify_decision_compression
else:
    from carf import Requirement, route_requirement, audit_action_reduction_for_causal_target, compare_linear_reductions, certify_markov_dynamics, certify_decision_compression
if __package__:
    from .parents.tsrc import FeatureSpec
else:
    from parents.tsrc import FeatureSpec

class CARFTests(unittest.TestCase):
    def test_all_requirements_route_to_distinct_certificate_families(self):
        expected={
            Requirement.FULL_IO_BEHAVIOR:("CORMA","BRED"), Requirement.TARGET_OUTPUT_TRAJECTORY:("CORMA","TWMR"),
            Requirement.THRESHOLD_ACTION:("TSRC",), Requirement.CAUSAL_TARGET:("OTE",), Requirement.MARKOV_CLOSED_DYNAMICS:("SALC",),
            Requirement.DECISION_REGRET:("DSBC",), Requirement.OBSERVABLE_PREDICTIVE_DYNAMICS:("PSCT",),
        }
        for req,products in expected.items(): self.assertEqual(route_requirement(req).products,products)

    def test_action_safe_feature_deletion_can_be_causally_unsafe(self):
        rng=np.random.default_rng(20260825); n=5000
        x=4+rng.normal(0,.4,n); z=rng.normal(0,1,n)
        d=.8*z+rng.normal(0,1,n); y=2*d+3*z+rng.normal(0,1,n)
        values=np.column_stack([x,z])
        features=[FeatureSpec('decision_signal',1.0,5.0,1.0),FeatureSpec('confounder',0.0,5.0,10.0)]
        result=audit_action_reduction_for_causal_target(values,d,y,features,baselines=[4,0],reserve=.1)
        self.assertEqual(result.action_certificate.deleted_features,('confounder',))
        self.assertEqual(result.action_certificate.observed_action_changes,0)
        self.assertTrue(result.certificate_adequate_for_action)
        self.assertFalse(result.certificate_adequate_for_causal_target)
        self.assertLess(abs(result.full_causal_estimate.target-2.0),.08)
        self.assertGreater(abs(result.causal_target_drift),1.2)
        self.assertGreater(result.causal_drift_in_full_standard_errors,50)

    def test_linear_router_keeps_global_and_target_certificates_separate(self):
        a=np.diag([.9,.6,.2]); b=np.array([[1.0],[.3],[.2]])
        c_all=np.array([[1.0,0,0],[0,0,8.0]])
        c_target=np.array([[1.0,0,0]])
        result=compare_linear_reductions(a,b,c_all,c_target,error_budget=10.0,retain_count=1,horizon=20)
        self.assertTrue(result.audit.stable)
        self.assertEqual(result.target_weighted.retained_states,('state_0',))
        self.assertEqual(result.status,'GLOBAL_AND_TARGET_REDUCTIONS_COMPARED_WITH_DISTINCT_CERTIFICATES')

    def test_dynamic_and_decision_certificates_are_not_synonyms(self):
        p=np.array([[.8,.1,.1,0],[.1,.8,0,.1],[.2,0,.7,.1],[0,.2,.1,.7]])
        salc=certify_markov_dynamics(p,['A','A','B','B'],horizon=5)
        beliefs=np.array([[.9,.1],[.8,.2],[.2,.8],[.1,.9]])
        utilities=np.array([[1,0],[0,1]])
        dsbc=certify_decision_compression(beliefs,utilities,maximum_regret=.25)
        self.assertIn(salc.status,{'EXACT_LUMPABILITY_CERTIFIED','APPROXIMATE_WITH_QUANTIFIED_ERROR','DECLARED_ERROR_BUDGET_EXCEEDED'})
        self.assertEqual(dsbc.status,'DECISION_SUFFICIENT_BELIEF_COMPRESSION_CERTIFIED')
        self.assertNotEqual(route_requirement(Requirement.MARKOV_CLOSED_DYNAMICS).certificate_kind,route_requirement(Requirement.DECISION_REGRET).certificate_kind)

if __name__=='__main__': unittest.main()
