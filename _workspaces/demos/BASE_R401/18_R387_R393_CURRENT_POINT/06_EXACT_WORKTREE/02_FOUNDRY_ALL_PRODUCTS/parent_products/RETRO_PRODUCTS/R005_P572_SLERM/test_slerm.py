import unittest

import numpy as np

from slerm import monitor_lock_in


class Tests(unittest.TestCase):
    def test_energy_transferring_lock_is_detected(self):
        fs = 100.; t = np.arange(0, 20, 1/fs)
        force = np.sin(2*np.pi*2*t); displacement = -np.cos(2*np.pi*2*t)
        result = monitor_lock_in(force, displacement, sample_rate=fs, window_samples=1000, step_samples=500, dangerous_response_rms=.5)
        self.assertEqual(result.status, "ENERGY_TRANSFERRING_LOCK_IN_DETECTED")
        self.assertGreater(result.dangerous_window_fraction, .9)

    def test_frequency_mismatch_is_not_lock(self):
        fs = 100.; t = np.arange(0, 20, 1/fs)
        result = monitor_lock_in(np.sin(2*np.pi*2*t), np.sin(2*np.pi*3*t), sample_rate=fs, window_samples=1000, step_samples=500, dangerous_response_rms=.2)
        self.assertEqual(result.status, "NO_LOCK_IN_DETECTED")

    def test_frequency_lock_without_amplitude_is_separate(self):
        fs = 100.; t = np.arange(0, 20, 1/fs)
        result = monitor_lock_in(np.sin(2*np.pi*2*t), -.01*np.cos(2*np.pi*2*t), sample_rate=fs, window_samples=1000, step_samples=500, dangerous_response_rms=.5)
        self.assertEqual(result.status, "FREQUENCY_LOCK_WITHOUT_DANGEROUS_TRANSFER")

    def test_mismatched_vectors_are_rejected(self):
        with self.assertRaises(ValueError):
            monitor_lock_in([1]*20, [1]*19, sample_rate=1, window_samples=10, step_samples=5, dangerous_response_rms=1)


if __name__ == "__main__":
    unittest.main()
