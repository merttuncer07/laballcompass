import unittest

import numpy as np

from theory_wave2 import (
    PotentialMemory,
    compile_conditional_moment,
    sample_conditional_problem,
)


class TheoryWaveTwoTests(unittest.TestCase):
    def test_conditional_compiler_is_finite(self):
        rng = np.random.default_rng(2)
        data = sample_conditional_problem(rng, "skew", 1000)
        compiler = compile_conditional_moment(
            *data, cubic=0.18, noise_variance=0.3, robust=True
        )
        estimate = compiler.predict(data[0][:20], data[1][:20], data[2][:20])
        self.assertTrue(np.all(np.isfinite(estimate)))

    def test_moment_memory_obeys_budget(self):
        rng = np.random.default_rng(3)
        memory = PotentialMemory(16, "moment")
        for _ in range(100):
            memory.add(rng.normal(size=2), rng.choice([-1.0, 1.0]))
        self.assertEqual(len(memory.weights), 16)
        self.assertTrue(np.all(memory.variances > 0))


if __name__ == "__main__":
    unittest.main()
