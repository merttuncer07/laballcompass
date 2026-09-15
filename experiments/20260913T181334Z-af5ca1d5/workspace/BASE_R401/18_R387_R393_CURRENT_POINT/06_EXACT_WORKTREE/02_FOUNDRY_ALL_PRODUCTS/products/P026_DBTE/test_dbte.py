import unittest
if __package__:
    from .dbte import Edge, deployable_on_series_path, explore_deployable_tipping
else:
    from dbte import Edge, deployable_on_series_path, explore_deployable_tipping


class DBTETests(unittest.TestCase):
    def setUp(self): self.edges=[Edge('wide',80,1),Edge('narrow',30,1)]
    def test_true_bottleneck_flips(self):
        r=explore_deployable_tipping(100,self.edges,horizon=3,target=50,capacity_grid={'wide':[100], 'narrow':[40,50,60]})
        self.assertEqual(r.tipping_edge,'narrow'); self.assertEqual(r.tipping_capacity,50)
    def test_wide_expansion_does_nothing(self): self.assertEqual(deployable_on_series_path(100,[Edge('wide',100,1),Edge('narrow',30,1)],3),30)
    def test_late_route_is_zero(self): self.assertEqual(deployable_on_series_path(100,[Edge('late',100,4)],3),0)
    def test_yield_is_real_constraint(self): self.assertEqual(deployable_on_series_path(100,[Edge('e',80,1,.5)],3),40)


if __name__ == '__main__': unittest.main()
