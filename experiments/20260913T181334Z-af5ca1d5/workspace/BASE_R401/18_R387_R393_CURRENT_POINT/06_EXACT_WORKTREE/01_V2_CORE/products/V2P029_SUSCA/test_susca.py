import unittest
from susca import Item,support_adjusted_shared_capacity as f
class T(unittest.TestCase):
 def base(self): return [Item('fragile',10,(10,0),.2),Item('supported',7,(10,5),1),Item('anchor',3,(0,5),1)]
 def test_fragile_excluded(self): self.assertIn('fragile',f(self.base(),(10,5),min_support=.3).excluded)
 def test_supported_first(self): self.assertEqual(f(self.base(),(10,5),min_support=.3).order[0],'supported')
 def test_no_double_count(self): self.assertLessEqual(sum(f(self.base(),(10,5),min_support=.3).allocation.values()),15)
 def test_full_support_reduces_to_nominal(self):
  x=[Item('a',4,(5,),1),Item('b',3,(5,),1)]; r=f(x,(5,)); self.assertAlmostEqual(r.supported_value,r.nominal_value)
 def test_support_changes_ranking(self):
  x=[Item('a',10,(5,),.4),Item('b',5,(5,),1)]; self.assertEqual(f(x,(5,),min_support=.1).order[0],'b')
 def test_hard_floor(self): self.assertEqual(f([Item('a',1,(1,),.1)],(1,),min_support=.2).supported_value,0)
 def test_invalid_support(self):
  with self.assertRaises(ValueError): f([Item('a',1,(1,),1.2)],(1,))
 def test_invalid_shape(self):
  with self.assertRaises(ValueError): f([Item('a',1,(1,2),1)],(1,))
if __name__=='__main__': unittest.main()
