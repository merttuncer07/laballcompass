from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

import probe_transfer
from probe_transfer import (
    FactorModel,
    OracleMeter,
    build_runner,
    fit_factor_model,
    hand_verification,
    make_ground_truth,
    measure_linear,
    measure_offset,
    orthonormal_columns,
    probe_bilinear,
    probe_core,
    probe_image,
    run_case,
)


class TestRunnerReplication(unittest.TestCase):
    def test_build_runner_replications_match_mean(self):
        rng = np.random.default_rng(0)
        h, offset, linear = make_ground_truth(4, 2, 3.0, rng)
        runner = build_runner(h, offset, linear, 0.5, rng)
        z = rng.normal(size=4)
        samples = runner(z, 200_000)
        self.assertEqual(samples.shape, (200_000,))
        mean = float(np.mean(samples))
        expected = offset + z @ linear + z @ h @ z
        self.assertLess(abs(mean - expected), 0.01)

    def test_single_query_returns_full_replication_sample(self):
        rng = np.random.default_rng(1)
        h, offset, linear = make_ground_truth(3, 1, 1.0, rng)
        runner = build_runner(h, offset, linear, 0.0, rng)
        z = rng.normal(size=3)
        samples = runner(z, 5)
        self.assertEqual(np.shape(samples), (5,))
        self.assertTrue(np.allclose(samples, samples[0]))


class TestHandVerification(unittest.TestCase):
    def test_noiseless_hand_computed_example_end_to_end(self):
        result = hand_verification()
        self.assertLess(result["absolute_error"], 1e-10)
        self.assertAlmostEqual(result["bilinear_e1e1"], 3.0, places=10)
        self.assertAlmostEqual(result["bilinear_e1e2"], 0.0, places=10)
        self.assertAlmostEqual(result["offset_recovered"], 1.0, places=10)
        self.assertTrue(
            np.allclose(result["linear_recovered"], [2.0, -1.0, 0.5], atol=1e-10)
        )


class TestFactorOnlyLearner(unittest.TestCase):
    def test_factor_model_never_materializes_dense_kernel(self):
        rng = np.random.default_rng(3)
        h, offset, linear = make_ground_truth(12, 2, 5.0, rng)
        meter = OracleMeter(build_runner(h, offset, linear, 0.0, rng))
        image = probe_image(meter, 12, 3, 4, rng)
        model = fit_factor_model(meter, image, 2, 4, offset, linear)
        self.assertEqual(model.basis.shape, (12, 2))
        self.assertEqual(model.core.shape, (2, 2))
        largest = max(arr.size for arr in (model.basis, model.core))
        self.assertLess(largest, 12 * 12)

    def test_factor_model_predicts_noiseless_truth(self):
        rng = np.random.default_rng(4)
        h, offset, linear = make_ground_truth(8, 2, 2.0, rng)
        meter = OracleMeter(build_runner(h, offset, linear, 0.0, rng))
        image = probe_image(meter, 8, 3, 16, rng)
        model = fit_factor_model(meter, image, 2, 16, offset, measure_linear(meter, 8, 16))
        heldout = [rng.normal(size=8) for _ in range(20)]
        predictions = model.predict(heldout)
        targets = np.array([offset + z @ linear + z @ h @ z for z in heldout])
        self.assertTrue(np.allclose(predictions, targets, atol=1e-8))


