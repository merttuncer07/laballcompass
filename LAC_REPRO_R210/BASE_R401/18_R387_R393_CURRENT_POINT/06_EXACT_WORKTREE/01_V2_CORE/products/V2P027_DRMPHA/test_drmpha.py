import unittest
from drmpha import decision_relevant_holdout_audit as f
class T(unittest.TestCase):
 def test_order_dev(self): self.assertEqual(f(development_scores={'a':1,'b':2},protected_losses={'a':0,'b':10}).audit_order[0],'b')
 def test_holdout_best(self): self.assertEqual(f(development_scores={'a':1,'b':2},protected_losses={'a':0,'b':10}).selected,'a')
 def test_no_leak_order(self): self.assertEqual(f(development_scores={'a':1,'b':2},protected_losses={'a':999,'b':-999}).audit_order,('b','a'))
 def test_empty(self): self.assertIsNone(f(development_scores={},protected_losses={}).selected)
 def test_mismatch(self):
  with self.assertRaises(ValueError): f(development_scores={'a':1},protected_losses={'b':1})
 def test_comparator(self): self.assertNotEqual(f(development_scores={'a':1,'b':3},protected_losses={'a':0,'b':9}).audit_order[0],f(development_scores={'a':1,'b':3},protected_losses={'a':0,'b':9}).selected)
if __name__=='__main__': unittest.main()
