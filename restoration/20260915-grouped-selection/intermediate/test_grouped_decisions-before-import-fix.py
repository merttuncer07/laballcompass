import numpy as np
import pytest
from drew import audit_decision_model_selection, run_reliability_workbench


def inputs():
    return dict(training_predictions={'a': [[1, 0], [0, 1], [1, 0], [0, 1]]},
        training_outcomes=[[1, 0], [0, 1], [1, 0], [0, 1]],
        validation_predictions={'a': [[1, 0], [1, 0], [1, 0], [1, 0]]},
        validation_outcomes=[[0, 1], [0, 1], [1, 0], [1, 0]],
        action_payoff_exposures=np.eye(2), initial_action_exposure=[0, 0],
        training_groups=['s1', 's1', 's2', 's2'], validation_groups=['v1', 'v1', 'v2', 'v2'],
        bootstrap_samples=100)


def test_workbench_carries_group_semantics_to_actual_selected_candidate():
    result = run_reliability_workbench(decision_inputs=inputs()).decision_audit
    assert result.decision_selector_matches_loss_matrix
    assert result.adaptive_selection.resampling_method == 'whole_groups'
    assert result.adaptive_selection.holdout_unit_count == 2
    assert result.adaptive_selection.pointwise_standard_error == .5


@pytest.mark.parametrize('cost', [.1, float('nan'), float('inf')])
def test_grouped_sequential_paths_cannot_silently_use_fixed_row_bootstrap(cost):
    with pytest.raises(ValueError, match='transaction_cost=0'):
        audit_decision_model_selection(**inputs(), transaction_cost=cost)


def test_shared_subject_rejected_through_workbench():
    args = inputs(); args['validation_groups'] = ['s1', 's1', 'v2', 'v2']
    with pytest.raises(ValueError, match='disjoint'):
        run_reliability_workbench(decision_inputs=args)
