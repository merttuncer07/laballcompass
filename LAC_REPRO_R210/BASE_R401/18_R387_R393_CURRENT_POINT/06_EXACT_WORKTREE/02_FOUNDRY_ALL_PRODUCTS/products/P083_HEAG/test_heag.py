import copy
import math
import numpy as np
import pytest
from . import heag


def config(copies=1):
    return {'evidence': {'current_estimate': 0., 'current_standard_error': 1.,
        'historical': [{'name': 'history_'+str(i), 'estimate': 0., 'standard_error': 1., 'observation_id': 'one_observation'} for i in range(copies)]},
        'decision': {'action_names': ['hold', 'act'], 'action_slopes': [[0.], [1.]], 'action_intercepts': [0., 0.],
                     'future_error_relation': 'independent_of_evidence',
                     'channels': [{'name': 'new_measurement', 'measurement_vector': [1.], 'noise_variance': 1., 'cost': .15}]}}


def test_native_product_calls_both_canonical_parents(monkeypatch):
    ebc, _ = heag._parent('ebc'); aicc, _ = heag._parent('aicc')
    calls = []
    original_borrow, original_value = ebc.borrow_evidence, aicc.AdaptiveInformationController.channel_value
    def borrow(*args, **kwargs):
        calls.append('EBC'); return original_borrow(*args, **kwargs)
    def value(self, channel):
        calls.append('AICC'); return original_value(self, channel)
    monkeypatch.setattr(ebc, 'borrow_evidence', borrow)
    monkeypatch.setattr(aicc.AdaptiveInformationController, 'channel_value', value)
    r = heag.evaluate(config())
    assert calls == ['EBC', 'AICC', 'AICC']
    assert r['reconstruction_tier'] == 'NATIVE_REIMPLEMENTATION_NOT_HISTORICAL_SOURCE'
    assert {m['name'] for m in r['mechanisms']} == {'EBC', 'AICC'}
    assert all(len(m['sha256']) == 64 for m in r['mechanisms'])


def test_declared_copies_leave_acquisition_invariant_and_independence_can_stop_it():
    reference = heag.evaluate(config())['with_history']
    for n in (2, 5, 20):
        r = heag.review_dependency(config(n))
        assert r['dependency_preserved']['with_history'] == reference
        assert r['dependency_preserved']['with_history']['chosen_channel'] == 'new_measurement'
        assert r['independence_assumed']['with_history']['chosen_channel'] is None
        assert r['selection_changes_if_dependency_ignored']


def test_equal_estimates_with_distinct_identities_remain_separate():
    c = config(2)
    for i, r in enumerate(c['evidence']['historical']): r['observation_id'] = str(i)
    result = heag.evaluate(c)
    assert result['borrowing']['posterior_standard_error'] == pytest.approx(1/math.sqrt(3))
    assert result['with_history']['chosen_channel'] is None


def test_zero_borrowing_cap_preserves_current_only_decision():
    c = config(5); c['evidence']['borrowing_cap_ratio'] = 0.
    r = heag.evaluate(c)
    assert r['with_history'] == r['current_only']


def test_current_observation_copies_do_not_add_information():
    c = config(5); c['evidence']['current_observation_id'] = 'one_observation'
    r = heag.evaluate(c)
    assert r['with_history'] == r['current_only']
    assert r['borrowing']['current_overlap_count'] == 5


def test_conflict_suppresses_history_and_restores_acquisition():
    c = config()
    c['evidence']['historical'][0]['estimate'] = 50.
    r = heag.evaluate(c)
    assert r['borrowing']['borrowed_precision'] < 1e-100
    assert r['with_history']['chosen_channel'] == r['current_only']['chosen_channel'] == 'new_measurement'


def test_partial_covariance_flows_through_both_motors_and_matches_closed_form():
    c = config(2)
    for i, row in enumerate(c['evidence']['historical']): row['observation_id'] = str(i)
    covariance = np.full((3, 3), .8)+.2*np.eye(3)
    c['evidence'].update(covariance=covariance.tolist(), covariance_names=['current', 'history_0', 'history_1'],
                         adaptive=False, borrowing_cap_ratio=100.)
    c['decision']['channels'][0]['cost'] = .2
    result = heag.review_dependency(c)
    joint, diagonal = result['dependency_preserved'], result['independence_assumed']
    ones = np.ones(3); precision = ones@np.linalg.solve(covariance, ones); variance = 1/precision
    assert joint['borrowing']['posterior_standard_error']**2 == pytest.approx(variance)
    expected_value = variance/math.sqrt(variance+1)/math.sqrt(2*math.pi)
    assert joint['with_history']['ranked_channels'][0]['expected_decision_improvement'] == pytest.approx(expected_value)
    assert joint['with_history']['chosen_channel'] == 'new_measurement'
    assert diagonal['with_history']['chosen_channel'] is None
    assert any(m['name'] == 'EBC_joint_covariance' for m in joint['mechanisms'])


def test_cost_and_downstream_utility_control_acquisition():
    c = config()
    c['decision']['channels'][0]['cost'] = .1
    assert heag.evaluate(c)['with_history']['chosen_channel'] == 'new_measurement'
    c['decision']['channels'][0]['cost'] = .2
    assert heag.evaluate(c)['with_history']['chosen_channel'] is None
    c['decision']['channels'][0]['cost'] = 0.
    c['decision']['action_slopes'] = [[1.], [1.]]
    r = heag.evaluate(c)
    assert r['with_history']['chosen_channel'] is None
    assert r['with_history']['ranked_channels'][0]['expected_decision_improvement'] == 0.


def test_empty_history_and_no_offered_channels_are_valid():
    c = config(0); c['decision']['channels'] = []
    result = heag.evaluate(c)
    assert result['with_history'] == result['current_only']
    assert result['with_history']['chosen_channel'] is None


def test_shared_future_error_is_not_silently_treated_as_independent():
    c = config(); c['decision']['future_error_relation'] = 'shared_with_history'
    with pytest.raises(ValueError, match='shared error needs a joint model'): heag.evaluate(c)


def test_invalid_covariance_and_identity_conflicts_are_rejected():
    c = config(2); c['evidence']['historical'][1]['estimate'] = 3.
    with pytest.raises(ValueError, match='conflicting'): heag.evaluate(c)
    c = config()
    c['evidence'].update(covariance=[[1., 2.], [2., 1.]], covariance_names=['current', 'history_0'])
    with pytest.raises(ValueError, match='positive semidefinite'): heag.evaluate(c)


def test_score_placeholder_and_unknown_model_fields_rejected():
    with pytest.raises(ValueError, match='score-only'): heag.evaluate([{'name': 'a', 'score': 8}])
    c = config(); c['decision']['budget'] = 3
    with pytest.raises(ValueError): heag.evaluate(c)
    with pytest.raises(ValueError, match='budget'): heag.evaluate(config(), budget=3)
    c = config(); c['evidence']['covariance_names'] = ['current']
    with pytest.raises(ValueError, match='require'): heag.evaluate(c)


def test_review_does_not_mutate_input_or_change_costs():
    c = config(5); before = copy.deepcopy(c)
    r = heag.review_dependency(c)
    assert c == before
    assert r['dependency_preserved']['with_history']['ranked_channels'][0]['cost'] == .15
    assert r['independence_assumed']['with_history']['ranked_channels'][0]['cost'] == .15
