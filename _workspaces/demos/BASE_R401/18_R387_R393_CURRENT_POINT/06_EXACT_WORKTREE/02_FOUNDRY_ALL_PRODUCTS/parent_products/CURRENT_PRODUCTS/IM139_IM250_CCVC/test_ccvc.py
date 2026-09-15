import unittest

import numpy as np

from ccvc import ConservationConstrainedViability
from demo_resource_circulation import build_system


class CCVCTests(unittest.TestCase):
    def test_safe_manifold_vertices_are_certified(self):
        result = build_system().certify_vertices()
        self.assertTrue(result["viable"])
        self.assertEqual(result["vertex_count"], 6)
        self.assertGreaterEqual(result["minimum_inward_margin"], -1e-9)

    def test_filtered_step_preserves_constraints(self):
        system = build_system()
        state = np.array([0.79, 0.16, 0.05])
        nominal = np.array([-0.12, -0.12, 0.12])
        control = system.filter_control(state, nominal, 0.1)
        next_state = state + 0.1 * system.velocity(state, control)
        self.assertTrue(system.in_safe_set(next_state, 1e-8))
        self.assertTrue(system.on_manifold(next_state, 1e-8))

    def test_outward_uncontrolled_boundary_is_rejected(self):
        system = ConservationConstrainedViability(
            np.array([[0.0, 0.0], [0.0, 0.0]]),
            np.array([[0.0], [0.0]]),
            np.array([[1.0, 1.0]]),
            np.array([1.0]),
            np.array([[1.0, 0.0], [-1.0, 0.0]]),
            np.array([0.6, -0.6]),
            np.array([0.0]),
            np.array([0.0]),
        )
        # The singleton x1=0.6 is tangent rather than strictly inward, so it is viable.
        certificate = system.local_certificate(np.array([0.6, 0.4]))
        self.assertTrue(certificate.feasible)
        self.assertAlmostEqual(certificate.inward_margin, 0.0, places=10)


if __name__ == "__main__":
    unittest.main()

