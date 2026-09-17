import math
import numpy as np
import pytest

from acsa import audit_adaptive_selection


def test_tiebreak_audits_the_selected_column_and_its_interval():
    r = audit_adaptive_selection([[0,0],[0,0]], [[9,0],[9,2],[9,4]],
        candidate_names=['a','b'], selection_tiebreak_scores=[[-1,0],[0,0]],
        bootstrap_samples=200, random_seed=0)
    assert r.selected_candidate == 'b'
    assert r.selected_holdout_loss == 2
    assert r.selected_holdout_regret == 0
    assert r.pointwise_standard_error == pytest.approx(2/math.sqrt(3))
    assert r.selected_holdout_loss_bootstrap_interval_95[1] <= 4
    assert 'maximum_mean_tiebreak_score' in r.selection_rule


def test_default_rule_still_uses_first_equal_loss_column():
    r = audit_adaptive_selection([[0,0],[0,0]], [[9,0],[9,2]],
        candidate_names=['a','b'], bootstrap_samples=100)
    assert r.selected_candidate == 'a'
    assert r.selection_bootstrap_frequencies == (1.,0.)


def test_secondary_score_cannot_override_primary_loss():
    r = audit_adaptive_selection([[0,1],[0,1]], [[0,1],[0,1]],
        selection_tiebreak_scores=[[-1e9,1e9],[-1e9,1e9]], bootstrap_samples=100)
    assert r.selected_candidate == 'candidate_0'


def test_identical_loss_and_score_retains_column_order():
    r = audit_adaptive_selection([[0,0],[0,0]], [[0,0],[0,0]],
        selection_tiebreak_scores=[[7,7],[7,7]], bootstrap_samples=100)
    assert r.selection_bootstrap_frequencies == (1.,0.)


def test_bootstrap_preserves_loss_score_pairs_and_repeats_full_selection_rule():
    # Four equiprobable size-two resamples: (0,0), (0,1), (1,0), (1,1).
    # First three choose a, last chooses b; exact bootstrap probability is 3/4.
    r = audit_adaptive_selection([[0,1],[1,0]], [[0,0],[0,0]],
        candidate_names=['a','b'], selection_tiebreak_scores=[[2,0],[0,1]],
        bootstrap_samples=4000, random_seed=84)
    assert r.selected_candidate == 'a'
    assert r.selection_bootstrap_frequencies[0] == pytest.approx(.75, abs=.03)
    assert r.selection_fragility == pytest.approx(.25, abs=.03)


@pytest.mark.parametrize('scores', [[[0,1]], [[0,float('nan')],[0,1]], [[0,1],[0,float('inf')]]])
def test_invalid_tiebreak_matrices_rejected(scores):
    with pytest.raises(ValueError, match='selection_tiebreak_scores'):
        audit_adaptive_selection([[0,0],[0,0]], [[0,0],[0,0]],
            selection_tiebreak_scores=scores, bootstrap_samples=100)


def test_holdout_outcomes_cannot_change_selection_or_fragility():
    args=dict(selection_losses=[[0,1],[1,0]], selection_tiebreak_scores=[[2,0],[0,1]],
              bootstrap_samples=200, random_seed=7)
    a=audit_adaptive_selection(holdout_losses=[[0,100],[0,100]], **args)
    b=audit_adaptive_selection(holdout_losses=[[100,0],[100,0]], **args)
    assert a.selected_candidate == b.selected_candidate
    assert a.selection_bootstrap_frequencies == b.selection_bootstrap_frequencies
    assert a.selected_holdout_regret == 0 and b.selected_holdout_regret == 100


@pytest.mark.parametrize('threshold', [float('nan'), float('inf'), -float('inf'), -1.0])
def test_invalid_material_regret_rejected(threshold):
    with pytest.raises(ValueError, match='material_regret must be finite'):
        audit_adaptive_selection([[0,1],[0,1]], [[1,0],[1,0]],
            material_regret=threshold, bootstrap_samples=100)
