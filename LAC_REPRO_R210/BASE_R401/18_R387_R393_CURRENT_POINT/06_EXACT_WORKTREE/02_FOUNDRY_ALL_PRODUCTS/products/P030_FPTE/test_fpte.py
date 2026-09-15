import unittest
if __package__:
    from .fpte import FailureMechanism,explore_retention_tipping,frozen_architecture_energy
else:
    from fpte import FailureMechanism,explore_retention_tipping,frozen_architecture_energy


class FPTETests(unittest.TestCase):
    def mechanisms(self): return [FailureMechanism('sacrificial',.2,5),FailureMechanism('deflection',.25,6),FailureMechanism('pullout',.2,2)]
    def test_tipping_found_without_reoptimization(self):
        r=explore_retention_tipping(self.mechanisms(),baseline_retention=.8,retention_grid=[.7,.5,.3],required_energy=4); self.assertEqual(r.tipping_retention,.3)
    def test_bridge_cliff_hides_later_mechanisms(self): self.assertEqual(frozen_architecture_energy(self.mechanisms(),.3)[1],('sacrificial',))
    def test_baseline_meets_requirement(self): self.assertGreater(explore_retention_tipping(self.mechanisms(),baseline_retention=.8,retention_grid=[.3],required_energy=4).baseline_energy,4)
    def test_no_flip_is_explicit(self): self.assertIsNone(explore_retention_tipping(self.mechanisms(),baseline_retention=.8,retention_grid=[.8],required_energy=1).tipping_retention)


if __name__ == '__main__': unittest.main()
