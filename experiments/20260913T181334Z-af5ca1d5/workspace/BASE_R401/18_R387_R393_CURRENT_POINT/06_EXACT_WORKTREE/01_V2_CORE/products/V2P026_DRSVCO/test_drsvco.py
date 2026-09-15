import unittest
from drsvco import decision_relevant_cycle_explore as f
class T(unittest.TestCase):
 def test_crossing_prioritized(self): self.assertEqual(f(points=[('static',10,.9,.01),('uncertain',5,.3,.1)],min_active=.25).evaluate,'uncertain')
 def test_no_crossing_leverage(self): self.assertEqual(f(points=[('a',2,.9,.1),('b',4,.9,.2)],min_active=.2).evaluate,'b')
 def test_empty(self): self.assertIsNone(f(points=[],min_active=.2).evaluate)
 def test_invalid(self):
  with self.assertRaises(ValueError): f(points=[],min_active=2)
 def test_boundary_equal(self): self.assertEqual(f(points=[('x',1,.3,.05)],min_active=.35).evaluate,'x')
 def test_comparator_diff(self): self.assertNotEqual(f(points=[('static',10,.9,.01),('boundary',4,.3,.1)],min_active=.25).evaluate,'static')
if __name__=='__main__': unittest.main()
