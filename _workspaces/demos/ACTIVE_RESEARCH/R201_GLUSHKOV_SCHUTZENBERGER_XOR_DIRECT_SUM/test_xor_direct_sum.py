import unittest

import numpy as np

from xor_direct_sum import XorDirectSumCompiler
from wave3 import random_observable_automaton


class XorDirectSumTests(unittest.TestCase):
    def test_swapped_duplicate_is_equivalent(self):
        automaton = random_observable_automaton(np.random.default_rng(2), states=5)
        compiler = XorDirectSumCompiler([automaton, automaton])
        decision = compiler.decide((0, 1), (1, 0))
        self.assertFalse(decision.distinguishable)

    def test_returned_word_really_distinguishes(self):
        rng = np.random.default_rng(4)
        automata = [random_observable_automaton(rng, states=5) for _ in range(3)]
        compiler = XorDirectSumCompiler(automata)
        for _ in range(100):
            left = tuple(int(rng.integers(5)) for _ in automata)
            right = tuple(int(rng.integers(5)) for _ in automata)
            decision = compiler.decide(left, right)
            if decision.word is not None:
                self.assertNotEqual(
                    compiler.run_xor_output(left, decision.word),
                    compiler.run_xor_output(right, decision.word),
                )


if __name__ == "__main__":
    unittest.main()
