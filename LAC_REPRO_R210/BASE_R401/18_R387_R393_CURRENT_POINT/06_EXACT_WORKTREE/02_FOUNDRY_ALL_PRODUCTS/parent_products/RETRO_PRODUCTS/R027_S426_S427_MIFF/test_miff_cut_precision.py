"""Independent partition oracle and real defects in the former float residuals."""
from fractions import Fraction
from itertools import product
import math
import random

import pytest

from miff import InformationFlow, design_inference_firewall


def evaluate(nodes, flows, sources=('s',), targets=('t',)):
    return design_inference_firewall(nodes, flows, suspect_sources=sources, protected_targets=targets)


def exhaustive_cost(nodes, flows, sources, targets):
    # All admissible vertex partitions, not an augmenting-path implementation.
    free = sorted(set(nodes) - set(sources) - set(targets))
    values = []
    for flags in product((False, True), repeat=len(free)):
        side = set(sources) | {n for n, take in zip(free, flags) if take}
        values.append(sum((Fraction(float(f.cut_cost)) for f in flows
                           if f.source in side and f.target not in side), Fraction(0)))
    return min(values)


@pytest.mark.parametrize('scale', [1., 1e-13, 1e-100, 1e16, 1e100, 5e-324])
def test_chain_selects_cheaper_cut_at_every_scale(scale):
    flows = [InformationFlow('s', 'mid', .5, 5*scale, 'expensive'),
             InformationFlow('mid', 't', .5, scale, 'cheap')]
    r = evaluate(['s', 'mid', 't'], flows)
    assert [f.label for f in r.cut_edges] == ['cheap']
    assert r.total_cut_cost == scale
    assert r.firewalled_protected_contamination == (0.,)


@pytest.mark.parametrize('cost', [1e16, 1e308, 5e-324])
def test_super_terminal_edges_cannot_replace_real_cut(cost):
    r = evaluate(['s', 't'], [InformationFlow('s', 't', .5, cost)])
    assert len(r.cut_edges) == 1
    assert r.total_cut_cost == cost
    assert r.status == 'MINIMUM_COST_FIREWALL_ISOLATES_PROTECTED_MODULES'


def test_parallel_cost_sum_can_exceed_float_range_when_optimal_cut_does_not():
    flows = [InformationFlow('s', 'm', .1, 1e308, 'large1'),
             InformationFlow('s', 'm', .1, 1e308, 'large2'),
             InformationFlow('m', 't', .1, 1., 'exit')]
    r = evaluate(['s', 'm', 't'], flows)
    assert [e.label for e in r.cut_edges] == ['exit']
    assert r.total_cut_cost == 1.


def test_unrepresentable_optimal_total_is_rejected_not_reported_as_infinity():
    with pytest.raises(ValueError, match='output range'):
        evaluate(['s', 't'], [InformationFlow('s', 't', .1, 1e308)] * 2)


def test_one_float_step_cost_difference_is_not_erased():
    larger = math.nextafter(1., 2.)
    flows = [InformationFlow('s', 'm', .1, larger, 'larger'),
             InformationFlow('m', 't', .1, 1., 'smaller')]
    assert evaluate(['s', 'm', 't'], flows).cut_edges == (flows[1],)


def test_mixed_extreme_capacities_preserve_a_small_but_real_edge():
    flows = [InformationFlow('s', 'm', .1, 1e308),
             InformationFlow('m', 't', .1, 5e-324)]
    assert evaluate(['s', 'm', 't'], flows).cut_edges == (flows[1],)


@pytest.mark.parametrize('exponent', [-900, 0, 900])
def test_networkx_published_directed_graph_expected_cut(exponent):
    # NetworkX test_maxflow.py::test_digraph3, expected min cut = 23.
    edges = [('s','v1',16),('s','v2',13),('v1','v2',10),('v2','v1',4),
             ('v1','v3',12),('v3','v2',9),('v2','v4',14),('v4','v3',7),
             ('v3','t',20),('v4','t',4)]
    flows = [InformationFlow(a,b,.02,math.ldexp(float(cost),exponent)) for a,b,cost in edges]
    r = evaluate(['s','v1','v2','v3','v4','t'], flows)
    assert r.total_cut_cost == math.ldexp(23., exponent)
    assert r.firewalled_protected_contamination == (0.,)


@pytest.mark.parametrize('exponent', [-900, 0, 900])
def test_against_all_vertex_partitions_with_parallel_reverse_and_multiple_terminals(exponent):
    rng = random.Random(84027)
    nodes = ['s','s2','a','b','t','t2']
    for _ in range(20):
        flows = [InformationFlow(a,b,.01,math.ldexp(rng.randint(1,50)/8,exponent),str(i))
                 for i,(a,b) in enumerate((rng.sample(nodes,2) for _ in range(16)))]
        r = evaluate(nodes, flows, ('s','s2'), ('t','t2'))
        exact = sum((Fraction(float(f.cut_cost)) for f in r.cut_edges), Fraction(0))
        assert exact == exhaustive_cost(nodes, flows, ('s','s2'), ('t','t2'))
        assert all(abs(v) < 1e-15 for v in r.firewalled_protected_contamination)
