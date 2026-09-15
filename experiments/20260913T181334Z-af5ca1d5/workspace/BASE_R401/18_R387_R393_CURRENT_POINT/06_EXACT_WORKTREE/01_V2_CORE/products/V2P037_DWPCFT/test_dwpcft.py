import unittest
from dwpcft import *
class T(unittest.TestCase):
 def pts(self): return [Point(.05,10,4,.01),Point(.1,1,4,.01),Point(.2,10,4,.5)]
 def test_boundary_consequence_gets_most(self):
  r=decision_weighted_pcft_calibration(self.pts(),additional_samples=9); self.assertGreater(r.added_samples[.05],r.added_samples[.2])
 def test_uncertainty_reduced(self):
  r=decision_weighted_pcft_calibration(self.pts(),additional_samples=9); self.assertLess(r.after_weighted_uncertainty,r.before_weighted_uncertainty)
 def test_beats_uniform(self): self.assertLessEqual(decision_weighted_pcft_calibration(self.pts(),additional_samples=9).after_weighted_uncertainty,decision_weighted_pcft_calibration(self.pts(),additional_samples=9).uniform_after)
 def test_budget_conserved(self): self.assertEqual(sum(decision_weighted_pcft_calibration(self.pts(),additional_samples=9).added_samples.values()),9)
 def test_zero_budget(self): self.assertEqual(sum(decision_weighted_pcft_calibration(self.pts(),additional_samples=0).added_samples.values()),0)
 def test_negative_budget(self):
  with self.assertRaises(ValueError): decision_weighted_pcft_calibration(self.pts(),additional_samples=-1)
 def test_empty(self):
  with self.assertRaises(ValueError): decision_weighted_pcft_calibration([],additional_samples=1)
 def test_status(self): self.assertIn('CALIBRATION',decision_weighted_pcft_calibration(self.pts(),additional_samples=1).status)
if __name__=='__main__': unittest.main()