class TestCubicRecovery(unittest.TestCase):
    def test_rank_five_nonorthogonal_coefficient_recovery(self):
        rng = np.random.default_rng(211)
        dimension, rank = 12, 5
        factors = rng.normal(size=(dimension, rank))
        factors /= np.linalg.norm(factors, axis=0)
        weights = np.array([1.7, -0.8, 0.35, -0.2, 0.1])
        linear = rng.normal(size=dimension)

        def response(z, n):
            value = 2.0 + linear @ z + 0.3 * z @ z
            value += (z @ factors) ** 3 @ weights
            return np.full(n, value)

        basis, core = probe_transfer.recover_multilinear(
            OracleMeter(response), dimension, 3, rank, seed=17
        )
        expected = np.einsum("ia,ja,ka,a->ijk", factors, factors, factors, weights)
        recovered = np.einsum("ia,jb,kc,abc->ijk", basis, basis, basis, core)
        self.assertLess(np.max(np.abs(recovered - expected)), 1e-6)

    def test_cp_factor_extraction_recovers_true_components(self):
        rng = np.random.default_rng(31)
        dimension, rank = 14, 4
        factors, _ = np.linalg.qr(rng.normal(size=(dimension, rank)))
        weights = np.array([1.7, -0.8, 0.35, -0.2])
        linear = rng.normal(size=dimension)

        def response(z, n):
            value = 2.0 + linear @ z + ((z @ factors) ** 3) @ weights
            return np.full(n, value)

        meter = OracleMeter(response)
        basis, core = probe_transfer.recover_multilinear(
            meter, dimension, 3, rank, seed=3
        )
        factors_hat, weights_hat = probe_transfer.extract_cp_factors(
            meter, basis, dimension, seed=99, core=core
        )
        cosines = np.abs(factors_hat @ factors)
        self.assertLess(1.0 - float(cosines.max(axis=1).min()), 1e-8)
        permutation = cosines.argmax(axis=1)
        orientation = np.array(
            [float(factors_hat[a] @ factors[:, permutation[a]]) for a in range(rank)]
        )
        np.testing.assert_allclose(
            weights_hat * orientation, weights[permutation], atol=1e-8
        )
        tensor_true = sum(
            weights[a] * np.einsum("i,j,k->ijk", *[factors[:, a]] * 3)
            for a in range(rank)
        )
        tensor_hat = sum(
            weights_hat[a] * np.einsum("i,j,k->ijk", *[factors_hat[a]] * 3)
            for a in range(rank)
        )
        self.assertLess(float(np.max(np.abs(tensor_true - tensor_hat))), 1e-8)

    def test_core_free_nonorthogonal_weights_and_sample_budget(self):
        for rank in (1, 3, 5):
            for n in (1, 4):
                with self.subTest(rank=rank, n=n):
                    rng = np.random.default_rng(77)
                    dimension = 16
                    factors = rng.normal(size=(dimension, rank))
                    factors *= np.linspace(0.5, 1.5, rank) / np.linalg.norm(
                        factors, axis=0
                    )
                    weights = np.array([1.2, -0.7, 0.4, -0.3, 0.2])[:rank]
                    linear = rng.normal(size=dimension)
                    replications = []

                    def response(z, n):
                        replications.append(n)
                        value = 2.0 + linear @ z + 0.3 * z @ z
                        value += ((z @ factors) ** 3) @ weights
                        return np.full(n, value)

                    basis, _ = np.linalg.qr(factors)
                    meter = OracleMeter(response)
                    factors_hat, weights_hat = probe_transfer.extract_cp_factors(
                        meter, basis, dimension, seed=2, n=n, core=None
                    )
                    expected = np.einsum(
                        "ia,ja,ka,a->ijk", factors, factors, factors, weights
                    )
                    observed = np.einsum(
                        "ai,aj,ak,a->ijk",
                        factors_hat, factors_hat, factors_hat, weights_hat,
                    )
                    self.assertLess(float(np.max(np.abs(observed - expected))), 1e-12)
                    self.assertEqual(meter.count, 8 * n * (2 * rank**2 + rank))
                    self.assertEqual(set(replications), {n})
                    np.testing.assert_allclose(
                        np.linalg.norm(factors_hat, axis=1), 1.0, atol=1e-12
                    )
                    self.assertTrue(np.all(weights_hat >= 0.0))

    def test_quartic_core_free_signed_weights_and_query_counts(self):
        dimension, rank, order, n = 8, 3, 4, 2
        rng = np.random.default_rng(77)
        factors = rng.normal(size=(dimension, rank))
        factors *= np.array([0.7, 1.1, 1.4]) / np.linalg.norm(factors, axis=0)
        weights = np.array([1.2, -0.7, 0.4])
        linear = rng.normal(size=dimension)

        def response(z, n):
            value = 2.0 + linear @ z + 0.3 * z @ z + 0.1 * z[0] ** 3
            return np.full(n, value + ((z @ factors) ** order) @ weights)

        meter = OracleMeter(response)
        basis, core = probe_transfer.recover_multilinear(
            meter, dimension, order, rank, seed=3, n=n, measure_core=False
        )
        self.assertIsNone(core)
        self.assertEqual(meter.count, n * 2**order * dimension * rank)
        factors_hat, weights_hat = probe_transfer.extract_cp_factors(
            meter, basis, dimension, seed=2, n=n, order=order
        )
        expected = np.einsum("ia,ja,ka,la,a->ijkl", *[factors] * order, weights)
        observed = np.einsum(
            "ai,aj,ak,al,a->ijkl", *[factors_hat] * order, weights_hat
        )
        self.assertLess(float(np.max(np.abs(observed - expected))), 1e-10)
        self.assertEqual(np.count_nonzero(weights_hat < 0), 1)
        np.testing.assert_allclose(
            np.sort(weights_hat),
            np.sort(weights * np.linalg.norm(factors, axis=0)**order),
            atol=1e-10, rtol=0,
        )
        self.assertEqual(
            meter.count, n * 2**order * (dimension * rank + 2 * rank**2 + rank)
        )

    def test_higher_order_extraction_with_and_without_core(self):
        for order in (4, 5, 6):
            for use_core in (False, True):
                with self.subTest(order=order, use_core=use_core):
                    dimension, rank = 5, 2
                    rng = np.random.default_rng(37)
                    factors = rng.normal(size=(dimension, rank))
                    factors *= np.array([0.8, 1.2]) / np.linalg.norm(factors, axis=0)
                    weights = np.array([1.2, -0.7])
                    basis, _ = np.linalg.qr(factors)

                    def response(z, n):
                        return np.full(n, 1.0 + z[0] ** (order - 1)
                                       + ((z @ factors) ** order) @ weights)

                    def tensor(rows, coefficients):
                        result = np.zeros((rows.shape[1],) * order)
                        for row, coefficient in zip(rows, coefficients):
                            term = row
                            for _ in range(order - 1):
                                term = np.multiply.outer(term, row)
                            result += coefficient * term
                        return result

                    core = tensor(factors.T @ basis, weights) if use_core else None
                    meter = OracleMeter(response)
                    recovered, coefficients = probe_transfer.extract_cp_factors(
                        meter, basis, dimension, seed=2, order=order, core=core
                    )
                    np.testing.assert_allclose(
                        tensor(recovered, coefficients), tensor(factors.T, weights),
                        atol=1e-10, rtol=0,
                    )
                    self.assertEqual(
                        meter.count, 2**order * (2 * rank**2 + (0 if use_core else rank))
                    )
                    self.assertEqual(
                        np.count_nonzero(coefficients < 0), 0 if order % 2 else 1
                    )

    def test_order_four_full_ambient_reconstruction(self):
        rng = np.random.default_rng(7)
        dimension, rank, order = 10, 3, 4
        factors = rng.normal(size=(dimension, rank))
        factors /= np.linalg.norm(factors, axis=0)
        weights = np.array([1.2, -0.7, 0.4])
        linear = rng.normal(size=dimension)

        def response(z, n):
            value = 2.0 + linear @ z + ((z @ factors) ** order) @ weights
            return np.full(n, value)

        meter = OracleMeter(response)
        u = [rng.normal(size=dimension) for _ in range(order)]
        per_mode = [factors.T @ u[k] for k in range(order)]
        expected_polar = float(
            sum(
                weights[a] * np.prod([per_mode[k][a] for k in range(order)])
                for a in range(rank)
            )
        )
        observed_polar = probe_transfer.probe_multilinear(meter, u)
        self.assertLess(abs(observed_polar - expected_polar), 1e-10)

        basis, core = probe_transfer.recover_multilinear(
            meter, dimension, order, rank, seed=3
        )
        g = factors.T @ basis
        expected_core = np.zeros((rank,) * order)
        for j in np.ndindex((rank,) * order):
            expected_core[j] = float(
                np.sum(weights * np.prod(g[:, list(j)], axis=1))
            )
        self.assertLess(float(np.max(np.abs(core - expected_core))), 1e-9)

        tensor_true = np.zeros((dimension,) * order)
        for a in range(rank):
            tensor_true += weights[a] * np.einsum(
                "i,j,k,l->ijkl", *[factors[:, a]] * order
            )
        reconstructed = np.einsum(
            "abcd,ia,jb,kc,ld->ijkl", core, basis, basis, basis, basis
        )
        self.assertLess(float(np.max(np.abs(reconstructed - tensor_true))), 1e-6)


