import unittest
from mfqa import FidelityChannel,allocate_quasineutral_measurements


F=FidelityChannel('fine',.0001,.002)
C=FidelityChannel('cheap',.001,.0002)


class MFQATests(unittest.TestCase):
    def test_near_boundary_high_correlation_uses_multifidelity(self):
        r=allocate_quasineutral_measurements(.049,.0004,tolerance=.05,total_budget=.1,fine_channel=F,cheap_channel=C,pilot_correlation=.9)
        self.assertEqual(r.mode,'multifidelity');self.assertGreater(r.n_cheap,r.n_fine)

    def test_far_boundary_skips_program(self):
        r=allocate_quasineutral_measurements(.005,.000025,tolerance=.05,total_budget=.1,fine_channel=F,cheap_channel=C,pilot_correlation=.9)
        self.assertEqual(r.mode,'no_measurement')

    def test_low_correlation_routes_to_fine_only(self):
        r=allocate_quasineutral_measurements(.049,.0004,tolerance=.05,total_budget=.1,fine_channel=F,cheap_channel=C,pilot_correlation=.05)
        self.assertEqual(r.mode,'fine_only')

    def test_negative_value_cheap_channel_routes_to_fine(self):
        expensive=FidelityChannel('cheap',.001,.02)
        r=allocate_quasineutral_measurements(.049,.0004,tolerance=.05,total_budget=.1,fine_channel=F,cheap_channel=expensive,pilot_correlation=.9)
        self.assertEqual(r.mode,'fine_only')

    def test_budget_respected(self):
        r=allocate_quasineutral_measurements(.049,.0004,tolerance=.05,total_budget=.1,fine_channel=F,cheap_channel=C,pilot_correlation=.9)
        self.assertLessEqual(r.spent_budget,.1+1e-12)

    def test_invalid_channel_contract_rejected(self):
        with self.assertRaises(ValueError):allocate_quasineutral_measurements(.049,.1,tolerance=.05,total_budget=1,fine_channel=F,cheap_channel=FidelityChannel('bad',1,0),pilot_correlation=.5)


if __name__=='__main__':unittest.main()
