from __future__ import annotations

import csv
import json
import re
from pathlib import Path


WORKSPACE = Path(r"C:\Users\mertt\OneDrive\Belgeler\ChatGPT\newlabexplore")
GENERATED = WORKSPACE / "lcb_core_revision" / "generated"


RETRO50_RELATIONS = {
    "ClosureFinderV0": ("R042 PSCT; R024 BRED", "COMPLEMENT", "HIGH", "observable/state closure before reduction or prediction"),
    "CycleFlowAnalyzerV0": ("R002 HFAD", "LIGHTWEIGHT_FALLBACK", "HIGH", "HFAD adds local-face versus global-harmonic resolution"),
    "DiscrepancyRandomizerV0": ("R050 CBAC", "COMPLEMENT", "HIGH", "balanced experimental assignment and design-law inference"),
    "DecisionFluctuationGuardV0": ("R007 BICC; R028 TDSX; R044 DLEW", "SUITE_COMPLEMENT", "MEDIUM", "decision fragility and model-risk stack"),
    "MemoryKernelClosureV0": ("R024 BRED; R042 PSCT", "COMPLEMENT", "HIGH", "memory/state discovery before reduction"),
    "EffectiveDiversityGuardV0": ("R023 CORMA; R037 SACPS; R038 DHCC", "SUITE_COMPLEMENT", "HIGH", "effective rather than nominal independent information"),
    "ReliabilityTemperedEvidenceV0": ("R026 EBC", "COMPLEMENT", "HIGH", "reliability-weighted evidence borrowing"),
    "HiddenMassLinkageV0": ("R049 MLHPE", "DIRECT_SURFACE_OVERLAP", "HIGH", "hidden-population estimation with linkage uncertainty"),
    "CausalEdgeValidatorFeaturesV0": ("R008 LGID; R022 CDA", "COMPONENT", "MEDIUM", "causal-assumption and intervention-value validation"),
    "LiquidityLoadSharingStressV0": ("R004 OFLS", "COMPLEMENT", "HIGH", "liquidity state plus burden redistribution"),
    "LiquidityStateEngineV0": ("R004 OFLS", "DIRECT_COMPONENT", "HIGH", "usable-liquidity state for flow simulation"),
    "CompetingExitExposureV0": ("R047 MCRIS", "DIRECT_COMPONENT", "HIGH", "state-dependent competing exits"),
    "BandSpecificRelationGateV0": ("R005 SLERM; R034 RSPI", "COMPLEMENT", "HIGH", "band-specific synchronization evidence gate"),
    "TargetPopulationAnchorCalibratorV0": ("R026 EBC", "COMPLEMENT", "MEDIUM", "trusted target anchor before evidence borrowing"),
    "TreatmentConfounderFeedbackGuardV0": ("R008 LGID; R022 CDA", "COMPONENT", "MEDIUM", "time-varying treatment-confounder feedback"),
    "BurstAwareSamplerV0": ("R045 ATRC; R030 ISPO", "COMPLEMENT", "MEDIUM", "adaptive sampling/memory allocation"),
    "InterfaceWidthOptimizerV0": ("R003 RIC; R018 MCSC", "SUITE_COMPLEMENT", "MEDIUM", "structured exact optimization and certificates"),
    "SafeProblemReducerV0": ("R003 RIC; R018 MCSC", "SUITE_COMPLEMENT", "HIGH", "safe reduction before exact optimization"),
    "SolverCertificateAuditV0": ("R003 RIC; R018 MCSC", "SUITE_COMPLEMENT", "HIGH", "independent solver/certificate verification"),
    "AdmissibleShiftRobustOptimizerV0": ("R028 TDSX; R029 SCE; R044 DLEW", "SUITE_COMPLEMENT", "HIGH", "declared-shift robustness plus tipping exploration"),
    "GuaranteeTransportGateV0": ("R028 TDSX; R029 SCE; R044 DLEW", "SUITE_COMPLEMENT", "HIGH", "deployment-shift validity gate"),
    "EffectiveRedundancyAuditV0": ("R023 CORMA; R037 SACPS; R038 DHCC", "SUITE_COMPLEMENT", "HIGH", "coherent-path/covariance redundancy audit"),
    "DecisionWeightedCalibrationV0": ("R026 EBC; R044 DLEW", "COMPLEMENT", "MEDIUM", "calibration budget by decision consequence"),
    "DecisionSufficientCompressorV0": ("R039 DSBC", "DIRECT_SURFACE_OVERLAP", "HIGH", "decision-regret-aware compression"),
    "SelectionAwareReferenceLawV0": ("R014 ACSA", "DIRECT_COMPONENT", "HIGH", "post-selection inference layer"),
    "ObservabilityCoveragePlannerV0": ("R023 CORMA; R024 BRED; R042 PSCT", "SUITE_COMPLEMENT", "HIGH", "sensor coverage, state discovery and reduction"),
    "ReachableSubspaceAuditV0": ("R023 CORMA; R024 BRED; R042 PSCT", "SUITE_COMPLEMENT", "MEDIUM", "controllable/observable subspace audit"),
    "ObservationPolicyConfoundingGuardV0": ("R008 LGID; R022 CDA", "COMPONENT", "MEDIUM", "measurement-policy confounding"),
    "EffectiveComplexityMeterV0": ("R024 BRED; R046 MDDC", "COMPLEMENT", "MEDIUM", "effective model complexity versus nominal size"),
    "MultiFidelityBudgetControllerV0": ("R022 CDA", "COMPLEMENT", "MEDIUM", "value-of-information and measurement budget"),
}


