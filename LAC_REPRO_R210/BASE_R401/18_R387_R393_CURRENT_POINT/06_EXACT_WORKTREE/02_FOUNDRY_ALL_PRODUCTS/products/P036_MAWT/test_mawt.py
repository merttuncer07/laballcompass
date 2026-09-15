from .mawt import *
def test_same_shape_hides_quantity_in_w2():
 r=mawt([0,10],[50,50],[0,10],[75,75]); assert r['normalized_w2']==0 and r['created_mass']==50
def test_equal_mass_geometry_shift_visible(): assert mawt([0],[100],[10],[100])['normalized_w2']==10
def test_mass_accounts_stay_raw(): assert mawt([0],[150],[0],[100])['destroyed_mass']==50

