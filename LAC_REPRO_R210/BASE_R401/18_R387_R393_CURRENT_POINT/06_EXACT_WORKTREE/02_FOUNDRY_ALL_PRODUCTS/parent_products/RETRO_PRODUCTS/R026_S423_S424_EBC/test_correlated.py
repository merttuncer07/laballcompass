import unittest
import numpy as np
from ebc import HistoricalEstimate, borrow_evidence, borrow_correlated_evidence, source_covariance, review_covariance


class CorrelatedEvidenceTests(unittest.TestCase):
    def test_diagonal_joint_model_matches_existing_ebc(self):
        history=[HistoricalEstimate('a',1,.6,.8),HistoricalEstimate('b',-.4,1.3)]
        kwargs=dict(compatibility_scale=1.2,borrowing_cap_ratio=.8)
        old=borrow_evidence(.1,.9,history,**kwargs)
        new=borrow_correlated_evidence(.1,.9,history,covariance=np.diag([.9**2,.6**2,1.3**2]),covariance_names=['current','a','b'],**kwargs)
        self.assertAlmostEqual(old.posterior_estimate,new.posterior_estimate)
        self.assertAlmostEqual(old.posterior_standard_error,new.posterior_standard_error)
        self.assertAlmostEqual(old.borrowed_precision,new.borrowed_precision)

    def test_unit_powers_match_separate_whitened_least_squares_reference(self):
        rng=np.random.default_rng(921)
        for _ in range(10):
            a=rng.normal(size=(5,5));cov=a@a.T+np.eye(5);values=rng.normal(size=5)
            history=[HistoricalEstimate(str(i),values[i],np.sqrt(cov[i,i])) for i in range(1,5)]
            result=borrow_correlated_evidence(values[0],np.sqrt(cov[0,0]),history,covariance=cov,covariance_names=['current','1','2','3','4'],adaptive=False,borrowing_cap_ratio=1e6)
            root=np.linalg.cholesky(cov);design=np.linalg.solve(root,np.ones((5,1)));target=np.linalg.solve(root,values)
            estimate=np.linalg.lstsq(design,target,rcond=None)[0][0]
            self.assertAlmostEqual(result.posterior_estimate,estimate)
            self.assertAlmostEqual(result.posterior_standard_error,1/np.linalg.norm(design))
            self.assertAlmostEqual(sum(result.linear_weights),1)

    def test_shared_noise_does_not_look_like_three_independent_measurements(self):
        cov=.8*np.ones((3,3))+.2*np.eye(3)
        result=borrow_correlated_evidence(1,1,[HistoricalEstimate('a',1,1),HistoricalEstimate('b',1,1)],covariance=cov,covariance_names=['current','a','b'])
        self.assertAlmostEqual(result.posterior_standard_error,np.sqrt((1+2*.8)/3))
        self.assertGreater(result.posterior_standard_error,1/np.sqrt(3))

    def test_exact_alias_invariance_with_partial_cross_source_covariance(self):
        base=np.array([[1,.3,.2],[.3,1,.4],[.2,.4,1]])
        history=[HistoricalEstimate('a',.4,1,observation_id='A'),HistoricalEstimate('b',.8,1,observation_id='B')]
        original=borrow_correlated_evidence(0,1,history,covariance=base,covariance_names=['current','a','b'])
        expanded=base[np.ix_([0,1,2,1],[0,1,2,1])]
        copied=borrow_correlated_evidence(0,1,history+[HistoricalEstimate('a_copy',.4,1,observation_id='A')],covariance=expanded,covariance_names=['current','a','b','a_copy'])
        self.assertEqual(original.posterior_estimate,copied.posterior_estimate)
        self.assertEqual(original.posterior_standard_error,copied.posterior_standard_error)

    def test_current_alias_is_removed_before_conditional_solve(self):
        result=borrow_correlated_evidence(1,1,[HistoricalEstimate('copy',1,1,observation_id='C')],covariance=np.ones((2,2)),covariance_names=['current','copy'],current_observation_id='C')
        self.assertEqual(result.posterior_estimate,1)
        self.assertEqual(result.posterior_standard_error,1)
        self.assertEqual(result.retained_names,('current',))

    def test_invalid_covariance_and_identity_are_explained(self):
        h=[HistoricalEstimate('a',0,1)]
        for cov in ([[1,2],[2,1]],[[1,.2],[.1,1]],[[1,0],[0,2]],[[1,1],[1,1]]):
            with self.assertRaises(ValueError):borrow_correlated_evidence(0,1,h,covariance=cov,covariance_names=['current','a'])
        with self.assertRaisesRegex(ValueError,'order'):
            borrow_correlated_evidence(0,1,h,covariance=np.eye(2),covariance_names=['a','current'])
        with self.assertRaisesRegex(ValueError,'identical covariance rows'):
            borrow_correlated_evidence(0,1,[HistoricalEstimate('copy',0,1,observation_id='C')],covariance=np.eye(2),covariance_names=['current','copy'],current_observation_id='C')

    def test_negative_linear_weights_are_retained_not_clipped(self):
        result=borrow_correlated_evidence(1,1,[HistoricalEstimate('a',2,2)],covariance=[[1,1.8],[1.8,4]],covariance_names=['current','a'],adaptive=False,borrowing_cap_ratio=1e6)
        self.assertLess(result.linear_weights[1],0)
        self.assertAlmostEqual(sum(result.linear_weights),1)

    def test_zero_cap_or_zero_power_returns_current_only(self):
        for power,cap in [(0,2),(1,0)]:
            result=borrow_correlated_evidence(1,1,[HistoricalEstimate('a',2,1,power)],covariance=[[1,.5],[.5,1]],covariance_names=['current','a'],borrowing_cap_ratio=cap)
            self.assertEqual(result.posterior_estimate,1)
            self.assertEqual(result.posterior_standard_error,1)

    def test_adaptive_conditional_likelihood_matches_scalar_closed_form(self):
        # Current variance 1, history variance 4, covariance .6.
        # Given current x, history has mean .6*x + .4*mu and variance 3.64.
        p=.7*np.exp(-.5*(1/np.sqrt(3.8)/1.5)**2)
        info=.4**2*p/3.64
        numerator=.4*p/3.64
        result=borrow_correlated_evidence(0,1,[HistoricalEstimate('a',1,2,.7)],covariance=[[1,.6],[.6,4]],covariance_names=['current','a'],borrowing_cap_ratio=10)
        self.assertAlmostEqual(result.posterior_estimate,numerator/(1+info))
        self.assertAlmostEqual(result.posterior_standard_error,np.sqrt(1/(1+info)))
        capped=borrow_correlated_evidence(0,1,[HistoricalEstimate('a',1,2,.7)],covariance=[[1,.6],[.6,4]],covariance_names=['current','a'],borrowing_cap_ratio=.01)
        self.assertLessEqual(capped.borrowing_precision_ratio,.01+1e-14)

    def test_joint_gls_does_not_depend_on_which_observation_is_current(self):
        cov=np.array([[1,.2,.4],[.2,2,.3],[.4,.3,3.]])
        values=np.array([.1,.7,1.4]);results=[]
        for order in ([0,1,2],[1,2,0],[2,0,1]):
            c=cov[np.ix_(order,order)];y=values[order]
            result=borrow_correlated_evidence(y[0],np.sqrt(c[0,0]),[HistoricalEstimate('a',y[1],np.sqrt(c[1,1])),HistoricalEstimate('b',y[2],np.sqrt(c[2,2]))],covariance=c,covariance_names=['current','a','b'],adaptive=False,borrowing_cap_ratio=100)
            results.append(result.posterior_estimate)
        self.assertTrue(np.allclose(results,results[0]))

    def test_linear_source_propagation_preserves_shared_noise_cancellation(self):
        source=np.diag([.2,.3,.4]);a=np.array([[1,0,-1],[0,1,-1]])
        cov=source_covariance(a,source)
        self.assertTrue(np.allclose(cov,[[.6,.4],[.4,.7]]))
        contrast=np.array([1,-1])
        self.assertAlmostEqual(contrast@cov@contrast,.2+.3)

    def test_covariance_review_uses_same_policy_and_marginal_variances(self):
        result=review_covariance({'current_estimate':1,'current_standard_error':1,'historical':[{'name':'a','estimate':1,'standard_error':1}],'covariance':[[1,.8],[.8,1]],'covariance_names':['current','a']})
        self.assertLess(result['se_change_if_covariance_ignored'],0)
        self.assertEqual(result['estimate_shift_if_covariance_ignored'],0)


if __name__=='__main__':unittest.main()
