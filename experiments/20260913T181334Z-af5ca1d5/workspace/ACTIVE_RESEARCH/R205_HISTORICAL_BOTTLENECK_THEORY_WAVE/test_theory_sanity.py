import unittest

import numpy as np

from theory_sanity import (
    compress_signed_responses,
    compressed_response,
    glushkov_polynomial_outputs,
    permute_edges,
    preisach_dense_output,
    preisach_prefix_output,
    recover_nested_thinning,
    recover_symmetric_low_rank,
    thinned_transition,
    two_color_core_is_unsatisfiable,
)


class HistoricalTheorySanityTests(unittest.TestCase):
    def test_nested_thinning_recovers_unknown_rate_and_chain(self):
        transition = np.array(
            [[0.72, 0.18, 0.10], [0.11, 0.76, 0.13], [0.19, 0.16, 0.65]]
        )
        retention = 0.63
        first = thinned_transition(transition, retention)
        second = thinned_transition(transition, retention**2)
        recovered_retention, recovered_transition = recover_nested_thinning(
            first, second
        )
        self.assertAlmostEqual(recovered_retention, retention, places=11)
        self.assertTrue(np.allclose(recovered_transition, transition, atol=1e-11))

    def test_bounded_degree_lift_matches_direct_automata_output(self):
        for word in ("", "a", "b", "abba", "baababa"):
            self.assertEqual(*glushkov_polynomial_outputs(word))

    def test_dense_preisach_prefix_is_exact(self):
        rng = np.random.default_rng(4)
        weights = rng.normal(size=(12, 12))
        frontier = rng.integers(-1, 12, size=12)
        self.assertAlmostEqual(
            preisach_prefix_output(weights, frontier),
            preisach_dense_output(weights, frontier),
            places=12,
        )

    def test_active_volterra_recovers_rank_three_kernel(self):
        rng = np.random.default_rng(8)
        factor = rng.normal(size=(14, 3))
        kernel = factor @ np.diag([1.7, -0.8, 0.35]) @ factor.T
        recovered = recover_symmetric_low_rank(kernel, 3, seed=13)
        self.assertTrue(np.allclose(recovered, kernel, atol=1e-9))

    def test_orbit_permutation_preserves_failure(self):
        triangle = [(0, 1), (1, 2), (0, 2)]
        permutation = {0: 5, 1: 9, 2: 7}
        self.assertTrue(two_color_core_is_unsatisfiable(triangle))
        self.assertTrue(
            two_color_core_is_unsatisfiable(permute_edges(triangle, permutation))
        )

    def test_signed_carathéodory_preserves_anchor_predictions(self):
        rng = np.random.default_rng(19)
        responses = rng.normal(size=(40, 5))
        coefficients = rng.normal(size=40)
        expected = coefficients @ responses
        compressed = compress_signed_responses(responses, coefficients)
        observed = compressed_response(compressed)
        support = sum(len(points) for _, _, points, _ in compressed)
        self.assertLessEqual(support, 2 * (responses.shape[1] + 1))
        self.assertTrue(np.allclose(observed, expected, atol=1e-9))


if __name__ == "__main__":
    unittest.main()
