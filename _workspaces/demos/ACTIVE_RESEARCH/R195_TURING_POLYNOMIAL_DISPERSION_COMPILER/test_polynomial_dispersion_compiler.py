import unittest

import numpy as np

from polynomial_dispersion_compiler import PolynomialDispersionCompiler


class TestPolynomialDispersionCompiler(unittest.TestCase):
    def test_quartic_crossing_matches_closed_form(self):
        drive, bending = 1.7, 0.8
        compiler = PolynomialDispersionCompiler([0.0, drive, -bending])
        for n in (2, 4, 7):
            roots = compiler.crossing_q(n, n + 1, (1e-7, 10.0))
            expected = drive / (bending * (n * n + (n + 1) ** 2))
            self.assertTrue(any(abs(root - expected) < 1e-11 for root in roots))

    def test_compiled_margin_matches_dense_oracle(self):
        compiler = PolynomialDispersionCompiler([0.0, 1.4, -0.7, -0.08])
        design = compiler.design(6, range(1, 12), (0.002, 0.15))
        oracle = compiler.dense_oracle(6, range(1, 12), (0.002, 0.15), samples=200_001)
        # The algebraic candidate can be slightly better than a finite dense grid.
        self.assertGreaterEqual(design.separation_margin, oracle["margin"] - 2e-10)
        self.assertLess(abs(design.q - oracle["q"]), 2e-6)

    def test_quench_sign_separates_target(self):
        compiler = PolynomialDispersionCompiler([0.0, 1.5, -0.9])
        design = compiler.design(5, range(1, 10), (0.003, 0.2))
        self.assertGreater(design.target_quench_rate, 0.0)
        self.assertLess(design.worst_rival_quench_rate, 0.0)
        self.assertAlmostEqual(
            design.target_quench_rate, -design.worst_rival_quench_rate, places=12
        )

    def test_no_dominant_window_rejected(self):
        compiler = PolynomialDispersionCompiler([0.0, -1.0])
        with self.assertRaises(ValueError):
            compiler.design(5, range(1, 7), (0.01, 0.2))

    def test_zero_width_interval_matches_point_design(self):
        coefficients = np.array([0.0, 1.5, -0.9, -0.04])
        compiler = PolynomialDispersionCompiler(coefficients)
        point = compiler.design(5, range(1, 11), (0.003, 0.2))
        robust = compiler.design_interval(
            5, range(1, 11), (0.003, 0.2), coefficients, coefficients
        )
        self.assertAlmostEqual(point.q, robust.q, places=11)
        self.assertAlmostEqual(point.separation_margin, robust.separation_margin, places=11)
        self.assertTrue(robust.robust_interval)

    def test_interval_quench_separates_all_box_corners(self):
        middle = np.array([0.0, 1.5, -0.9])
        radius = np.array([0.01, 0.02, 0.01])
        compiler = PolynomialDispersionCompiler(middle)
        design = compiler.design_interval(
            5, range(1, 10), (0.003, 0.2), middle - radius, middle + radius
        )
        for bits in range(8):
            corner = np.where(
                [(bits >> j) & 1 for j in range(3)], middle + radius, middle - radius
            )
            model = PolynomialDispersionCompiler(corner)
            target = float(model.modal_rate_q(5, design.q) + design.additive_quench)
            rivals = [
                float(model.modal_rate_q(m, design.q) + design.additive_quench)
                for m in range(1, 10)
                if m != 5
            ]
            self.assertGreater(target, 0.0)
            self.assertLess(max(rivals), 0.0)

    def test_shape_interval_certifies_all_box_corners_with_microprobe(self):
        middle = np.array([0.2, 1.5, -0.9])
        radius = np.array([0.15, 0.04, 0.015])
        compiler = PolynomialDispersionCompiler(middle)
        design = compiler.design_shape_interval(
            5, range(1, 10), (0.003, 0.2), middle - radius, middle + radius
        )
        for bits in range(8):
            corner = np.where(
                [(bits >> j) & 1 for j in range(3)], middle + radius, middle - radius
            )
            model = PolynomialDispersionCompiler(corner)
            target = float(model.modal_rate_q(5, design.q))
            rivals = {
                m: float(model.modal_rate_q(m, design.q))
                for m in range(1, 10)
                if m != 5
            }
            rival = max(rivals.values())
            self.assertGreaterEqual(target - rival, design.certified_separation_margin - 1e-10)
            quench = compiler.microprobe_quench(target, rival)
            self.assertGreater(target + quench, 0.0)
            self.assertLess(rival + quench, 0.0)


if __name__ == "__main__":
    unittest.main()
