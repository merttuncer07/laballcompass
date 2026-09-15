import unittest

import numpy as np

from portfolio_wave1 import (
    minimum_capacity_marginal,
    project_two_additive_capacity,
    run_choquet,
    run_steinbuch,
    run_volterra,
)


class PortfolioWaveOneTests(unittest.TestCase):
    def test_signed_capacity_projection_is_exactly_monotone(self):
        a = np.array([-0.2, 0.05, 0.1])
        b = np.array([-0.4, 0.25])
        pairs = [(0, 1), (1, 2)]
        pa, pb = project_two_additive_capacity(a, b, pairs)
        self.assertGreaterEqual(minimum_capacity_marginal(pa, pb, pairs), -1e-9)
        self.assertAlmostEqual(float(pa.sum() + pb.sum()), 1.0, places=9)

    def test_steinbuch_wave_runs(self):
        result = run_steinbuch()["summary"]
        self.assertEqual(result["case_count"], 48)

    def test_choquet_wave_runs_and_certifies(self):
        result = run_choquet()["summary"]
        self.assertEqual(result["exact_monotonicity_certificates"], result["case_count"])

    def test_volterra_reduces_parameters(self):
        result = run_volterra()["summary"]
        self.assertGreater(result["parameter_reduction"], 0.5)


if __name__ == "__main__":
    unittest.main()
