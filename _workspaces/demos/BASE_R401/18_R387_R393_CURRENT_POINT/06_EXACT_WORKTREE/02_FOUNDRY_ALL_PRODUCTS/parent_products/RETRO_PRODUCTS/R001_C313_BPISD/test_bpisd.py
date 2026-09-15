import unittest
from bpisd import design_binary_persuasion

class BPISDTests(unittest.TestCase):
    def setUp(self):
        self.result=design_binary_persuasion(prior_state_one=0.3,action_names=["REJECT","ADOPT"],
            receiver_payoffs=[[0,0],[-1.5,1]],sender_payoffs=[[0,0],[1,1]])
    def test_bayes_plausibility(self):
        self.assertAlmostEqual(self.result.bayes_posterior_mean,0.3); self.assertLess(self.result.bayes_plausibility_residual,1e-10)
    def test_persuasion_improves_sender_value(self):
        self.assertAlmostEqual(self.result.no_information_sender_value,0); self.assertGreater(self.result.optimized_sender_value,0.49)
    def test_channel_likelihoods_sum_by_state(self):
        self.assertAlmostEqual(sum(s.probability_given_state_zero for s in self.result.signals),1)
        self.assertAlmostEqual(sum(s.probability_given_state_one for s in self.result.signals),1)
    def test_invalid_prior_rejected(self):
        with self.assertRaises(ValueError):
            design_binary_persuasion(prior_state_one=1,action_names=["a"],receiver_payoffs=[[0,1]],sender_payoffs=[[0,1]])
if __name__=="__main__": unittest.main()
