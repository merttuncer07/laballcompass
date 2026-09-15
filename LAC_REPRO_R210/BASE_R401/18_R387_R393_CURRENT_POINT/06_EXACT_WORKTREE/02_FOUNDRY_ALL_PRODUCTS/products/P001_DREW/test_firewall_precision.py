import pytest

if __package__:
    from .drew import run_reliability_workbench
else:
    from drew import run_reliability_workbench


@pytest.mark.parametrize('scale', [1e-13, 1., 1e16])
def test_drew_preserves_miff_cheapest_cut_when_cost_units_change(scale):
    r = run_reliability_workbench(firewall_inputs={
        'modules': ['search','diagnostic','protected'],
        'flows': [
            {'source':'search','target':'diagnostic','gain':.3,'cut_cost':5*scale,'label':'expensive'},
            {'source':'diagnostic','target':'protected','gain':.3,'cut_cost':scale,'label':'cheap'},
        ],
        'suspect_sources':['search'], 'protected_targets':['protected'],
    })
    assert [f.label for f in r.inference_firewall.cut_edges] == ['cheap']
    assert r.inference_firewall.total_cut_cost == scale
    assert 'PROTECTED_EVALUATION_REQUIRES_FLOW_CUT' in r.evidence_flags
    assert r.inference_firewall.firewalled_protected_contamination == (0.,)
