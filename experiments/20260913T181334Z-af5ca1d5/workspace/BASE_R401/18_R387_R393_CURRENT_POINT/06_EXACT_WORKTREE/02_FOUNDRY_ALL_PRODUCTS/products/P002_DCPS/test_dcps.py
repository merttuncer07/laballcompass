import unittest
import numpy as np

if __package__:
    from .dcps import (
        build_decision_closed_representation,
        transform_sequence,
        learn_constrained_policy_from_representation,
        evaluate_representation_predictors,
    )
else:
    from dcps import (
        build_decision_closed_representation,
        transform_sequence,
        learn_constrained_policy_from_representation,
        evaluate_representation_predictors,
    )


def order2_process(prob_one, seed=0, length=30000):
    rng = np.random.default_rng(seed)
    seq = [0, 1]
    for _ in range(length - 2):
        context = (seq[-2], seq[-1])
        seq.append(int(rng.random() < prob_one[context]))
    return seq


SAFE = {(0, 0): .10, (0, 1): .80, (1, 0): .20, (1, 1): .90}
INCOMPATIBLE = {(0, 0): .10, (0, 1): .20, (1, 0): .80, (1, 1): .90}
UTIL = np.eye(2)


def parity_process(seed=7, length=30000):
    rng = np.random.default_rng(seed)
    sequence = [0, 1]
    for _ in range(length - 2):
        same = sequence[-1] == sequence[-2]
        p_one = .8 if same else .2
        sequence.append(int(rng.random() < p_one))
    return sequence


def asset_returns(sequence, seed=0):
    rng = np.random.default_rng(seed)
    sym = np.asarray(sequence)
    base = np.where(sym[:, None] == np.array([0, 1])[None, :], .012, -.003)
    return base + rng.normal(scale=.003, size=base.shape)


