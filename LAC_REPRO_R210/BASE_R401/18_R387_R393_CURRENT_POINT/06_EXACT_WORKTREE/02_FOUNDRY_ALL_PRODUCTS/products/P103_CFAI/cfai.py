"""Circular-Flow Audit Allocation: new native implementation, 2026-09-14.

The historical composition description survives; its original source does not.
This implementation invokes the packaged HFAD, BICC and ACRA mechanisms. It
allocates an explicit sensitivity proxy, not fraud probability or audit risk.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Mapping

import numpy as np

PRODUCT_SPEC = {
    'product_id': 'P103', 'short_name': 'CFAI',
    'title': 'Circular-Flow Audit Allocation', 'parents_raw': 'HFAD + BICC + ACRA',
    'execution_mode': 'native_flow_allocation',
    'implementation_version': 'native_reimplementation_20260914',
    'claim_boundary_raw': 'Observed replacement sensitivity of circulation energy; neither a fraud label nor a calibrated audit benefit.'}

PARENTS = {
    'hfad': 'RETRO_PRODUCTS/R002_C326_HFAD/hfad.py',
    'bicc': 'RETRO_PRODUCTS/R007_C349_BICC/bicc.py',
    'acra': 'CURRENT_PRODUCTS/IM406_IM037_ACRA/acra.py',
}


def _parent(name):
    path = Path(__file__).resolve().parents[2] / 'parent_products' / PARENTS[name]
    module_id = '_cfai_native_' + name
    if module_id not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_id, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = module
        spec.loader.exec_module(module)
    return sys.modules[module_id], path


def allocate_flow_review(node_count, edges, base_flows, replacement_flows=None, *,
                         budget, options=None, edge_names=None):
    """Rank actual graph edges and choose one resolution option per edge.

    Each row is a deterministic scenario. Coordinate replacements change only
    that edge; other edges remain fixed. With no replacement_flows, probes set
    each edge to zero. Options specify cost and an assumed residual_error
    multiplier. Allocation minimizes sum(RMS replacement effect squared times
    multiplier squared), subject to the budget. These are explicit modelling
    choices, not learned probabilities or measured inspection effectiveness.
    """
    if not isinstance(node_count, int) or isinstance(node_count, bool) or not 1 <= node_count <= 2000:
        raise ValueError('node_count must be an integer between 1 and 2000')
    edges = [tuple(edge) for edge in edges]
    if not edges or len(edges) > 200 or any(len(e) != 2 for e in edges):
        raise ValueError('Provide between 1 and 200 oriented edges, each with two endpoints')
    base = np.asarray(base_flows, dtype=float)
    if base.ndim != 2 or base.shape[0] < 1 or base.shape[1] != len(edges) or not np.all(np.isfinite(base)):
        raise ValueError('base_flows must be a finite scenario-by-edge matrix')
    if base.size > 20000:
        raise ValueError('This dense implementation supports up to 20,000 scenario-edge entries')
    replacement = np.zeros_like(base) if replacement_flows is None else np.asarray(replacement_flows, dtype=float)
    if replacement.shape != base.shape or not np.all(np.isfinite(replacement)):
        raise ValueError('replacement_flows must be finite and match base_flows')
    names = list(edge_names) if edge_names is not None else [f'{a}->{b} [{i}]' for i, (a,b) in enumerate(edges)]
    if len(names) != len(edges) or any(not isinstance(n,str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError('edge_names must contain one unique nonempty name per edge')
    if not np.isfinite(budget) or budget < 0:
        raise ValueError('budget must be finite and nonnegative')
    option_rows = list(options) if options is not None else [
        {'name': 'unreviewed', 'cost': 0.0, 'residual_error': 1.0},
        {'name': 'reviewed', 'cost': 1.0, 'residual_error': 0.0}]
    for option in option_rows:
        if set(option) != {'name','cost','residual_error'}:
            raise ValueError('Each option needs name, cost and residual_error')
        if not isinstance(option['name'],str) or not option['name'] or any(
                not np.isfinite(option[k]) or option[k] < 0 for k in ('cost','residual_error')):
            raise ValueError('Option names must be nonempty; cost and residual_error finite and nonnegative')

    hfad, hfad_path = _parent('hfad')
    bicc, bicc_path = _parent('bicc')
    acra, acra_path = _parent('acra')
    decomposer = hfad.HodgeFlowAttributionDecomposer(hfad.incidence_from_edges(node_count, edges))

    def cycle_energy(flow):
        result = decomposer.decompose(flow)
        return result.local_cycle_energy + result.harmonic_energy

    influence = bicc.audit_concentration(cycle_energy, base, replacement, sampling_model='scenario_pairs')
    regions = [acra.DecisionRegion(names[i.coordinate], i.rms_replacement_effect**2, 0.0, 1.0)
               for i in influence.influences]
    resolution = [acra.ResolutionOption(o['name'],o['cost'],o['residual_error'],0.0) for o in option_rows]
    allocator = acra.AdaptiveConsequenceResolutionAllocator(regions, resolution)
    plan = allocator.allocate(float(budget))
    priority = sorted(influence.influences, key=lambda x: (-x.rms_replacement_effect, names[x.coordinate]))
    return {
        'product': PRODUCT_SPEC,
        'reconstruction_tier': 'NATIVE_REIMPLEMENTATION_NOT_HISTORICAL_SOURCE',
        'scenario_count': int(len(base)), 'edge_count': len(edges),
        'baseline_cycle_energy': [cycle_energy(row) for row in base],
        'probe': 'each edge replaced by zero' if replacement_flows is None else 'supplied coordinate replacement scenarios',
        'edge_priority': [{'edge_index': x.coordinate, 'edge_name': names[x.coordinate],
                           'source': edges[x.coordinate][0], 'target': edges[x.coordinate][1],
                           'rms_energy_change': x.rms_replacement_effect,
                           'maximum_observed_energy_change': x.maximum_observed_replacement_effect}
                          for x in priority],
        'plan': {'budget': plan['budget'], 'total_cost': plan['total_cost'],
                 'remaining_influence_score': plan['total_decision_loss'],
                 'allocations': [{'edge_name': a['region'], 'option': a['option'], 'cost': a['cost'],
                                  'residual_influence_score': a['decision_loss']} for a in plan['allocations']]},
        'options': option_rows,
        'influence_scope': influence.certificate_status,
        'probabilistic_certificate': None,
        'assumptions': [
            'Hodge circulation is a signed cycle-space projection; it does not establish a directed circular payment or fraud.',
            'Coordinate probes are scenarios, not independent draws. No concentration guarantee is reported.',
            'The additive allocation score ignores joint inspection interactions.',
            'Resolution multipliers are assumptions; default reviewed=0 models complete removal of that edge sensitivity.',
            'No claim is made that this score equals monetary loss or actual auditor benefit.'],
        'mechanisms': [{'name': name.upper(), 'source': str(path.relative_to(Path(__file__).resolve().parents[2])),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                       for name,path in [('hfad',hfad_path),('bicc',bicc_path),('acra',acra_path)]]}


def evaluate(records, *, baseline=None, budget=None):
    """Execute a graph configuration; the old score-only placeholder is retired."""
    if not isinstance(records, Mapping):
        raise ValueError('CFAI requires a graph configuration: node_count, edges and base_flows; score-only records do not run its mechanisms')
    if baseline is not None:
        raise ValueError('baseline score records are not a circular-flow comparison')
    allowed = {'node_count','edges','base_flows','replacement_flows','budget','options','edge_names'}
    if set(records) - allowed:
        raise ValueError('Unknown CFAI fields: ' + ', '.join(sorted(set(records) - allowed)))
    if not {'node_count','edges','base_flows'} <= set(records):
        raise ValueError('CFAI needs node_count, edges and base_flows')
    kwargs = dict(records)
    if budget is not None: kwargs['budget'] = budget
    if 'budget' not in kwargs: raise ValueError('CFAI needs an inspection budget')
    return allocate_flow_review(**kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', help='JSON graph and flow configuration')
    parser.add_argument('--output', help='New JSON result file; existing files are preserved')
    args = parser.parse_args(argv)
    try:
        result = evaluate(json.loads(Path(args.config).read_text()))
        content = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        if args.output:
            with Path(args.output).open('x') as handle: handle.write(content)
            print(args.output)
        else: print(content, end='')
    except (ValueError, OSError, RuntimeError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
