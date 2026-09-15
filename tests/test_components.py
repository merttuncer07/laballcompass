import unittest
from maintenance.components import resolve,target_matches
from maintenance.runner import discover
class ComponentTests(unittest.TestCase):
 def test_stable_foundry_id_routes_to_its_tests(self):
  r=resolve('P039');matched=[t for t in discover('all') if target_matches(r,t)];self.assertEqual(len(matched),1);self.assertIn('P039_CACF',matched[0].pattern)
 def test_recovered_id_routes_to_recovered_contract(self):
  r=resolve('V2P057');self.assertEqual(sum(target_matches(r,t) for t in discover('all')),1)
 def test_unknown_id_explained(self):
  with self.assertRaises(ValueError):resolve('NOT_REAL')
