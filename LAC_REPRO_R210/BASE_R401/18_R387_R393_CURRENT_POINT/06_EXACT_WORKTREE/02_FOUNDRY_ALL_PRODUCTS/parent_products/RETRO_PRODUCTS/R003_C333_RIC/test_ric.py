import unittest

import numpy as np

from ric import assignment_equalities, certify_total_unimodularity, compare_lp_and_integer


class RICTests(unittest.TestCase):
    def test_assignment_matrix_is_totally_unimodular(self):
        matrix, _ = assignment_equalities(3)
        certificate = certify_total_unimodularity(matrix)
        self.assertTrue(certificate.is_totally_unimodular)
        self.assertTrue(certificate.theorem_applies_with_integer_rhs)

    def test_triangle_cover_exposes_determinant_two(self):
        matrix = -np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]])
        certificate = certify_total_unimodularity(matrix)
        self.assertFalse(certificate.is_totally_unimodular)
        self.assertEqual(certificate.max_absolute_subdeterminant, 2)

    def test_assignment_lp_has_zero_integrality_gap(self):
        matrix, rhs = assignment_equalities(3)
        result = compare_lp_and_integer(np.arange(9, dtype=float), equality_matrix=matrix, equality_bound=rhs)
        self.assertTrue(result.lp_solution_is_integral)
        self.assertAlmostEqual(result.integrality_gap, 0.0)

    def test_triangle_cover_lp_is_fractional(self):
        matrix = -np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]], dtype=float)
        result = compare_lp_and_integer(np.ones(3), inequality_matrix=matrix, inequality_bound=-np.ones(3))
        self.assertFalse(result.lp_solution_is_integral)
        self.assertAlmostEqual(result.lp_objective, 1.5)
        self.assertAlmostEqual(result.integer_objective, 2.0)


if __name__ == "__main__":
    unittest.main()

