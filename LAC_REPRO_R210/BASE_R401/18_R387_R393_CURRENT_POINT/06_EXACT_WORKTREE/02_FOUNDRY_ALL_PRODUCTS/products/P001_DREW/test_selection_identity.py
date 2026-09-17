import pytest
import numpy as np

if __package__:
    from .drew import audit_decision_model_selection, _decision_matrices
else:
    from drew import audit_decision_model_selection, _decision_matrices


def tied_decision(holdout):
    predictions={'a':[[0,1],[0,1]], 'b':[[1,0],[1,0]]}
    return audit_decision_model_selection(predictions, [[0,0],[1,0]], predictions, holdout,
        [[1,0],[0,1]], initial_action_exposure=[.5,.5], transaction_cost=1,
        bootstrap_samples=200)


def test_a_good_selected_model_is_not_failed_using_another_models_holdout():
    r=tied_decision([[0,0],[3,0]])
    assert r.decision_loss.selected_by_training_decision_loss == 'b'
    assert r.adaptive_selection.selected_candidate == 'b'
    assert r.adaptive_selection.selected_holdout_regret == 0
    assert r.status == 'DECISION_SELECTION_SURVIVES_PROTECTED_AUDIT'
    assert r.decision_selector_matches_loss_matrix


def test_a_bad_selected_model_is_not_hidden_by_another_models_holdout():
    r=tied_decision([[0,0],[0,3]])
    assert r.adaptive_selection.selected_candidate == 'b'
    assert r.adaptive_selection.selected_holdout_regret == .5
    assert r.status == 'DECISION_SELECTION_FAILS_PROTECTED_AUDIT'


def test_fragility_repeats_the_payoff_tiebreak_on_selection_resamples():
    r=tied_decision([[0,0],[3,0]])
    # The two original losses tie. Except for resampling the first row twice,
    # b has higher realized payoff; a wins the remaining complete tie.
    assert r.adaptive_selection.selection_bootstrap_frequencies[1] == pytest.approx(.75, abs=.09)
    assert r.adaptive_selection.selection_fragility == pytest.approx(.25, abs=.09)


def test_regret_and_payoff_matrices_match_both_dlew_metrics():
    predictions={'a':[[0,1],[0,1]], 'b':[[1,0],[1,0]]}
    names,losses,payoffs=_decision_matrices(predictions, [[0,0],[1,0]],
        [[1,0],[0,1]], initial_action_exposure=[.5,.5], transaction_cost=1)
    r=tied_decision([[0,0],[3,0]])
    by_name={x.name:x for x in r.decision_loss.training_candidates}
    for j,name in enumerate(names):
        assert losses[:,j].mean() == by_name[name].mean_decision_regret
        assert payoffs[:,j].mean() == by_name[name].mean_realized_payoff
    np.testing.assert_array_equal(losses,[[0,0],[0,0]])
    np.testing.assert_array_equal(payoffs,[[-1,-1],[0,1]])
