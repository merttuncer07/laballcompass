import random
import unittest

from cpdbe import Edge, pressure_guided_deployable_tipping
from dbte import deployable_on_series_path, explore_deployable_tipping


class CPDBETests(unittest.TestCase):
    # P026 invariant-preservation cases.
    def test_true_bottleneck_flip_is_preserved(self):
        edges=[Edge('wide',120,1),Edge('narrow',30,1)]
        grid={'wide':[130,150], 'narrow':[40,50,60]}
        base=explore_deployable_tipping(100,edges,horizon=3,target=50,capacity_grid=grid)
        got=pressure_guided_deployable_tipping(100,edges,horizon=3,target=50,capacity_grid=grid)
        self.assertEqual((got.tipping.tipping_edge,got.tipping.tipping_capacity),(base.tipping_edge,base.tipping_capacity))

    def test_wide_slack_expansion_is_pruned(self):
        r=pressure_guided_deployable_tipping(100,[Edge('wide',120,1),Edge('narrow',30,1)],horizon=3,target=50,capacity_grid={'wide':[130,150], 'narrow':[40,50]})
        self.assertIn('wide',r.pruned_edges)
        self.assertNotIn('wide',r.scanned_edges)

    def test_late_route_remains_zero(self):
        r=pressure_guided_deployable_tipping(100,[Edge('late',100,4)],horizon=3,target=10,capacity_grid={'late':[120,150]})
        self.assertEqual(r.tipping.baseline_deployable,0)
        self.assertEqual(r.tipping.status,'NO_TIPPING_POINT_ON_GRID')

    def test_yield_constraint_is_preserved(self):
        r=pressure_guided_deployable_tipping(100,[Edge('e',80,1,.5)],horizon=3,target=50,capacity_grid={'e':[90,100]})
        self.assertEqual(r.tipping.baseline_deployable,40)
        self.assertEqual(r.tipping.status,'DEPLOYABLE_TARGET_TIPPING_POINT_FOUND')

    # Adapter/certificate boundary cases.
    def test_zero_pressure_capacity_increase_cannot_change_output(self):
        edges=[Edge('slack',150,1),Edge('bind',40,1)]
        before=deployable_on_series_path(100,edges,3)
        after=deployable_on_series_path(100,[Edge('slack',1000,1),Edge('bind',40,1)],3)
        self.assertEqual(before,after)
        r=pressure_guided_deployable_tipping(100,edges,horizon=3,target=60,capacity_grid={'slack':[200,1000],'bind':[60,80]})
        self.assertIn('slack',r.pruned_edges)

    def test_equal_incoming_capacity_is_safely_pruned(self):
        edges=[Edge('upstream',40,1),Edge('equal',40,1)]
        r=pressure_guided_deployable_tipping(100,edges,horizon=3,target=50,capacity_grid={'equal':[50,80]})
        p={x.edge_name:x.minimum_cap_correction for x in r.edge_pressure}
        self.assertEqual(p['equal'],0.0)
        self.assertEqual(r.scanned_grid_points,0)
        self.assertEqual(r.tipping.status,'NO_TIPPING_POINT_ON_GRID')

    def test_positive_pressure_is_not_overclaimed_as_unique_bottleneck(self):
        r=pressure_guided_deployable_tipping(100,[Edge('wide',80,1),Edge('narrow',30,1)],horizon=3,target=50,capacity_grid={'wide':[100], 'narrow':[50]})
        # Both caps are active locally; K009 pressure alone cannot drop 'wide'.
        self.assertEqual(set(r.scanned_edges),{'wide','narrow'})
        self.assertEqual(r.tipping.tipping_edge,'narrow')

    def test_decreasing_grid_fails_closed_to_full_scan(self):
        edges=[Edge('a',120,1),Edge('b',30,1)]
        grid={'a':[20,140], 'b':[50]}
        full=explore_deployable_tipping(100,edges,horizon=3,target=50,capacity_grid=grid)
        r=pressure_guided_deployable_tipping(100,edges,horizon=3,target=50,capacity_grid=grid)
        self.assertFalse(r.certificate_applicable)
        self.assertEqual(r.scanned_grid_points,r.full_grid_points)
        self.assertEqual(r.tipping,full)

    def test_target_already_met_fails_closed_to_full_scan(self):
        edges=[Edge('a',120,1),Edge('b',80,1)]
        grid={'a':[130], 'b':[90]}
        full=explore_deployable_tipping(100,edges,horizon=3,target=70,capacity_grid=grid)
        r=pressure_guided_deployable_tipping(100,edges,horizon=3,target=70,capacity_grid=grid)
        self.assertFalse(r.certificate_applicable)
        self.assertEqual(r.tipping,full)

    def test_random_monotone_grids_match_full_p026_exactly(self):
        rng=random.Random(7)
        for _ in range(120):
            n=rng.randint(2,6)
            edges=[Edge(f'e{i}',rng.uniform(20,160),rng.uniform(0,0.4),rng.uniform(.7,1.0)) for i in range(n)]
            stock=rng.uniform(30,180); horizon=sum(e.lead_time for e in edges)+1
            baseline=deployable_on_series_path(stock,edges,horizon)
            target=baseline+rng.uniform(1,40)
            grid={e.name:[e.capacity+rng.uniform(0,80) for __ in range(3)] for e in edges}
            full=explore_deployable_tipping(stock,edges,horizon=horizon,target=target,capacity_grid=grid)
            got=pressure_guided_deployable_tipping(stock,edges,horizon=horizon,target=target,capacity_grid=grid)
            self.assertEqual(got.tipping,full)

    def test_many_slack_edges_reduce_grid_without_changing_result(self):
        edges=[Edge('s0',200),Edge('s1',150),Edge('b',40),Edge('s2',120),Edge('s3',200)]
        grid={e.name:[e.capacity+10,e.capacity+20,e.capacity+40,e.capacity+80] for e in edges}
        full=explore_deployable_tipping(100,edges,horizon=1,target=70,capacity_grid=grid)
        got=pressure_guided_deployable_tipping(100,edges,horizon=1,target=70,capacity_grid=grid)
        self.assertEqual(got.tipping,full)
        self.assertEqual(got.full_grid_points,20)
        self.assertEqual(got.scanned_grid_points,4)
        self.assertAlmostEqual(got.pruning_fraction,.8)

    def test_unknown_edge_and_duplicate_names_are_rejected(self):
        with self.assertRaises(KeyError):
            pressure_guided_deployable_tipping(10,[Edge('a',5)],horizon=1,target=8,capacity_grid={'x':[9]})
        with self.assertRaises(ValueError):
            pressure_guided_deployable_tipping(10,[Edge('a',5),Edge('a',6)],horizon=1,target=8,capacity_grid={'a':[9]})


if __name__=='__main__': unittest.main()
