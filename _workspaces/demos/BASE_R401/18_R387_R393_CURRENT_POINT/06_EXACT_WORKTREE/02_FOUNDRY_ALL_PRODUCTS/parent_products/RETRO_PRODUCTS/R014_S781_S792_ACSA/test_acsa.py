import unittest

import numpy as np

from acsa import audit_adaptive_selection


class Tests(unittest.TestCase):
    def test_adaptive_decoy_is_exposed_without_being_deleted(self):
        selection = np.tile([0.30, 0.25, 0.10], (100, 1))
        holdout = np.tile([0.30, 0.25, 0.50], (100, 1))
        result = audit_adaptive_selection(
            selection, holdout, candidate_names=["base", "real", "decoy"],
            bootstrap_samples=200, material_regret=0.01,
        )
        self.assertEqual(result.selected_candidate, "decoy")
        self.assertEqual(result.holdout_best_candidate, "real")
        self.assertAlmostEqual(result.selected_holdout_regret, 0.25)
        self.assertEqual(result.status, "ADAPTIVE_SELECTION_REGRET_DETECTED")
        self.assertEqual(len(result.holdout_mean_losses), 3)

    def test_real_winner_survives_holdout(self):
        selection = np.tile([0.40, 0.20], (40, 1))
        holdout = np.tile([0.42, 0.22], (40, 1))
        result = audit_adaptive_selection(selection, holdout, bootstrap_samples=200)
        self.assertEqual(result.selected_candidate, result.holdout_best_candidate)
        self.assertEqual(result.status, "SELECTED_CANDIDATE_SURVIVES_HOLDOUT_AUDIT")

    def test_bootstrap_is_reproducible(self):
        rng = np.random.default_rng(3)
        selection = rng.normal(size=(80, 4))
        holdout = rng.normal(size=(70, 4))
        first = audit_adaptive_selection(selection, holdout, bootstrap_samples=200, random_seed=7)
        second = audit_adaptive_selection(selection, holdout, bootstrap_samples=200, random_seed=7)
        self.assertEqual(first.selection_bootstrap_frequencies, second.selection_bootstrap_frequencies)
        self.assertEqual(first.selected_holdout_loss_bootstrap_interval_95, second.selected_holdout_loss_bootstrap_interval_95)

    def test_shape_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_adaptive_selection(np.ones((10, 2)), np.ones((10, 3)))


if __name__ == "__main__":
    unittest.main()
