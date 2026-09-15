import unittest

import numpy as np

from dlew import evaluate_decision_models


def construction(seed=44, training_size=300, validation_size=600):
    rng = np.random.default_rng(seed)
    def sample(size):
        common = .001 + rng.normal(scale=.002, size=size)
        spread = rng.normal(scale=.010, size=size)
        outcomes = np.column_stack((common + spread, common - spread))
        rmse_model = outcomes + rng.normal(scale=.006, size=outcomes.shape)
        common_bias = rng.normal(loc=.030, scale=.003, size=(size, 1))
        decision_model = outcomes + common_bias + rng.normal(scale=.001, size=outcomes.shape)
        return outcomes, {"lowest_rmse": rmse_model, "decision_boundary": decision_model}
    train_y, train_predictions = sample(training_size)
    val_y, val_predictions = sample(validation_size)
    return train_predictions, train_y, val_predictions, val_y


class Tests(unittest.TestCase):
    def test_prediction_and_decision_rankings_can_diverge(self):
        result = evaluate_decision_models(
            *construction(), [[1, 0], [0, 1]], initial_action_exposure=[.5, .5], transaction_cost=.0002
        )
        self.assertEqual(result.selected_by_training_prediction_rmse, "lowest_rmse")
        self.assertEqual(result.selected_by_training_decision_loss, "decision_boundary")
        self.assertTrue(result.selection_ranking_diverges)

    def test_decision_selection_reduces_untouched_regret(self):
        result = evaluate_decision_models(
            *construction(), [[1, 0], [0, 1]], initial_action_exposure=[.5, .5], transaction_cost=.0002
        )
        self.assertGreater(result.validation_regret_reduction_from_decision_selection, 0)

    def test_every_induced_action_and_turnover_is_retained(self):
        values = construction(validation_size=80)
        result = evaluate_decision_models(
            *values, [[1, 0], [0, 1]], initial_action_exposure=[.5, .5], transaction_cost=.001
        )
        for candidate in result.validation_candidates:
            self.assertEqual(len(candidate.actions), 80)
            self.assertGreaterEqual(candidate.total_turnover, 0)

    def test_candidate_shape_mismatch_is_rejected(self):
        train_p, train_y, val_p, val_y = construction()
        val_p["lowest_rmse"] = val_p["lowest_rmse"][:, :1]
        with self.assertRaises(ValueError):
            evaluate_decision_models(
                train_p, train_y, val_p, val_y, [[1, 0], [0, 1]], initial_action_exposure=[.5, .5]
            )


if __name__ == "__main__":
    unittest.main()
