import unittest
if __package__:
    from .reis import allocate_relational_safeguards
else:
    from reis import allocate_relational_safeguards


class REISTests(unittest.TestCase):
    def result(self): return allocate_relational_safeguards({'A':.9725,'B':.02649,'C':.02649},{'A':1.7464,'B':132.212,'C':.6021},{'A':1,'B':1,'C':1},budget=1)
    def test_probability_and_impact_disagree(self): self.assertEqual(self.result().posterior_priority[0],'A'); self.assertEqual(self.result().impact_priority[0],'B')
    def test_budget_selects_impact(self): self.assertEqual(self.result().selected_safeguards,('B',))
    def test_risk_product(self): self.assertAlmostEqual(self.result().posterior_impact['B'],.02649*132.212)
    def test_mismatched_records_rejected(self):
        with self.assertRaises(ValueError): allocate_relational_safeguards({'A':1},{'B':1},{'A':1},budget=1)


if __name__ == '__main__': unittest.main()
