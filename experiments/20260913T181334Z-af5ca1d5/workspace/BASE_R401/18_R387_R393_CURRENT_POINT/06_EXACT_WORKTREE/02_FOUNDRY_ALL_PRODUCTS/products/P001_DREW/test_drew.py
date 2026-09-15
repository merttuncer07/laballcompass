import unittest

import numpy as np

if __package__:
    from .drew import (
        audit_decision_model_selection,
        decision_regret_matrix,
        explore_decision_selection_surface,
        run_reliability_workbench,
    )
else:
    from drew import (
        audit_decision_model_selection,
        decision_regret_matrix,
        explore_decision_selection_surface,
        run_reliability_workbench,
    )
if __package__:
    from .parents.dlew import evaluate_decision_models
else:
    from parents.dlew import evaluate_decision_models


def dlew_construction(seed=44, training_size=300, validation_size=600):
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


def adaptive_decoy_case(training_size=40, validation_size=80):
    train_y = np.tile([[1.0, 0.0], [0.0, 1.0]], (training_size // 2, 1))
    val_y = np.tile([[1.0, 0.0], [0.0, 1.0]], (validation_size // 2, 1))
    robust_train = train_y.copy()
    robust_train[:4] = robust_train[:4, ::-1]
    train_p = {"adaptive_decoy": train_y.copy(), "robust": robust_train}
    val_p = {"adaptive_decoy": val_y[:, ::-1].copy(), "robust": val_y.copy()}
    return train_p, train_y, val_p, val_y


class DREWTests(unittest.TestCase):
    def test_regret_adapter_matches_dlew_candidate_means(self):
        train_p, train_y, val_p, val_y = dlew_construction(validation_size=100)
        names, losses = decision_regret_matrix(
            val_p, val_y, [[1, 0], [0, 1]], initial_action_exposure=[.5, .5], transaction_cost=.0002
        )
        result = evaluate_decision_models(
            train_p, train_y, val_p, val_y, [[1, 0], [0, 1]],
            initial_action_exposure=[.5, .5], transaction_cost=.0002,
        )
        by_name = {x.name: x.mean_decision_regret for x in result.validation_candidates}
        for j, name in enumerate(names):
            self.assertAlmostEqual(float(losses[:, j].mean()), by_name[name], places=12)

    def test_decision_selection_overfit_is_exposed_on_protected_sample(self):
        train_p, train_y, val_p, val_y = adaptive_decoy_case()
        result = audit_decision_model_selection(
            train_p, train_y, val_p, val_y, [[1, 0], [0, 1]],
            initial_action_exposure=[.5, .5], bootstrap_samples=200, material_regret=.01,
        )
        self.assertEqual(result.decision_loss.selected_by_training_decision_loss, "adaptive_decoy")
        self.assertEqual(result.protected_best_candidate, "robust")
        self.assertEqual(result.adaptive_selection.status, "ADAPTIVE_SELECTION_REGRET_DETECTED")
        self.assertEqual(result.status, "DECISION_SELECTION_FAILS_PROTECTED_AUDIT")
        self.assertGreater(result.adaptive_selection.selected_holdout_regret, .5)

    def test_prediction_vs_decision_ranking_is_preserved(self):
        train_p, train_y, val_p, val_y = dlew_construction()
        result = audit_decision_model_selection(
            train_p, train_y, val_p, val_y, [[1, 0], [0, 1]],
            initial_action_exposure=[.5, .5], transaction_cost=.0002, bootstrap_samples=200,
        )
        self.assertTrue(result.decision_loss.selection_ranking_diverges)
        self.assertEqual(result.decision_loss.selected_by_training_prediction_rmse, "lowest_rmse")
        self.assertEqual(result.decision_loss.selected_by_training_decision_loss, "decision_boundary")

    def test_tdsx_finds_where_decision_selection_advantage_flips(self):
        train_p, train_y, val_p, val_y = dlew_construction(seed=7, training_size=400, validation_size=800)
        base_decision = val_p["decision_boundary"].copy()
        swapped = base_decision[:, ::-1].copy()
        def builder(params):
            q = float(params["degradation"])
            vp = dict(val_p)
            vp["decision_boundary"] = (1.0 - q) * base_decision + q * swapped
            return {
                "training_predictions": train_p,
                "training_outcomes": train_y,
                "validation_predictions": vp,
                "validation_outcomes": val_y,
                "action_payoff_exposures": [[1, 0], [0, 1]],
                "initial_action_exposure": [.5, .5],
                "transaction_cost": .0002,
            }
        surface = explore_decision_selection_surface(
            builder, {"degradation": np.linspace(0, 1, 21)}, {"degradation": 0.0}
        )
        self.assertEqual(surface.status, "TIPPING_POINT_FOUND")
        self.assertIsNotNone(surface.tipping_point)
        self.assertGreater(surface.tipping_point.parameters["degradation"], 0.0)

    def test_full_route_a_preserves_all_parent_results_and_flags(self):
        train_p, train_y, val_p, val_y = adaptive_decoy_case()
        x = np.linspace(-2, 2, 100)
        result = run_reliability_workbench(
            decision_inputs={
                "training_predictions": train_p,
                "training_outcomes": train_y,
                "validation_predictions": val_p,
                "validation_outcomes": val_y,
                "action_payoff_exposures": [[1, 0], [0, 1]],
                "initial_action_exposure": [.5, .5],
                "bootstrap_samples": 200,
                "material_regret": .01,
            },
            specification_inputs={
                "outcomes": {"y": 2 * x + 1}, "treatments": {"x": x}, "controls": {},
                "control_sets": {"none": []}, "samples": {"all": np.ones(x.size, dtype=bool)},
            },
            sensitivity_inputs={
                "evaluator": lambda p: 1.0 - p["stress"],
                "parameter_grids": {"stress": [0.0, .5, 1.0, 1.5]},
                "baseline_parameters": {"stress": 0.0}, "decision_threshold": 0.0,
            },
            divergence_inputs={
                "reference_beliefs": [[.51, .48, .01]],
                "candidate_beliefs": {"near_flip": [[.48, .51, .01]], "far_safe": [[.70, .29, .01]]},
                "state_action_utilities": [[1, 0], [0, 1], [0, 0]],
            },
            firewall_inputs={
                "modules": ["adaptive_search", "protected_eval", "diagnostic"],
                "flows": [
                    {"source": "adaptive_search", "target": "protected_eval", "gain": .4, "cut_cost": 1.0},
                    {"source": "adaptive_search", "target": "diagnostic", "gain": .2, "cut_cost": 5.0},
                ],
                "suspect_sources": ["adaptive_search"], "protected_targets": ["protected_eval"],
            },
        )
        self.assertEqual(len(result.branch_coverage), 5)
        self.assertEqual(result.status, "FULL_ROUTE_A_WITH_REVIEW_FLAGS")
        self.assertIn("ADAPTIVE_SELECTION_HOLDOUT_REGRET", result.evidence_flags)
        self.assertIn("DECISION_TIPPING_POINT_INSIDE_DECLARED_SURFACE", result.evidence_flags)
        self.assertIn("METRIC_DECISION_RANKING_INVERSION", result.evidence_flags)
        self.assertIn("PROTECTED_EVALUATION_REQUIRES_FLOW_CUT", result.evidence_flags)
        self.assertIsNotNone(result.specification_curve)

    def test_boundary_case_without_shift_survives_protected_audit(self):
        train_p, train_y, _, val_y = adaptive_decoy_case()
        val_p = {"adaptive_decoy": val_y.copy(), "robust": val_y.copy()}
        result = audit_decision_model_selection(
            train_p, train_y, val_p, val_y, [[1, 0], [0, 1]],
            initial_action_exposure=[.5, .5], bootstrap_samples=200, material_regret=.01,
        )
        self.assertEqual(result.adaptive_selection.status, "SELECTED_CANDIDATE_SURVIVES_HOLDOUT_AUDIT")
        self.assertEqual(result.adaptive_selection.selected_holdout_regret, 0.0)

    def test_interface_mismatch_is_rejected_not_silently_adapted(self):
        train_p, train_y, val_p, val_y = adaptive_decoy_case()
        val_p["adaptive_decoy"] = val_p["adaptive_decoy"][:, :1]
        with self.assertRaises(ValueError):
            audit_decision_model_selection(
                train_p, train_y, val_p, val_y, [[1, 0], [0, 1]],
                initial_action_exposure=[.5, .5], bootstrap_samples=200,
            )

    def test_empty_workbench_is_rejected(self):
        with self.assertRaises(ValueError):
            run_reliability_workbench()


if __name__ == "__main__":
    unittest.main()
