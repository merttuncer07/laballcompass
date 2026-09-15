import unittest
from tfld import design_localization

class TFLDTests(unittest.TestCase):
    def test_feasible_design_meets_both_limits(self):
        r=design_localization(sample_rate_hz=1000,maximum_time_spread_seconds=.03,maximum_frequency_spread_hz=15,window_lengths=[16,32,64,128,256])
        self.assertEqual(r.status,"FEASIBLE_DESIGN_FOUND"); self.assertTrue(r.selected.feasible)
    def test_impossible_joint_request_is_explicit(self):
        r=design_localization(sample_rate_hz=1000,maximum_time_spread_seconds=.001,maximum_frequency_spread_hz=2,window_lengths=[8,16,32,64,128])
        self.assertEqual(r.status,"JOINT_REQUIREMENT_NOT_MET"); self.assertFalse(r.selected.feasible)
    def test_gaussian_uncertainty_product_near_lower_scale(self):
        r=design_localization(sample_rate_hz=1000,maximum_time_spread_seconds=1,maximum_frequency_spread_hz=1000,window_lengths=[256],window_types=["GAUSSIAN"])
        self.assertGreater(r.selected.uncertainty_product,.07); self.assertLess(r.selected.uncertainty_product,.09)
    def test_invalid_length_rejected(self):
        with self.assertRaises(ValueError): design_localization(sample_rate_hz=1,maximum_time_spread_seconds=1,maximum_frequency_spread_hz=1,window_lengths=[2])
if __name__=="__main__": unittest.main()