R50_RELATIONS = {
    "RX-149": ("SharedCapacityAllocatorV0", "COMPONENT_EXTENSION", "overlap-aware marginal value"),
    "RX-067": ("InterfaceWidthOptimizerV0; SafeProblemReducerV0", "KERNEL_EXTENSION", "future-equivalent state compression"),
    "RX-039": ("none", "NEW_SURFACE", "conditional/fiber sampling"),
    "RX-137": ("R043 SRCD", "RETRO50_COMPLEMENT", "renegotiation-aware commitment and incentive preflight"),
    "RX-138": ("R018 MCSC; R043 SRCD", "RETRO50_COMPLEMENT", "implementability projection and contract/decision feasibility"),
}


def role_for(name: str) -> str:
    if name == "TruncatedPoolRankV0":
        return "HELPER_IMPLEMENTATION"
    if re.search(r"(Guard|Gate|Audit|Diagnostic|Monitor|Scanner|Alarm|Verifier|Discriminator)", name):
        return "ASSURANCE_OR_DIAGNOSTIC_KERNEL"
    if re.search(r"(Planner|Optimizer|Allocator|Router|Controller|Reserver|Commit|Execution)", name):
        return "ACTION_OR_OPTIMIZATION_KERNEL"
    if re.search(r"(Sensor|Sensing|Sampler|Inference|Calibrator|Tuner|Decoder)", name):
        return "INFERENCE_OR_MEASUREMENT_KERNEL"
    if re.search(r"(Engine|State|Compressor|Reducer|Finder|Analyzer|Meter)", name):
        return "STATE_OR_TRANSFORMATION_KERNEL"
    return "CAPABILITY_COMPONENT"


def evidence_for(matches: list[dict]) -> str:
    statuses = " ".join((m.get("status") or "") for m in matches)
    if "FAILS" in statuses or "PARTIAL_FAIL" in statuses:
        return "BENCHMARKED_WITH_NARROW_OR_LOSING_SHELL"
    if "BENCHMARKED" in statuses:
        return "MECHANISM_BENCHMARKED"
    if "LIVE" in statuses:
        return "PROTOTYPE_ONLY_OR_PENDING"
    return "EXECUTABLE_PROTOTYPE_PROVENANCE_LINK_INCOMPLETE"


def adoption_for(role: str, evidence: str) -> str:
    if role == "HELPER_IMPLEMENTATION":
        return "ADOPT_AS_INTERNAL_HELPER"
    if evidence == "BENCHMARKED_WITH_NARROW_OR_LOSING_SHELL":
        return "ADOPT_CAPABILITY_WITH_ROUTER_REQUIRED"
    if evidence == "MECHANISM_BENCHMARKED":
        return "ADOPT_CAPABILITY_NOT_PRODUCTION_CLAIM"
    return "ADOPT_TO_CANDIDATE_REGISTRY_NOT_DEPLOYMENT"


