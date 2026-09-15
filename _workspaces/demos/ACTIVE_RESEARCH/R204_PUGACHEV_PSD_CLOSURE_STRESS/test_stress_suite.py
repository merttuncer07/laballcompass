import unittest

import numpy as np

from stress_suite import dense_transition
from automatic_psd_closure import compile_closure


class StressSuiteTests(unittest.TestCase):
    def test_dense_transition_is_stable_and_nonlocal(self):
        matrix = dense_transition(8)
        self.assertLess(np.max(np.abs(np.linalg.eigvals(matrix))), 0.95)
        self.assertGreater(np.count_nonzero(np.abs(matrix) > 1e-3), 32)

    def test_sixteen_dimensional_dictionary_is_psd_and_linear_count(self):
        closure, record = compile_closure(
            16,
            "gaussian",
            training_count=2_500,
            calibration_trajectories=0,
        )
        self.assertEqual(record["atom_count"], 36)
        self.assertGreater(np.min(np.linalg.eigvalsh(closure.covariance_atoms)), 0.0)
        self.assertGreater(record["atom_storage_reduction"], 1e12)


if __name__ == "__main__":
    unittest.main()
