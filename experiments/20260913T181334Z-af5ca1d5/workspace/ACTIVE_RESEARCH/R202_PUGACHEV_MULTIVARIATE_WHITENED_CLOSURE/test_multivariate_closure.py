import unittest

import numpy as np

from multivariate_closure import compile_closure


class MultivariateClosureTests(unittest.TestCase):
    def test_update_is_finite_and_psd(self):
        closure = compile_closure("mixture", seed=2)
        mean = np.zeros((30, 2))
        covariance = np.repeat(np.eye(2)[None, :, :], 30, axis=0)
        measured = np.random.default_rng(3).normal(size=(30, 2))
        posterior_mean, posterior_covariance = closure.update(
            mean, covariance, measured, cubic=0.18
        )
        self.assertTrue(np.all(np.isfinite(posterior_mean)))
        self.assertTrue(np.all(np.linalg.eigvalsh(posterior_covariance) > 0))


if __name__ == "__main__":
    unittest.main()
