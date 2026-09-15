import unittest
import math
import numpy as np

from ebc import HistoricalEstimate, borrow_evidence, review_identity


class EBCTests(unittest.TestCase):
    def test_review_separates_assumed_independence_from_declared_identity(self):
        result=review_identity({'current_estimate':0,'current_standard_error':1,'historical':[
            {'name':str(i),'estimate':1,'standard_error':1,'observation_id':'same'} for i in range(5)]})
        self.assertLess(result['identity_preserved']['posterior_estimate'],.6)
        self.assertGreater(result['independence_assumed']['posterior_estimate'],.6)
        self.assertGreater(result['estimate_shift_from_counting_aliases'],0)
    def test_compatible_history_reduces_uncertainty(self) -> None:
        result = borrow_evidence(
            1.0, 0.3, [HistoricalEstimate("old", 1.05, 0.2)], borrowing_cap_ratio=3.0
        )
        self.assertLess(result.posterior_standard_error, 0.3)
        self.assertGreater(result.contributions[0].final_power, 0.9)

    def test_conflicting_precise_history_is_downweighted(self) -> None:
        result = borrow_evidence(
            0.0, 0.2, [HistoricalEstimate("conflict", 3.0, 0.05)], compatibility_scale=1.0
        )
        self.assertLess(result.contributions[0].final_power, 1e-10)
        self.assertAlmostEqual(result.posterior_estimate, 0.0, places=6)

    def test_total_borrowed_precision_obeys_cap(self) -> None:
        history = [HistoricalEstimate(str(i), 1.0, 0.01) for i in range(5)]
        result = borrow_evidence(1.0, 0.5, history, borrowing_cap_ratio=1.5)
        self.assertLessEqual(result.borrowing_precision_ratio, 1.5 + 1e-12)
        self.assertLess(result.cap_scale, 1.0)

    def test_zero_cap_equals_current_only(self) -> None:
        result = borrow_evidence(
            2.0, 0.4, [HistoricalEstimate("old", 1.0, 0.1)], borrowing_cap_ratio=0.0
        )
        self.assertAlmostEqual(result.posterior_estimate, 2.0)
        self.assertAlmostEqual(result.posterior_standard_error, 0.4)

    def test_declared_copies_do_not_shift_estimate_or_shrink_uncertainty(self):
        one = borrow_evidence(0,1,[HistoricalEstimate('original',1,1,observation_id='study:estimate')])
        copied = borrow_evidence(0,1,[HistoricalEstimate(str(i),1,1,observation_id='study:estimate') for i in range(100)])
        self.assertEqual(one.posterior_estimate,copied.posterior_estimate)
        self.assertEqual(one.posterior_standard_error,copied.posterior_standard_error)
        self.assertEqual(copied.distinct_historical_observations,1)
        self.assertEqual(copied.duplicate_history_count,99)
        self.assertEqual(sum(c.borrowed_precision>0 for c in copied.contributions),1)
        power=math.exp(-1/9)
        self.assertAlmostEqual(copied.posterior_estimate,power/(1+power))
        self.assertAlmostEqual(copied.posterior_standard_error,1/math.sqrt(1+power))

    def test_matches_gls_reference_for_perfectly_repeated_estimates(self):
        # A separate covariance calculation: perfect within-observation
        # correlation, independent groups, EBC powers held fixed.
        history=[HistoricalEstimate('a'+str(i),1,2,observation_id='a') for i in range(3)]
        history += [HistoricalEstimate('b'+str(i),-1,1.5,observation_id='b') for i in range(2)]
        values=np.array([h.estimate for h in history])
        covariance=np.zeros((5,5))
        for i,h in enumerate(history):
            power=math.exp(-.5*((h.estimate/math.sqrt(h.standard_error**2+1))/1.5)**2)
            for j,k in enumerate(history):
                if h.observation_id==k.observation_id:covariance[i,j]=h.standard_error**2/power
        precision=np.linalg.pinv(covariance);ones=np.ones(5)
        total=1+ones@precision@ones
        result=borrow_evidence(0,1,history,borrowing_cap_ratio=100)
        self.assertAlmostEqual(result.posterior_estimate,(ones@precision@values)/total)
        self.assertAlmostEqual(result.posterior_standard_error,1/math.sqrt(total))

    def test_equal_values_alone_do_not_establish_duplicate_identity(self):
        one=borrow_evidence(0,1,[HistoricalEstimate('a',1,1)])
        distinct=borrow_evidence(0,1,[HistoricalEstimate('a',1,1),HistoricalEstimate('b',1,1)])
        self.assertGreater(distinct.posterior_estimate,one.posterior_estimate)
        self.assertEqual(distinct.duplicate_history_count,0)

    def test_current_observation_cannot_be_borrowed_again(self):
        result=borrow_evidence(2,.4,[HistoricalEstimate('copy',2,.4,observation_id='current')],current_observation_id='current')
        self.assertEqual(result.posterior_estimate,2)
        self.assertAlmostEqual(result.posterior_standard_error,.4)
        self.assertEqual(result.borrowed_precision,0)
        self.assertEqual(result.current_overlap_count,1)

    def test_conflicting_values_under_one_identity_require_joint_model(self):
        with self.assertRaisesRegex(ValueError,'covariance'):
            borrow_evidence(0,1,[HistoricalEstimate('a',1,1,observation_id='x'),HistoricalEstimate('b',2,1,observation_id='x')])
        with self.assertRaisesRegex(ValueError,'conflicts'):
            borrow_evidence(0,1,[HistoricalEstimate('a',1,1,observation_id='x')],current_observation_id='x')

    def test_duplicate_power_policy_is_max_not_sum_and_order_invariant(self):
        history=[HistoricalEstimate('a',1,1,.2,'x'),HistoricalEstimate('b',1,1,.6,'x')]
        a=borrow_evidence(0,1,history);b=borrow_evidence(0,1,list(reversed(history)))
        once=borrow_evidence(0,1,[history[1]])
        self.assertEqual(a.posterior_estimate,b.posterior_estimate)
        self.assertEqual(a.posterior_estimate,once.posterior_estimate)
        self.assertEqual(a.contributions[0].counted_as,'b')


if __name__ == "__main__":
    unittest.main()
