from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np

# Reuse the exact packaged P003 consumer implementation.  K019's neutral
# effective-diversity mechanism is independently reimplemented here; the
# monolithic LCB prototype library is intentionally not imported.
_REPO = Path(__file__).resolve().parents[3]
_P003 = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products" / "P003_SANP"
if str(_P003) not in sys.path:
    sys.path.insert(0, str(_P003))

from sanp import construct_support_aware_neutral_portfolio  # noqa: E402
from parents.enpc import PortfolioSolution, construct_portfolio  # noqa: E402


@dataclass(frozen=True)
class SupportEvidence:
    nominal_count: int
    pairwise_rho: float


@dataclass(frozen=True)
class SupportEvidenceCheck:
    pair: tuple[int, int]
    mask_supports_relation: bool
    nominal_count: int
    pairwise_rho: float
    aggregate_variance_inflation: float
    effective_independent_count: float
    aggregate_se_inflation: float
    pairwise_threshold_says_small: bool
    collective_risk_flag: bool
    passes_gate: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EDSANPResult:
    route: str
    portfolio: PortfolioSolution
    structured_result: object | None
    support_checks: tuple[SupportEvidenceCheck, ...]
    failed_pairs: tuple[tuple[int, int], ...]
    missing_pairs: tuple[tuple[int, int], ...]
    status: str

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "portfolio": {
                "weights": list(map(float, self.portfolio.weights)),
                "expected_return": float(self.portfolio.expected_return),
                "volatility": float(self.portfolio.volatility),
                "objective_value": float(self.portfolio.objective_value),
                "factor_exposure": list(map(float, self.portfolio.factor_exposure)),
                "budget_residual": float(self.portfolio.budget_residual),
                "maximum_constraint_residual": float(self.portfolio.maximum_constraint_residual),
                "neutral_subspace_dimension": int(self.portfolio.neutral_subspace_dimension),
            },
            "structured_result": None if self.structured_result is None else self.structured_result.to_dict(),
            "support_checks": [x.to_dict() for x in self.support_checks],
            "failed_pairs": [list(x) for x in self.failed_pairs],
            "missing_pairs": [list(x) for x in self.missing_pairs],
            "status": self.status,
        }


def _effective_diversity(evidence: SupportEvidence, *, pairwise_threshold: float, max_variance_inflation: float, min_effective_count: float, pair: tuple[int, int], mask_supports_relation: bool) -> SupportEvidenceCheck:
    n = int(evidence.nominal_count)
    rho = float(evidence.pairwise_rho)
    if n < 1:
        raise ValueError("nominal_count must be >= 1")
    if n > 1 and not (-1.0 / (n - 1) <= rho < 1.0):
        raise ValueError("pairwise_rho outside equicorrelation PSD range")
    if n == 1 and abs(rho) > 1e-15:
        raise ValueError("pairwise_rho must be zero when nominal_count is one")
    vif = 1.0 + (n - 1) * rho
    if vif <= 0:
        raise ValueError("nonpositive aggregate variance factor")
    n_eff = n / vif
    collective = vif > float(max_variance_inflation)
    return SupportEvidenceCheck(
        pair=pair,
        mask_supports_relation=bool(mask_supports_relation),
        nominal_count=n,
        pairwise_rho=rho,
        aggregate_variance_inflation=float(vif),
        effective_independent_count=float(n_eff),
        aggregate_se_inflation=float(vif ** 0.5),
        pairwise_threshold_says_small=abs(rho) < float(pairwise_threshold),
        collective_risk_flag=collective,
        passes_gate=bool(n_eff >= float(min_effective_count) and not collective),
    )


def _validate_mask(mask, p: int) -> tuple[np.ndarray, tuple[tuple[int, int], ...]]:
    m = np.asarray(mask, dtype=bool)
    if m.shape != (p, p) or not np.array_equal(m, m.T) or not np.all(np.diag(m)):
        raise ValueError("support_mask must be symmetric, square, and include the diagonal")
    decisions = tuple((i, j) for i in range(p) for j in range(i + 1, p))
    return m, decisions


def _canonicalize_evidence(evidence: Mapping[tuple[int, int], SupportEvidence], p: int) -> dict[tuple[int, int], SupportEvidence]:
    out: dict[tuple[int, int], SupportEvidence] = {}
    for raw_pair, item in evidence.items():
        if len(raw_pair) != 2:
            raise ValueError("support evidence keys must be index pairs")
        i, j = map(int, raw_pair)
        if i == j or i < 0 or j < 0 or i >= p or j >= p:
            raise ValueError("support evidence pair is outside the off-diagonal asset index set")
        pair = (min(i, j), max(i, j))
        if pair in out:
            raise ValueError("duplicate support evidence after canonicalizing pair orientation")
        if not isinstance(item, SupportEvidence):
            item = SupportEvidence(**dict(item))  # type: ignore[arg-type]
        out[pair] = item
    return out


def _raw_portfolio(training_returns, expected_returns, *, factor_loadings=None, target_factor_exposure=None, budget=1.0, lower_bounds=-0.5, upper_bounds=0.8, risk_aversion=4.0) -> PortfolioSolution:
    train = np.asarray(training_returns, dtype=float)
    if train.ndim != 2 or train.shape[0] < 2 or train.shape[1] < 2 or not np.all(np.isfinite(train)):
        raise ValueError("training_returns must be a finite case-by-asset matrix")
    mu = np.asarray(expected_returns, dtype=float)
    if mu.shape != (train.shape[1],) or not np.all(np.isfinite(mu)):
        raise ValueError("expected_returns must contain one finite value per asset")
    raw_covariance = np.cov(train, rowvar=False, ddof=1)
    factors = None if factor_loadings is None else np.asarray(factor_loadings, dtype=float)
    target = None if target_factor_exposure is None else np.asarray(target_factor_exposure, dtype=float)
    return construct_portfolio(
        mu,
        raw_covariance,
        factor_loadings=factors,
        target_factor_exposure=target,
        budget=budget,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        risk_aversion=risk_aversion,
    )


