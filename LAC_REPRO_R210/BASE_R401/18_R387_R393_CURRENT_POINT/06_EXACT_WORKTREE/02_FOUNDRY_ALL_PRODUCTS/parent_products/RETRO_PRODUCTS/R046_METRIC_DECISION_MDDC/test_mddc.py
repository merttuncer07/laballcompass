import unittest
from mddc import diagnose_metric_decision_divergence
class Tests(unittest.TestCase):
 def test_small_metric_error_can_make_worse_decision(self):
  r=diagnose_metric_decision_divergence([[.51,.48,.01]],{'near_flip':[[.48,.51,.01]],'far_safe':[[.70,.29,.01]]},[[1,0],[0,1],[0,0]])
  self.assertGreater(r.ranking_inversions,0); self.assertEqual(r.status,'METRIC_DECISION_RANKING_DIVERGENCE_FOUND')
 def test_action_inversion_counted(self):
  r=diagnose_metric_decision_divergence([[.51,.48,.01]],{'x':[[.48,.51,.01]]},[[1,0],[0,1],[0,0]])
  self.assertEqual(r.action_inversions,1); self.assertAlmostEqual(r.scores[0].decision_regret,.03)
 def test_no_false_divergence(self):
  r=diagnose_metric_decision_divergence([[.8,.2]],{'a':[[.75,.25]],'b':[[.7,.3]]},[[1,0],[0,1]])
  self.assertEqual(r.ranking_inversions,0)
 def test_invalid_probability_rejected(self):
  with self.assertRaises(ValueError): diagnose_metric_decision_divergence([[.8,.8]],{'a':[[.5,.5]]},[[1,0],[0,1]])
if __name__=='__main__': unittest.main()
