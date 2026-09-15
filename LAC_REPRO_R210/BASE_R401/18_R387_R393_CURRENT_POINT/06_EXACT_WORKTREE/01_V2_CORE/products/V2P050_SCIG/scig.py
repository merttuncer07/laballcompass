"""Support-Covariance Independence Guard (SCIG), R388 shadow candidate.

Composition: R037 SACPS -> IM445_IM085 CSID.
SACPS covariance can merge nominally distinct safeguard evidence families when
supported dependence indicates a common-mode channel. CSID then recomputes
coverage and portfolio choice using the dependence-adjusted family partition.
"""
from __future__ import annotations

from typing import Sequence
import numpy as np


def _selected_names(design: dict) -> tuple[str, ...]:
    return tuple(design["selected"]["safeguards"])


def support_covariance_independence_guard(
    csid_module,
    covariance_estimator,
    failure_modes,
    safeguards,
    evidence_returns: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    *,
    budget: float,
    correlation_threshold: float = 0.6,
    ambiguity_band: float = 0.05,
    shrinkage_grid: Sequence[float] = tuple(np.linspace(0.0, 1.0, 21)),
) -> dict:
    """Build a conditional common-mode stress partition from observed covariance.

    Declared same-family safeguards are always kept common-mode. Distinct
    declared families are merged only when SACPS retains their covariance edge
    and its positive correlation clears the declared threshold. Strong signed
    associations excluded by support, or hidden by regularization, cause abstention. Correlations
    too close to the threshold cause abstention rather than an arbitrary merge.
    """
    safeguards = tuple(safeguards)
    failures = tuple(failure_modes)
    if len(safeguards) < 2:
        raise ValueError("at least two safeguards are required")
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("budget must be nonnegative")
    if not np.isfinite(correlation_threshold) or not np.isfinite(ambiguity_band) or not 0 < correlation_threshold < 1 or ambiguity_band < 0 or correlation_threshold - ambiguity_band < 0 or correlation_threshold + ambiguity_band > 1:
        raise ValueError("correlation threshold and ambiguity band are invalid")
    evidence = np.asarray(evidence_returns, dtype=float)
    if evidence.ndim != 2 or evidence.shape[0] < 5 or evidence.shape[1] != len(safeguards) or not np.all(np.isfinite(evidence)):
        raise ValueError("evidence_returns must be a finite row-by-safeguard matrix with at least five rows")
    support = np.asarray(support_mask, dtype=bool)
    if support.shape != (len(safeguards), len(safeguards)) or not np.array_equal(support, support.T) or not np.all(np.diag(support)):
        raise ValueError("support_mask must be symmetric, square, and include every safeguard diagonal")

    # Validate the decision inputs even when diagnostics later abstain.
    control_designer = csid_module.ContractSafeguardDesigner(failures, safeguards)
    centered = evidence - evidence.mean(axis=0)
    marginal_scale = np.linalg.norm(centered, axis=0)
    if np.any(marginal_scale == 0) or not np.all(np.isfinite(marginal_scale)):
        raise ValueError("evidence columns must have finite, nonzero variation")
    standardized = centered / marginal_scale
    raw_correlation = np.clip(standardized.T @ standardized, -1.0, 1.0)
    upper = correlation_threshold + ambiguity_band
    lower = correlation_threshold - ambiguity_band
    diagnostics = {"sample_rows": int(evidence.shape[0]),
                   "assumptions": [
                       "Pearson correlation is a diagnostic, not proof of common provenance or independence.",
                       "Family merging defines a common-mode stress model, not an observed failure law.",
                       "CSID multiplies coverage across remaining families under a conditional independence assumption.",
                       "Thresholds and ambiguity bands are user settings, not calibrated confidence intervals."],
                   "independence_certified": False}
    conflicts = []
    negative = []
    for i in range(len(safeguards)):
        for j in range(i + 1, len(safeguards)):
            if safeguards[i].evidence_family == safeguards[j].evidence_family:
                continue
            rho = float(raw_correlation[i, j])
            edge = {"left": safeguards[i].name, "right": safeguards[j].name,
                    "raw_correlation": rho, "supported": bool(support[i, j])}
            if abs(rho) > upper and not support[i, j]:
                conflicts.append(edge)
            elif rho < -upper:
                negative.append(edge)
    if conflicts or negative:
        return {"status": "ABSTAIN_SUPPORT_CONTRADICTED" if conflicts else "ABSTAIN_NEGATIVE_DEPENDENCE",
                "support_conflicts": conflicts, "negative_dependence_edges": negative,
                "diagnostics": diagnostics,
                "fallback": "No portfolio is certified or selected. Reconcile the support model with the observations; signed association alone cannot determine shared failure coverage."}

    estimate = covariance_estimator(evidence, support, shrinkage_grid=shrinkage_grid)
    covariance = np.asarray(estimate.covariance, dtype=float)
    if covariance.shape != support.shape or not np.all(np.isfinite(covariance)) or not np.allclose(covariance, covariance.T):
        raise ValueError("covariance estimator returned an invalid covariance matrix")
    scale = np.sqrt(np.diag(covariance))
    if np.any(scale <= 0) or not np.all(np.isfinite(scale)):
        raise RuntimeError("support-aware covariance has nonpositive marginal scale")
    correlation = covariance / np.outer(scale, scale)
    hidden = []
    for i in range(len(safeguards)):
        for j in range(i + 1, len(safeguards)):
            if (safeguards[i].evidence_family != safeguards[j].evidence_family
                    and raw_correlation[i, j] > upper and correlation[i, j] < lower):
                hidden.append({"left": safeguards[i].name, "right": safeguards[j].name,
                               "raw_correlation": float(raw_correlation[i, j]),
                               "regularized_correlation": float(correlation[i, j])})
    if hidden:
        return {"status": "ABSTAIN_REGULARIZATION_MASKS_DEPENDENCE", "hidden_dependence_edges": hidden,
                "selected_shrinkage": float(estimate.selected_shrinkage), "diagnostics": diagnostics,
                "fallback": "Regularization removed a strong observed association. No independence-based portfolio is selected."}

    parent = list(range(len(safeguards)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra,rb)] = min(ra,rb)

    # Preserve every explicit CSID common-mode declaration.
    for i in range(len(safeguards)):
        for j in range(i+1, len(safeguards)):
            if safeguards[i].evidence_family == safeguards[j].evidence_family:
                union(i,j)

    cross_family_edges=[]
    ambiguous=[]
    lower = correlation_threshold - ambiguity_band
    upper = correlation_threshold + ambiguity_band
    for i in range(len(safeguards)):
        for j in range(i+1, len(safeguards)):
            if safeguards[i].evidence_family == safeguards[j].evidence_family or not support[i,j]:
                continue
            rho = float(abs(correlation[i,j]))
            row={"left":safeguards[i].name,"right":safeguards[j].name,"absolute_correlation":rho}
            cross_family_edges.append(row)
            if lower <= rho <= upper:
                ambiguous.append(row)
            elif rho > upper:
                union(i,j)
    if ambiguous:
        return {
            "status":"ABSTAIN_DEPENDENCE_THRESHOLD_AMBIGUOUS",
            "ambiguous_edges":ambiguous,
            "correlation_threshold":float(correlation_threshold),
            "ambiguity_band":float(ambiguity_band),
            "diagnostics": diagnostics,
            "fallback":"No portfolio is selected. Resolve the ambiguous family boundary; retaining the original partition would not certify independence.",
        }

    roots={find(i) for i in range(len(safeguards))}
    root_ids={root:f"SCIG_FAMILY_{n+1}" for n,root in enumerate(sorted(roots))}
    adjusted=[]
    family_map={}
    for i,safeguard in enumerate(safeguards):
        family=root_ids[find(i)]
        family_map[safeguard.name]=family
        adjusted.append(csid_module.Safeguard(safeguard.name, safeguard.cost, family, safeguard.coverage))

    candidate_designer=csid_module.ContractSafeguardDesigner(failures,adjusted)
    control=control_designer.design(budget,family_aware=True)
    candidate=candidate_designer.design(budget,family_aware=True)

    adjusted_by_name={s.name:s for s in adjusted}
    control_under_adjusted=candidate_designer.evaluate([adjusted_by_name[name] for name in _selected_names(control)],family_aware=True).as_dict()
    candidate_selected=candidate["selected"]
    merged_cross_family = any(
        safeguards[i].evidence_family != safeguards[j].evidence_family and find(i)==find(j)
        for i in range(len(safeguards)) for j in range(i+1,len(safeguards))
    )
    return {
        "diagnostics": diagnostics,
        "selected_shrinkage":float(estimate.selected_shrinkage),
        "cross_family_covariance_edges":cross_family_edges,
        "dependence_adjusted_family_map":family_map,
        "merged_cross_family":bool(merged_cross_family),
        "control_declared_partition":control,
        "control_revalued_under_dependence_partition":control_under_adjusted,
        "candidate_dependence_adjusted_partition":candidate,
        "objective_improvement_under_assumed_partition":float(control_under_adjusted["objective"]-candidate_selected["objective"]),
        "status":"SUPPORT_COVARIANCE_CHANGED_CSID_INDEPENDENCE_PARTITION" if merged_cross_family else "SUPPORT_COVARIANCE_COLLAPSED_TO_DECLARED_FAMILIES",
    }
