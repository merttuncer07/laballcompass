import functools
import importlib.util
import pathlib
import sys
import unittest

import numpy as np

from sacapl import support_covariance_aware_policy

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SACPS = _load(
    "sacps_v2p049_parent",
    PACKAGE_ROOT / "02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R037_SUPPORT_COVARIANCE_SACPS/sacps.py",
)
CAPL = _load(
    "capl_v2p049_parent",
    PACKAGE_ROOT / "02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R041_CONSTRAINED_POLICY_CAPL/capl.py",
)


def _dataset(seed=3, spurious_correlation=0.85):
    rng = np.random.default_rng(seed)
    assets = 4
    sigma = np.array([0.035, 0.035, 0.015, 0.015])
    # This risk-estimation sample contains a finite-sample, off-support negative
    # covariance between assets 0 and 1. The declared structural support is
    # diagonal, so SACPS removes this nuisance edge. Policy train/validation
    # returns below are independently drawn from the declared diagonal geometry.
    z = rng.normal(size=(20, assets))
    z[:, 1] = -spurious_correlation * z[:, 0] + np.sqrt(1.0 - spurious_correlation**2) * z[:, 1]
    risk_returns = z * sigma

    def policy_sample(n):
        x = rng.normal(size=(n, 1))
        noise = rng.normal(size=(n, assets)) * sigma
        mean = np.column_stack(
            (
                0.006 + 0.004 * np.tanh(x[:, 0]),
                0.006 - 0.004 * np.tanh(x[:, 0]),
                np.full(n, 0.0032),
                np.full(n, 0.0032),
            )
        )
        return x, mean + noise

    train_x, train_r = policy_sample(120)
    val_x, val_r = policy_sample(600)
    return risk_returns, train_x, train_r, val_x, val_r


@functools.lru_cache(maxsize=None)
def case(dense_support=False):
    risk, train_x, train_r, val_x, val_r = _dataset()
    support = np.ones((4, 4), dtype=bool) if dense_support else np.eye(4, dtype=bool)
    return support_covariance_aware_policy(
        CAPL,
        SACPS.estimate_support_aware_covariance,
        train_x,
        train_r,
        val_x,
        val_r,
        risk,
        support,
        shrinkage_grid=[0.0],
        maximum_asset_weight=0.8,
        maximum_turnover=0.8,
        risk_aversion=20.0,
        transaction_cost=0.0002,
        population_size=30,
        generations=10,
        elite_fraction=0.15,
        seed=3,
    )


class SACAPLTests(unittest.TestCase):
    def test_support_mechanism_changes_policy(self):
        self.assertFalse(case()["policies_identical"])
        self.assertEqual(case()["status"], "SUPPORT_COVARIANCE_CHANGED_CAPL_RISK_OBJECTIVE")

    def test_support_removes_off_support_covariance(self):
        self.assertAlmostEqual(case()["supported_off_support_max_abs_covariance"], 0.0, places=14)
        self.assertGreater(case()["raw_off_support_max_abs_covariance"], 1e-4)

    def test_realized_validation_variance_improves(self):
        self.assertLess(case()["validation_variance_change_fraction_vs_raw_covariance"], -0.50)

    def test_realized_validation_ce_improves(self):
        self.assertGreater(case()["validation_certainty_equivalent_gain_vs_raw_covariance"], 0.001)

    def test_candidate_constraints_remain_certified(self):
        audit = case()["candidate_validation_audit"]
        self.assertEqual(audit["sum_violations"], 0)
        self.assertEqual(audit["lower_bound_violations"], 0)
        self.assertEqual(audit["upper_bound_violations"], 0)
        self.assertEqual(audit["turnover_violations"], 0)

    def test_dense_support_mechanism_removal_collapses_exactly(self):
        result = case(True)
        self.assertTrue(result["policies_identical"])
        self.assertEqual(result["status"], "SUPPORT_COVARIANCE_COLLAPSED_TO_RAW_CONTROL")
        self.assertAlmostEqual(result["validation_certainty_equivalent_gain_vs_raw_covariance"], 0.0, places=12)

    def test_deterministic(self):
        # Cached case is also rerun here with the same inputs to prove the source,
        # not only the cache, is deterministic.
        risk, train_x, train_r, val_x, val_r = _dataset()
        repeated = support_covariance_aware_policy(
            CAPL, SACPS.estimate_support_aware_covariance,
            train_x, train_r, val_x, val_r, risk, np.eye(4, dtype=bool),
            shrinkage_grid=[0.0], maximum_asset_weight=0.8, maximum_turnover=0.8,
            risk_aversion=20.0, transaction_cost=0.0002,
            population_size=30, generations=10, elite_fraction=0.15, seed=3,
        )
        self.assertEqual(case(), repeated)


    def test_support_contradiction_abstains(self):
        risk, train_x, train_r, val_x, val_r = _dataset()
        rng = np.random.default_rng(99)
        z = rng.normal(size=80)
        calibration = np.column_stack((z, 0.95 * z + 0.1 * rng.normal(size=80), rng.normal(size=80), rng.normal(size=80)))
        result = support_covariance_aware_policy(
            CAPL, SACPS.estimate_support_aware_covariance,
            train_x, train_r, val_x, val_r, risk, np.eye(4, dtype=bool),
            risk_calibration_returns=calibration,
            maximum_calibration_off_support_correlation=0.5,
            shrinkage_grid=[0.0], maximum_asset_weight=0.8, maximum_turnover=0.8,
            risk_aversion=20.0, transaction_cost=0.0002,
            population_size=30, generations=10, seed=3,
        )
        self.assertEqual(result["status"], "ABSTAIN_SUPPORT_CONTRADICTED_BY_CALIBRATION")
        self.assertGreater(result["maximum_calibration_off_support_correlation"], 0.5)

    def test_asset_dimension_mismatch_rejected(self):
        risk, train_x, train_r, val_x, val_r = _dataset()
        with self.assertRaises(ValueError):
            support_covariance_aware_policy(
                CAPL, SACPS.estimate_support_aware_covariance,
                train_x, train_r, val_x, val_r, risk[:, :3], np.eye(3, dtype=bool),
                shrinkage_grid=[0.0], maximum_asset_weight=0.8, maximum_turnover=0.8,
                risk_aversion=20.0, transaction_cost=0.0002,
                population_size=30, generations=10, seed=3,
            )

    def test_invalid_support_rejected_by_parent_contract(self):
        risk, train_x, train_r, val_x, val_r = _dataset()
        bad = np.eye(4, dtype=bool)
        bad[0, 1] = True
        with self.assertRaises(ValueError):
            support_covariance_aware_policy(
                CAPL, SACPS.estimate_support_aware_covariance,
                train_x, train_r, val_x, val_r, risk, bad,
                shrinkage_grid=[0.0], maximum_asset_weight=0.8, maximum_turnover=0.8,
                risk_aversion=20.0, transaction_cost=0.0002,
                population_size=30, generations=10, seed=3,
            )


if __name__ == "__main__":
    unittest.main()
