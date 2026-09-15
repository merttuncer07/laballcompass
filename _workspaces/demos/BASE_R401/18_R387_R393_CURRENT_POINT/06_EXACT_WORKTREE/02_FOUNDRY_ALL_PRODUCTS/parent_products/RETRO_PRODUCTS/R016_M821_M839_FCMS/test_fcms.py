import unittest

import numpy as np

from fcms import synthesize_compatible_microstructure


PHASES = [
    [[1, 0], [0, 1]], [[-1, 0], [0, 1]],
    [[1, 0], [0, -1]], [[-1, 0], [0, -1]],
]


class Tests(unittest.TestCase):
    def test_second_order_laminate_realizes_forbidden_zero(self):
        result = synthesize_compatible_microstructure(PHASES, [[0, 0], [0, 0]], maximum_lamination_depth=3)
        self.assertLess(result.frobenius_target_error, 1e-8)
        self.assertGreaterEqual(result.laminate_depth, 2)
        self.assertEqual(result.status, "COMPATIBLE_MICROSTRUCTURE_SYNTHESIZED")
        self.assertAlmostEqual(sum(value for _, value in result.phase_fractions), 1.0)

    def test_every_tree_connection_is_rank_one(self):
        result = synthesize_compatible_microstructure(PHASES, [[0, 0], [0, 0]], maximum_lamination_depth=3)
        def walk(node):
            if node.phase_name is not None: return
            self.assertLessEqual(node.rank_one_residual, 1e-9)
            walk(node.left); walk(node.right)
        walk(result.tree)

    def test_fabrication_resolution_can_be_the_only_blocker(self):
        result = synthesize_compatible_microstructure(
            PHASES, [[0, 0], [0, 0]], maximum_lamination_depth=3,
            specimen_thickness=1, minimum_fabrication_feature=.3,
        )
        self.assertLess(result.frobenius_target_error, 1e-8)
        self.assertEqual(result.status, "MATHEMATICALLY_REALIZABLE_BELOW_FABRICATION_RESOLUTION")

    def test_shape_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            synthesize_compatible_microstructure(PHASES, [[0, 0, 0], [0, 0, 0]])


if __name__ == "__main__":
    unittest.main()
