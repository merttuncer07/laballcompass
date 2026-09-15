import unittest

import numpy as np

from recursive_closure import compile_recursive_closure


class RecursiveClosureTests(unittest.TestCase):
    def test_closure_returns_positive_variance(self):
        closure = compile_recursive_closure("skew", seed=3)
        mean, variance = closure.update(
            np.zeros(20), np.ones(20), np.linspace(-2, 2, 20), cubic=0.18
        )
        self.assertTrue(np.all(np.isfinite(mean)))
        self.assertTrue(np.all(variance > 0))


if __name__ == "__main__":
    unittest.main()
