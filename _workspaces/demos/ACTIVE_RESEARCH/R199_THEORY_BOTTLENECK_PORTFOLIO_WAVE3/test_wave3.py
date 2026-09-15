import unittest

import numpy as np

from wave3 import (
    FiniteResponseAutomaton,
    characterization_set,
    compile_extremal_threshold,
    random_observable_automaton,
)


class WaveThreeTests(unittest.TestCase):
    def test_rank_automaton_remains_finite(self):
        rng = np.random.default_rng(1)
        automaton = FiniteResponseAutomaton(4, "rank", rng)
        for reward in np.linspace(-2, 2, 1000):
            action = automaton.choose()
            automaton.update(action, float(reward))
        self.assertTrue(np.all(automaton.state >= 0))
        self.assertTrue(np.all(automaton.state <= 255))

    def test_characterization_separates_states(self):
        rng = np.random.default_rng(2)
        automaton = random_observable_automaton(rng)
        words = characterization_set(automaton)
        fingerprints = [
            tuple(automaton.run_output(state, word) for word in words)
            for state in range(automaton.states)
        ]
        self.assertEqual(len(set(fingerprints)), automaton.states)

    def test_extremal_compiler_returns_feasible_witness(self):
        grid = np.linspace(0, 1, 31)
        result = compile_extremal_threshold(grid, mean=0.4, variance=0.05, alpha=0.2)
        weights = np.asarray(result["weights"])
        atoms = np.asarray(result["atoms"])
        self.assertAlmostEqual(float(weights.sum()), 1.0, places=7)
        self.assertAlmostEqual(float(weights @ atoms), 0.4, places=7)


if __name__ == "__main__":
    unittest.main()