def construct_effective_diversity_gated_portfolio(
    training_returns: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    support_evidence: Mapping[tuple[int, int], SupportEvidence],
    expected_returns: Sequence[float],
    *,
    covariance_validation_returns: Sequence[Sequence[float]] | None = None,
    factor_loadings=None,
    target_factor_exposure=None,
    budget: float = 1.0,
    lower_bounds=-0.5,
    upper_bounds=0.8,
    risk_aversion: float = 4.0,
    shrinkage_grid=tuple(np.linspace(0.0, 1.0, 21)),
    eigenvalue_floor: float = 1e-8,
    maximum_condition_number: float = 1e8,
    min_effective_count: float = 20.0,
    pairwise_threshold: float = 0.01,
    max_variance_inflation: float = 2.0,
) -> EDSANPResult:
    """Use P003 only when every off-diagonal mask decision has enough effective evidence.

    The adapter does not infer or edit the support graph.  A support mask asserts
    both presences and absences, so every off-diagonal mask decision must carry an
    evidence-multiplicity record.  K019-style equicorrelation accounting asks only
    whether that evidence is effectively diverse enough.  If any mask decision is
    missing evidence or fails the gate, the structured-support path fails closed to the same
    ENPC decision using raw sample covariance.

    Passing this gate is not evidence that a support relation is true; it only
    prevents nominally-many but strongly dependent evidence sources from being
    counted as independent support for P003's external support assumption.
    """
    train = np.asarray(training_returns, dtype=float)
    if train.ndim != 2 or train.shape[0] < 2 or train.shape[1] < 2 or not np.all(np.isfinite(train)):
        raise ValueError("training_returns must be a finite case-by-asset matrix")
    mask, mask_decisions = _validate_mask(support_mask, train.shape[1])
    evidence = _canonicalize_evidence(support_evidence, train.shape[1])

    checks = []
    missing = tuple(pair for pair in mask_decisions if pair not in evidence)
    for pair in mask_decisions:
        if pair not in evidence:
            continue
        checks.append(_effective_diversity(
            evidence[pair],
            pairwise_threshold=pairwise_threshold,
            max_variance_inflation=max_variance_inflation,
            min_effective_count=min_effective_count,
            pair=pair,
            mask_supports_relation=bool(mask[pair]),
        ))
    failed = tuple(check.pair for check in checks if not check.passes_gate)

    common = dict(
        factor_loadings=factor_loadings,
        target_factor_exposure=target_factor_exposure,
        budget=budget,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        risk_aversion=risk_aversion,
    )
    if missing or failed:
        portfolio = _raw_portfolio(train, expected_returns, **common)
        return EDSANPResult(
            route="RAW_COVARIANCE_ENPC_FALLBACK",
            portfolio=portfolio,
            structured_result=None,
            support_checks=tuple(checks),
            failed_pairs=failed,
            missing_pairs=missing,
            status="SUPPORT_EVIDENCE_NOT_EFFECTIVELY_DIVERSE_STRUCTURED_PATH_REFUSED",
        )

    structured = construct_support_aware_neutral_portfolio(
        train,
        mask,
        expected_returns,
        covariance_validation_returns=covariance_validation_returns,
        shrinkage_grid=shrinkage_grid,
        eigenvalue_floor=eigenvalue_floor,
        maximum_condition_number=maximum_condition_number,
        **common,
    )
    return EDSANPResult(
        route="SUPPORT_AWARE_SANP",
        portfolio=structured.portfolio,
        structured_result=structured,
        support_checks=tuple(checks),
        failed_pairs=tuple(),
        missing_pairs=tuple(),
        status="EFFECTIVE_DIVERSITY_GATE_PASSED_SUPPORT_AWARE_PATH_ALLOWED",
    )


def compare_gated_with_raw_on_fresh_returns(result: EDSANPResult, training_returns, expected_returns, fresh_returns, *, factor_loadings=None, target_factor_exposure=None, budget=1.0, lower_bounds=-0.5, upper_bounds=0.8, risk_aversion=4.0) -> dict:
    train = np.asarray(training_returns, dtype=float)
    fresh = np.asarray(fresh_returns, dtype=float)
    if fresh.ndim != 2 or train.ndim != 2 or fresh.shape[1] != train.shape[1]:
        raise ValueError("fresh return asset dimension differs from training")
    raw = _raw_portfolio(
        train, expected_returns,
        factor_loadings=factor_loadings,target_factor_exposure=target_factor_exposure,
        budget=budget,lower_bounds=lower_bounds,upper_bounds=upper_bounds,risk_aversion=risk_aversion,
    )
    cov = np.cov(fresh, rowvar=False, ddof=1)
    gated_var = float(result.portfolio.weights @ cov @ result.portfolio.weights)
    raw_var = float(raw.weights @ cov @ raw.weights)
    return {
        "route": result.route,
        "gated_variance": gated_var,
        "raw_variance": raw_var,
        "variance_change_fraction_vs_raw": float(gated_var / raw_var - 1.0) if raw_var > 0 else float("nan"),
        "cases": int(fresh.shape[0]),
        "status": "FRESH_OUT_OF_SAMPLE_GATED_VS_RAW_COMPARISON",
    }