def main() -> None:
    raw = json.loads((GENERATED / "core_registry_raw.json").read_text(encoding="utf-8"))
    r50 = json.loads((GENERATED / "r50_reanalysis.json").read_text(encoding="utf-8"))
    unified = []
    for record in raw:
        name = record["class_name"]
        role = role_for(name)
        evidence = evidence_for(record["queue_matches"])
        relation = RETRO50_RELATIONS.get(
            name,
            ("none", "NO_HIGH_CONFIDENCE_MATCH", "N/A", "new capability surface relative to the current 50-product registry"),
        )
        unified.append(
            {
                **record,
                "core_v2_role": role,
                "evidence_state": evidence,
                "adoption_state": adoption_for(role, evidence),
                "production_ready": False,
                "working_region": "PRESERVE_FROM_DOSSIER_AND_MAP_BEFORE_DEPLOYMENT",
                "failure_region": "LOCALIZE_BY_DATA_SHELL_COMPARATOR_METRIC_NOT_GLOBAL_DEATH",
                "router_or_fallback": "REQUIRED_BEFORE_EXTERNAL_DEPLOYMENT",
                "standalone_product_test": "OPEN_UNLESS_A_DEPLOYMENT_SHELL_WAS_VALIDATED",
                "retro50_relation": {
                    "products": relation[0],
                    "type": relation[1],
                    "confidence": relation[2],
                    "note": relation[3],
                },
            }
        )

    for edge, evidence in r50.items():
        rel = R50_RELATIONS[edge]
        unified.append(
            {
                "kernel_id": f"LCB-R50-{edge[3:]}",
                "class_name": None,
                "base_name": evidence["mechanism"],
                "source_line": None,
                "source_marker": "r50 partial benchmark",
                "docstring": None,
                "public_methods": [],
                "all_methods": [],
                "queue_matches": [{"edge_id": edge}],
                "origin": "r50_saved_results_no_executable_source_in_rescue",
                "core_v2_role": (
                    "CAPABILITY_COMPONENT" if "COMPONENT" in evidence["core_v2_state"] else "KERNEL_CANDIDATE"
                ),
                "evidence_state": "SAVED_RESULT_REANALYZED_SOURCE_CODE_ABSENT",
                "adoption_state": evidence["core_v2_state"],
                "production_ready": False,
                "working_region": evidence,
                "failure_region": "OUTSIDE_TESTED_SYNTHETIC_SHELL_UNKNOWN",
                "router_or_fallback": "REQUIRED; USE_TESTED_BASELINE_OUTSIDE_QUALIFIED_REGION",
                "standalone_product_test": "OPEN",
                "retro50_relation": {
                    "products": rel[0],
                    "type": rel[1],
                    "confidence": "MEDIUM" if rel[0] != "none" else "N/A",
                    "note": rel[2],
                },
            }
        )

    jsonl = "\n".join(json.dumps(row, ensure_ascii=False) for row in unified) + "\n"
    (GENERATED / "CORE_V2_UNIFIED_REGISTRY.jsonl").write_text(jsonl, encoding="utf-8")

    fields = [
        "kernel_id",
        "class_name",
        "base_name",
        "origin",
        "core_v2_role",
        "evidence_state",
        "adoption_state",
        "production_ready",
        "retro50_products",
        "retro50_relation_type",
        "retro50_confidence",
        "retro50_note",
    ]
    with (GENERATED / "CORE_V2_PRODUCT_CROSSWALK.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in unified:
            rel = row["retro50_relation"]
            writer.writerow(
                {
                    **{key: row.get(key) for key in fields if not key.startswith("retro50_")},
                    "retro50_products": rel["products"],
                    "retro50_relation_type": rel["type"],
                    "retro50_confidence": rel["confidence"],
                    "retro50_note": rel["note"],
                }
            )

    counts = {
        "records": len(unified),
        "r49_executable_classes": len(raw),
        "r50_result_only_records": len(r50),
        "roles": {},
        "evidence_states": {},
        "adoption_states": {},
        "high_confidence_retro50_relations": sum(
            r["retro50_relation"]["confidence"] == "HIGH" for r in unified
        ),
    }
    for field, target in [
        ("core_v2_role", "roles"),
        ("evidence_state", "evidence_states"),
        ("adoption_state", "adoption_states"),
    ]:
        for row in unified:
            key = row[field]
            counts[target][key] = counts[target].get(key, 0) + 1
    (GENERATED / "core_v2_counts.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
