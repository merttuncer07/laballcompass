import unittest
from cfdre import closure_fidelity_explore as f
class T(unittest.TestCase):
 def test_reduced(self): self.assertEqual(f(fidelity=.95,floor=.9).representation,'reduced')
 def test_full(self): self.assertEqual(f(fidelity=.7,floor=.9).representation,'full')
 def test_equal(self): self.assertEqual(f(fidelity=.9,floor=.9).representation,'reduced')
 def test_zero(self): self.assertEqual(f(fidelity=0,floor=.1).representation,'full')
 def test_invalid(self):
  with self.assertRaises(ValueError): f(fidelity=1.2,floor=.9)
 def test_comparator(self): self.assertNotEqual(f(fidelity=.5,floor=.8).representation,'reduced')
if __name__=='__main__': unittest.main()
