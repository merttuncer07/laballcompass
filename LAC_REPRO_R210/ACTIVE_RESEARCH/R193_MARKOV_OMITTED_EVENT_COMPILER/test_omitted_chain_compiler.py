import unittest

import numpy as np

from omitted_chain_compiler import (
    OmittedEventChainCompiler,
    invert_observed_transition,
    observed_transition,
    row_stochastic,
)


class TestOmittedChainCompiler(unittest.TestCase):
    def test_population_roundtrip(self):
        rng = np.random.default_rng(9)
        p = row_stochastic(rng.random((6, 6)))
        for rate in (0.0, 0.2, 0.6, 0.85):
            q = observed_transition(p, rate)
            recovered = invert_observed_transition(q, rate, project=False)
            np.testing.assert_allclose(recovered, p, atol=3e-12, rtol=3e-12)

    def test_rows_remain_stochastic(self):
        rng = np.random.default_rng(12)
        q = row_stochastic(rng.random((4, 4)))
        p = invert_observed_transition(q, 0.7, project=True)
        np.testing.assert_allclose(p.sum(axis=1), 1.0, atol=1e-12)
        self.assertGreaterEqual(float(p.min()), 0.0)

    def test_compiler_fits_and_reports_contract(self):
        retained = np.tile(np.array([0, 1, 2, 1, 0, 2], dtype=np.int64), 30)
        model = OmittedEventChainCompiler(0.4).fit(retained, 3)
        self.assertEqual(model.transition_.shape, (3, 3))
        self.assertIn("externally supplied", model.diagnostics()["identifiability_warning"])

    def test_invalid_omission_rejected(self):
        with self.assertRaises(ValueError):
            OmittedEventChainCompiler(1.0)


if __name__ == "__main__":
    unittest.main()
