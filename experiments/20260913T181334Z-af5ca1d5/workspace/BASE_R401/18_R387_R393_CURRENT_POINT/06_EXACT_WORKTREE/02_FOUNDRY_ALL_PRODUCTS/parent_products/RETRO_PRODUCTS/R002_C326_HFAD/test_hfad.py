import unittest

import numpy as np

from demo_flow_attribution import build_complex
from hfad import HodgeFlowAttributionDecomposer


class HFADTests(unittest.TestCase):
    def test_recovers_local_and_global_cycles(self):
        boundary_1, boundary_2 = build_complex()
        potential = boundary_1.T @ np.arange(7, dtype=float)
        local = 2.0 * boundary_2[:, 0]
        harmonic = np.zeros(8)
        harmonic[4:8] = 3.0
        result = HodgeFlowAttributionDecomposer(boundary_1, boundary_2).decompose(potential + local + harmonic)
        np.testing.assert_allclose(result.local_cycle_flow, local, atol=1e-9)
        np.testing.assert_allclose(result.harmonic_flow, harmonic, atol=1e-9)

    def test_components_reconstruct_observed_flow(self):
        boundary_1, boundary_2 = build_complex()
        flow = np.array([1.0, -2.0, 0.5, 3.0, -1.0, 2.0, 4.0, -0.5])
        result = HodgeFlowAttributionDecomposer(boundary_1, boundary_2).decompose(flow)
        reconstructed = result.potential_flow + result.local_cycle_flow + result.harmonic_flow
        np.testing.assert_allclose(reconstructed, flow, atol=1e-10)

    def test_cycle_components_have_zero_node_divergence(self):
        boundary_1, boundary_2 = build_complex()
        result = HodgeFlowAttributionDecomposer(boundary_1, boundary_2).decompose(np.arange(8, dtype=float))
        self.assertLess(result.divergence_residual_for_cycles, 1e-9)

    def test_rejects_invalid_face_boundary(self):
        boundary_1, boundary_2 = build_complex()
        boundary_2[3, 0] = 1.0
        with self.assertRaises(ValueError):
            HodgeFlowAttributionDecomposer(boundary_1, boundary_2)


if __name__ == "__main__":
    unittest.main()