class DCPSTests(unittest.TestCase):
    def test_decision_merge_can_preserve_predictive_closure(self):
        rep = build_decision_closed_representation(
            order2_process(SAFE, seed=1), UTIL, history_length=2,
            probability_tolerance=.035, maximum_decision_regret=0,
        )
        self.assertEqual(rep.predictive_state_result.predictive_state_count, 4)
        self.assertEqual(rep.initial_decision_cluster_count, 2)
        self.assertEqual(rep.decision_closed_cluster_count, 2)
        self.assertEqual(rep.closure_refinement_splits, 0)
        self.assertTrue(rep.closure_certified)
        self.assertEqual(rep.status, "DECISION_COMPRESSION_PRESERVES_PREDICTIVE_CLOSURE")
        self.assertAlmostEqual(rep.maximum_decision_regret, 0.0, places=12)

    def test_decision_safe_but_dynamically_invalid_merge_is_refined(self):
        rep = build_decision_closed_representation(
            order2_process(INCOMPATIBLE, seed=2), UTIL, history_length=2,
            probability_tolerance=.035, maximum_decision_regret=0,
        )
        self.assertEqual(rep.predictive_state_result.predictive_state_count, 4)
        self.assertEqual(rep.initial_decision_cluster_count, 2)
        self.assertEqual(rep.decision_closed_cluster_count, 4)
        self.assertGreaterEqual(rep.closure_refinement_splits, 2)
        self.assertTrue(rep.closure_certified)
        self.assertEqual(rep.status, "DECISION_COMPRESSION_REFINED_TO_RESTORE_CLOSURE")

    def test_nonclosed_parent_is_preserved_as_nonclosed(self):
        rep = build_decision_closed_representation(
            parity_process(), UTIL, history_length=2,
            probability_tolerance=.035, maximum_decision_regret=0,
        )
        self.assertFalse(rep.closure_certified)
        self.assertEqual(rep.status, "PARENT_PREDICTIVE_PARTITION_NOT_CLOSED")
        self.assertGreater(rep.predictive_state_result.closure_violation_rate, .1)

    def test_sequence_transform_is_causal_and_one_hot(self):
        discovery = order2_process(SAFE, seed=3, length=20000)
        rep = build_decision_closed_representation(
            discovery, UTIL, history_length=2, probability_tolerance=.035, maximum_decision_regret=0,
        )
        probe = order2_process(SAFE, seed=4, length=100)
        fm = transform_sequence(rep, probe)
        arr = fm.as_array()
        self.assertEqual(arr.shape, (98, 2))
        self.assertTrue(np.allclose(arr.sum(axis=1), 1))
        self.assertEqual(fm.row_indices[0], 2)
        self.assertEqual(len(fm.unresolved_row_indices), 0)

    def test_decision_closed_features_feed_constraint_certified_capl(self):
        discovery = order2_process(SAFE, seed=5, length=20000)
        rep = build_decision_closed_representation(
            discovery, UTIL, history_length=2, probability_tolerance=.035, maximum_decision_regret=0,
        )
        train_seq = order2_process(SAFE, seed=6, length=700)
        val_seq = order2_process(SAFE, seed=7, length=1000)
        result = learn_constrained_policy_from_representation(
            rep, train_seq, asset_returns(train_seq, 8), val_seq, asset_returns(val_seq, 9),
            maximum_asset_weight=.9, maximum_turnover=.8, risk_aversion=2,
            transaction_cost=.0002, population_size=30, generations=8, seed=4,
        )
        audit = result.validation_action_audit
        self.assertEqual((audit.sum_violations, audit.lower_bound_violations,
                          audit.upper_bound_violations, audit.turnover_violations), (0, 0, 0, 0))
        self.assertGreater(result.validation_objective_improvement_vs_equal_weight, 0)

    def test_dlew_evaluates_resolution_tradeoff_without_fabricated_latent_labels(self):
        discovery = order2_process(SAFE, seed=10, length=20000)
        rep = build_decision_closed_representation(
            discovery, UTIL, history_length=2, probability_tolerance=.035, maximum_decision_regret=0,
        )
        fit_seq = order2_process(SAFE, seed=11, length=2500)
        sel_seq = order2_process(SAFE, seed=12, length=1200)
        val_seq = order2_process(SAFE, seed=13, length=1400)
        result = evaluate_representation_predictors(
            rep,
            fit_seq, asset_returns(fit_seq, 14),
            sel_seq, asset_returns(sel_seq, 15),
            val_seq, asset_returns(val_seq, 16),
            [[1, 0], [0, 1]], initial_action_exposure=[.5, .5], transaction_cost=.0001,
        )
        self.assertEqual(result.status, "REPRESENTATION_PREDICTORS_EVALUATED_WITHOUT_FALLBACKS")
        val = {x.name: x for x in result.decision_loss.validation_candidates}
        self.assertLess(val["decision_closed"].mean_decision_regret, val["memoryless"].mean_decision_regret)
        self.assertLessEqual(val["decision_closed"].mean_decision_regret, val["raw_context"].mean_decision_regret + .002)

    def test_unseen_contexts_are_not_silently_imputed_for_capl(self):
        discovery = order2_process(SAFE, seed=17, length=20000)
        rep = build_decision_closed_representation(
            discovery, UTIL, history_length=2, probability_tolerance=.035, maximum_decision_regret=0,
        )
        train_seq = order2_process(SAFE, seed=18, length=100)
        val_seq = list(order2_process(SAFE, seed=19, length=100))
        val_seq[10] = 2
        with self.assertRaises(ValueError):
            learn_constrained_policy_from_representation(
                rep, train_seq, asset_returns(train_seq, 20), val_seq, np.zeros((100, 2)),
                maximum_asset_weight=.9, maximum_turnover=.8, risk_aversion=2,
                transaction_cost=.0002, population_size=10, generations=1, seed=4,
            )


if __name__ == "__main__":
    unittest.main()
