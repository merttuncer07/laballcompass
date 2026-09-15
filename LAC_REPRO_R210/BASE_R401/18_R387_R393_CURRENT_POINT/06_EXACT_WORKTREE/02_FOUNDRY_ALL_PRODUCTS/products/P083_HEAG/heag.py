"""Historical Evidence Acquisition Gate: new native implementation, 2026-09-14.

EBC -> scalar normal working belief -> AICC one-step information value.
Historical source remains missing. Future errors must be independent of used
evidence; that condition is declared, not inferred.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from collections.abc import Mapping
import numpy as np

PRODUCT_SPEC = {
    'product_id': 'P083', 'short_name': 'HEAG',
    'title': 'Historical Evidence Acquisition Gate', 'parents_raw': 'EBC + AICC',
    'execution_mode': 'native_evidence_acquisition',
    'implementation_version': 'native_reimplementation_20260914',
    'claim_boundary_raw': 'Plug-in normal EBC belief and one-step AICC affine utility; future error independent of used evidence. No calibrated audit recommendation or historical equivalence.'}
PARENTS = {'ebc': 'RETRO_PRODUCTS/R026_S423_S424_EBC/ebc.py',
           'aicc': 'CURRENT_PRODUCTS/IM359_IM014_AICC/aicc.py'}


def _parent(name):
    path = Path(__file__).resolve().parents[2]/'parent_products'/PARENTS[name]
    package_id = '_heag_parent_'+name
    module_id = package_id+'.'+name
    if module_id not in sys.modules:
        package = types.ModuleType(package_id)
        package.__path__ = [str(path.parent)]
        sys.modules[package_id] = package
        spec = importlib.util.spec_from_file_location(module_id, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = module
        spec.loader.exec_module(module)
    return sys.modules[module_id], path


def _validate_config(config):
    if not isinstance(config, Mapping) or set(config) != {'evidence', 'decision'}:
        raise ValueError('HEAG needs evidence and decision configurations; score-only records do not invoke its mechanisms')
    evidence, decision = config['evidence'], config['decision']
    if not isinstance(evidence, Mapping) or not isinstance(decision, Mapping):
        raise ValueError('evidence and decision must be mappings')
    required = {'current_estimate', 'current_standard_error', 'historical'}
    allowed = required | {'current_observation_id', 'compatibility_scale', 'borrowing_cap_ratio', 'confidence_z',
                          'covariance', 'covariance_names', 'current_name', 'adaptive'}
    if not required <= set(evidence) or set(evidence)-allowed:
        raise ValueError('Missing or unknown EBC evidence fields')
    if not isinstance(evidence['historical'], (list, tuple)) or len(evidence['historical']) > 500:
        raise ValueError('historical must contain at most 500 normal estimates')
    if 'covariance' not in evidence and set(evidence)&{'covariance_names', 'current_name', 'adaptive'}:
        raise ValueError('covariance_names, current_name and adaptive require an explicit evidence covariance')
    if set(decision) != {'action_names', 'action_slopes', 'action_intercepts', 'channels', 'future_error_relation'}:
        raise ValueError('decision requires action_names, action_slopes, action_intercepts, channels and future_error_relation')
    if decision['future_error_relation'] != 'independent_of_evidence':
        raise ValueError('This adapter requires future error independent of current/historical evidence; shared error needs a joint model')
    names = decision['action_names']
    if not isinstance(names, (list, tuple)) or not 1 <= len(names) <= 500 or any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError('action_names must contain 1 to 500 unique nonempty names')
    if np.asarray(decision['action_slopes']).shape != (len(names), 1) or np.asarray(decision['action_intercepts']).shape != (len(names),):
        raise ValueError('HEAG has one scalar estimand; each named action needs one slope and intercept')
    if not isinstance(decision['channels'], (list, tuple)) or len(decision['channels']) > 200:
        raise ValueError('channels must contain at most 200 candidate measurements')


def _acquisition(mean, se, decision, aicc):
    channels = []
    for row in decision['channels']:
        if not isinstance(row, Mapping) or set(row) != {'name', 'measurement_vector', 'noise_variance', 'cost'}:
            raise ValueError('Each channel requires name, measurement_vector, noise_variance and cost')
        channels.append(aicc.InformationChannel(**row))
    controller = aicc.AdaptiveInformationController([mean], [[se**2]], decision['action_slopes'], decision['action_intercepts'], channels)
    ranked = controller.rank_channels()
    return {'working_mean': float(mean), 'working_standard_error': float(se),
            'current_action': decision['action_names'][controller.action()],
            'current_action_utilities': controller.expected_action_utilities().tolist(),
            'chosen_channel': ranked[0].name if ranked and ranked[0].net_value > 0 else None,
            'ranked_channels': [asdict(v) for v in ranked]}


def evaluate(config, *, baseline=None, budget=None):
    """EBC reported mean/SE define a working Gaussian, not a calibrated posterior."""
    if baseline is not None or budget is not None:
        raise ValueError('HEAG selects one measurement using declared cost; score baselines and budget allocations are not this model')
    _validate_config(config)
    ebc, ebc_path = _parent('ebc'); aicc, aicc_path = _parent('aicc')
    arguments = dict(config['evidence'])
    history = [ebc.HistoricalEstimate(**r) for r in arguments.pop('historical')]
    borrow = ebc.borrow_correlated_evidence if 'covariance' in arguments else ebc.borrow_evidence
    borrowing = borrow(historical=history, **arguments)
    current = _acquisition(borrowing.current_estimate, borrowing.current_standard_error, config['decision'], aicc)
    informed = _acquisition(borrowing.posterior_estimate, borrowing.posterior_standard_error, config['decision'], aicc)
    current_values = {r['name']: r for r in current['ranked_channels']}
    mechanisms = [('EBC', ebc_path), ('AICC', aicc_path)]
    if 'covariance' in arguments: mechanisms.append(('EBC_joint_covariance', ebc_path.with_name('correlated.py')))
    return {'product': dict(PRODUCT_SPEC), 'reconstruction_tier': 'NATIVE_REIMPLEMENTATION_NOT_HISTORICAL_SOURCE',
            'borrowing': borrowing.to_dict(), 'current_only': current, 'with_history': informed,
            'selection_changed_by_history': current['chosen_channel'] != informed['chosen_channel'],
            'channel_value_changes': [{'name': r['name'],
                'information_value_change': r['expected_decision_improvement']-current_values[r['name']]['expected_decision_improvement'],
                'net_value_change': r['net_value']-current_values[r['name']]['net_value']} for r in informed['ranked_channels']],
            'assumptions': ['One scalar estimand shared by current and historical normal estimates.',
                'EBC estimate and reported SE define a plug-in Gaussian working belief; adaptive weighting and interval calibration are not established.',
                'Future measurement errors are declared independent of ALL used evidence. Repeated or partly shared measurements of that evidence do not satisfy this adapter.',
                'Costs and affine action utility use the same units. Selection maximizes one-step expected improvement minus cost.',
                'A changed selection does not establish truth of history, acquisition effectiveness, audit risk or an audit opinion.'],
            'mechanisms': [{'name': name, 'source': str(path.relative_to(Path(__file__).resolve().parents[2])),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in mechanisms]}


def review_dependency(config):
    """Same observations, policies and decision model; remove evidence dependence."""
    preserved = evaluate(config)
    evidence = dict(config['evidence'])
    evidence['historical'] = [{**r, 'observation_id': None} for r in evidence['historical']]
    evidence['current_observation_id'] = None
    if 'covariance' in evidence:
        covariance = np.asarray(evidence['covariance'], dtype=float)
        evidence['covariance'] = np.diag(np.diag(covariance)).tolist()
    independent = evaluate({**config, 'evidence': evidence})
    return {'dependency_preserved': preserved, 'independence_assumed': independent,
            'selection_changes_if_dependency_ignored': preserved['with_history']['chosen_channel'] != independent['with_history']['chosen_channel'],
            'comparison_scope': 'Same observations, EBC policies, utilities, channels and costs. Only identities/cross-covariance are removed. Sensitivity comparison, not measured real-world policy benefit.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input'); parser.add_argument('--review', action='store_true'); parser.add_argument('--output')
    args = parser.parse_args(argv)
    try:
        raw = Path(args.input).read_bytes(); config = json.loads(raw)
        result = review_dependency(config) if args.review else evaluate(config)
        result['input_sha256'] = hashlib.sha256(raw).hexdigest()
        result['product_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        text = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n'
        if args.output:
            with Path(args.output).open('x') as handle: handle.write(text)
            print(args.output)
        else: print(text, end='')
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__': raise SystemExit(main())