class TestNoisyOraclePath(unittest.TestCase):
    def test_noise_is_actually_injected_into_response(self):
        rng = np.random.default_rng(21)
        m = 6
        factors = rng.normal(size=(m, 2))
        weights = np.array([1.0, -0.5])
        linear = rng.normal(size=m)
        noise_rng = np.random.default_rng(22)

        def response(z, n):
            val = 1.0 + linear @ z + ((z @ factors) ** 3) @ weights
            return val + 0.05 * noise_rng.normal(size=n)

        z = rng.normal(size=m)
        samples = response(z, 8192)
        self.assertGreater(float(np.std(samples)), 0.01)
        self.assertLess(abs(float(np.mean(samples)) - (1.0 + linear @ z + ((z @ factors) ** 3) @ weights)), 0.01)

    def test_noisy_recovery_degrades_gracefully_and_stays_bounded(self):
        rng = np.random.default_rng(23)
        dimension, rank, order = 8, 2, 3
        factors = rng.normal(size=(dimension, rank))
        factors /= np.linalg.norm(factors, axis=0)
        weights = np.array([1.2, -0.7])
        linear = rng.normal(size=dimension)
        noise_rng = np.random.default_rng(24)

        def response(z, n):
            val = 1.0 + linear @ z + ((z @ factors) ** order) @ weights
            return val + 0.05 * noise_rng.normal(size=n)

        basis, core = probe_transfer.recover_multilinear(
            OracleMeter(response), dimension, order, 2, seed=5, n=8192
        )
        g = factors.T @ basis
        expected = np.zeros((2,) * order)
        for j in np.ndindex((2,) * order):
            expected[j] = float(np.sum(weights * np.prod(g[:, list(j)], axis=1)))
        scale = float(np.max(np.abs(expected)))
        rel_err = float(np.max(np.abs(core - expected))) / scale
        self.assertLess(rel_err, 0.05)


