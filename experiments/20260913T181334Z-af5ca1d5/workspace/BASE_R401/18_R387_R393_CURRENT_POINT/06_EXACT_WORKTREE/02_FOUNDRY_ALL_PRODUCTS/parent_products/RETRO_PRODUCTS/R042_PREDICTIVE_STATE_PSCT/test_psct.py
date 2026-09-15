import unittest

import numpy as np

from psct import discover_predictive_states


def grouped_markov(seed=42, length=20000):
    rng = np.random.default_rng(seed)
    matrix = np.array([
        [.45, .45, .05, .05], [.45, .45, .05, .05],
        [.10, .10, .40, .40], [.10, .10, .40, .40],
    ])
    sequence = [0]
    for _ in range(length - 1):
        sequence.append(int(rng.choice(4, p=matrix[sequence[-1]])))
    return sequence


def parity_process(seed=7, length=30000):
    rng = np.random.default_rng(seed)
    sequence = [0, 1]
    for _ in range(length - 2):
        same = sequence[-1] == sequence[-2]
        p_one = .8 if same else .2
        sequence.append(int(rng.random() < p_one))
    return sequence


class Tests(unittest.TestCase):
    def test_observable_symbols_collapse_to_closed_predictive_states(self):
        result = discover_predictive_states(grouped_markov(), history_length=1, probability_tolerance=.035)
        self.assertEqual(result.predictive_state_count, 2)
        self.assertEqual(result.closure_violation_rate, 0)
        self.assertEqual(result.status, "PREDICTIVE_STATE_CLOSURE_CERTIFIED_ON_OBSERVED_CONTEXTS")

    def test_good_one_step_partition_can_fail_recursive_closure(self):
        result = discover_predictive_states(parity_process(), history_length=2, probability_tolerance=.035)
        self.assertEqual(result.predictive_state_count, 2)
        self.assertGreater(result.closure_violation_rate, .1)
        self.assertEqual(result.status, "PREDICTIVE_PARTITION_FAILS_CLOSURE")

    def test_predictive_state_beats_memoryless_log_loss(self):
        result = discover_predictive_states(grouped_markov(), history_length=1, probability_tolerance=.035)
        self.assertGreater(result.predictive_log_loss_improvement, .05)

    def test_single_symbol_sequence_is_rejected(self):
        with self.assertRaises(ValueError):
            discover_predictive_states([1] * 100, history_length=1, probability_tolerance=.1)


if __name__ == "__main__":
    unittest.main()