class TestCrossDomainControls(unittest.TestCase):
    def test_full_rank_tensor_is_not_fooled_by_forced_low_rank(self):
        rng = np.random.default_rng(9)
        m, rank = 16, 3
        A = rng.normal(size=(m, m, m))
        A = (
            A
            + A.transpose(1, 0, 2)
            + A.transpose(2, 1, 0)
            + A.transpose(1, 2, 0)
            + A.transpose(2, 0, 1)
            + A.transpose(0, 2, 1)
        ) / 6.0

        def response(z, n):
            return np.full(n, float(np.einsum("i,j,k,ijk->", z, z, z, A)))

        meter = OracleMeter(response)
        basis, core = probe_transfer.recover_multilinear(
            meter, m, 3, rank, seed=1
        )
        f_hat, w_hat = probe_transfer.extract_cp_factors(
            meter, basis, m, seed=2, core=core
        )
        T_hat = sum(
            w_hat[a] * np.einsum("i,j,k->ijk", *[f_hat[a]] * 3)
            for a in range(rank)
        )
        rel_err = float(np.max(np.abs(T_hat - A))) / float(np.max(np.abs(A)))
        self.assertGreater(rel_err, 0.5)
        v = rng.normal(size=(3, m))
        t_true = probe_transfer.probe_multilinear(meter, [v[0], v[1], v[2]])
        t_model = sum(
            w_hat[a]
            * float(f_hat[a] @ v[0])
            * float(f_hat[a] @ v[1])
            * float(f_hat[a] @ v[2])
            for a in range(rank)
        )
        residual = abs(t_true - t_model) / max(abs(t_true), 1e-30)
        self.assertGreater(residual, 0.5)


class TestDegenerateRatioRetry(unittest.TestCase):
    def test_degenerate_ratios_detected_and_resolved_by_redraw(self):
        rng = np.random.default_rng(51)
        dimension, rank = 12, 3
        factors, _ = np.linalg.qr(rng.normal(size=(dimension, rank)))
        weights = np.array([1.0, -0.6, 0.3])
        linear = rng.normal(size=dimension)

        def response(z, n):
            value = 2.0 + linear @ z + ((z @ factors) ** 3) @ weights
            return np.full(n, value)

        class FirstPairDegenerateRng:
            def __init__(self):
                self.calls = 0
                self.fallback = np.random.default_rng(52)

            def normal(self, size=None):
                self.calls += 1
                if self.calls <= 2:
                    return np.ones(size)
                return self.fallback.normal(size=size)

        meter = OracleMeter(response)
        directions = FirstPairDegenerateRng()
        factors_hat, weights_hat = probe_transfer.extract_cp_factors(
            meter, factors, dimension, rng=directions, core=None, max_retries=2
        )
        self.assertEqual(directions.calls, 4)
        self.assertEqual(meter.count, 8 * (4 * rank**2 + rank))
        expected = np.einsum("ia,ja,ka,a->ijk", factors, factors, factors, weights)
        observed = np.einsum(
            "ai,aj,ak,a->ijk", factors_hat, factors_hat, factors_hat, weights_hat
        )
        self.assertLess(float(np.max(np.abs(observed - expected))), 1e-12)

    def test_persistent_degeneracy_raises_instead_of_silent_garbage(self):
        rng = np.random.default_rng(52)
        dimension, rank = 10, 3
        factors, _ = np.linalg.qr(rng.normal(size=(dimension, rank)))
        weights = np.array([1.0, -0.6, 0.3])
        linear = rng.normal(size=dimension)

        def response(z, n):
            value = 2.0 + linear @ z + ((z @ factors) ** 3) @ weights
            return np.full(n, value)

        meter = OracleMeter(response)
        basis, core = probe_transfer.recover_multilinear(
            meter, dimension, 3, rank, seed=1
        )
        # Pin both slices to the same degenerate direction: ratios all 1.
        class FixedRng:
            def __init__(self, dim):
                self.dim = dim

            def normal(self, size=None):
                return np.ones(self.dim)

        with self.assertRaises(ValueError):
            probe_transfer.extract_cp_factors(
                meter, basis, dimension, core=core, rng=FixedRng(dimension),
                max_retries=3,
            )


class TestSampleAccounting(unittest.TestCase):
    def test_reported_counts_match_actual_oracle_draws(self):
        rng = np.random.default_rng(9)
        h, offset, linear = make_ground_truth(12, 2, 10.0, rng)
        response = build_runner(h, offset, linear, 0.05, rng)
        draws = {"n": 0}

        def counting(z, n):
            draws["n"] += n
            return response(z, n)

        original = probe_transfer.build_runner
        probe_transfer.build_runner = lambda *a, **k: counting
        try:
            case = run_case(
                m=12, true_rank=2, condition=10.0, sigma=0.05, s=10, n=32,
                calibration_fraction=0.5, ridge=1e-3, seed=9,
                rank_grid=[0, 1, 2, 3], validation_count=24,
                calibration_count=24, heldout_count=24, abstain_count=12,
            )
        finally:
            probe_transfer.build_runner = original
        reported = (
            case["oracle_samples_active"]
            + case["oracle_samples_baseline"]
            + case["oracle_samples_eval"]
        )
        self.assertEqual(draws["n"], reported)
