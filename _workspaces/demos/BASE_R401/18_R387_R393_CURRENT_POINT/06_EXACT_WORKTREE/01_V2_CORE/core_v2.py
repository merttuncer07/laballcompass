"""Executable decision semantics for LabCompass Core V2.

Core V2 is intentionally not a scientific-novelty gate and not a product graveyard.
It records where a capability works, where it loses, what should route around it,
and how much evidence exists on separate axes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
from typing import Iterable
import json


class EvidenceLevel(IntEnum):
    NONE = 0
    EXECUTABLE = 1
    MECHANISM_CONTRAST = 2
    HELD_OUT_TRANSFER = 3
    OPERATIONAL_PILOT = 4
    MULTI_DOMAIN_PRODUCTION = 5


class ObservationDisposition(str, Enum):
    STRENGTHENS_WORKING_REGION = "STRENGTHENS_WORKING_REGION"
    NARROWS_REGION_AND_REQUIRES_ROUTER = "NARROWS_REGION_AND_REQUIRES_ROUTER"
    IMPLEMENTATION_REPAIR_REQUIRED = "IMPLEMENTATION_REPAIR_REQUIRED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ProductRole(str, Enum):
    STANDALONE = "STANDALONE"
    COMPONENT = "COMPONENT"
    BOTH = "BOTH"
    HELPER = "HELPER"


@dataclass(frozen=True)
class CapabilityProfile:
    capability_id: str
    name: str
    family: str
    evidence_tier: str
    strength_tags: frozenset[str] = frozenset()
    weakness_tags: frozenset[str] = frozenset()
    input_types: frozenset[str] = frozenset()
    output_types: frozenset[str] = frozenset()
    standalone_value: float = 0.0
    component_value: float = 0.0


@dataclass(frozen=True)
class CompositionCandidate:
    supplier_id: str
    consumer_id: str
    score: float
    interface_matches: tuple[str, ...]
    addressed_weaknesses: tuple[str, ...]
    shared_domains: tuple[str, ...]


def rank_composition(
    supplier: CapabilityProfile,
    consumer: CapabilityProfile,
    *,
    evidence_weight: float = 0.0,
) -> CompositionCandidate | None:
    """Rank a directed composition without using novelty or consensus as a veto."""
    interfaces=tuple(sorted(supplier.output_types & consumer.input_types))
    addressed=tuple(sorted(supplier.strength_tags & consumer.weakness_tags))
    shared=tuple(sorted((supplier.strength_tags | supplier.weakness_tags) & (consumer.strength_tags | consumer.weakness_tags)))
    if not interfaces and not addressed:
        return None
    score=4.0*len(interfaces)+5.0*len(addressed)+min(3,len(shared))+supplier.component_value+consumer.standalone_value+evidence_weight
    return CompositionCandidate(supplier.capability_id,consumer.capability_id,score,interfaces,addressed,shared)


@dataclass(frozen=True)
class EvidenceVector:
    code_correctness: EvidenceLevel = EvidenceLevel.NONE
    mechanism: EvidenceLevel = EvidenceLevel.NONE
    external_transfer: EvidenceLevel = EvidenceLevel.NONE
    operational_value: EvidenceLevel = EvidenceLevel.NONE
    deployment: EvidenceLevel = EvidenceLevel.NONE

    @property
    def production_ready(self) -> bool:
        return (
            self.code_correctness >= EvidenceLevel.EXECUTABLE
            and self.mechanism >= EvidenceLevel.MECHANISM_CONTRAST
            and self.external_transfer >= EvidenceLevel.HELD_OUT_TRANSFER
            and self.operational_value >= EvidenceLevel.OPERATIONAL_PILOT
            and self.deployment >= EvidenceLevel.MULTI_DOMAIN_PRODUCTION
        )


@dataclass(frozen=True)
class BenchmarkObservation:
    shell: str
    dataset_or_generator: str
    comparator: str
    metric: str
    candidate_minus_comparator_utility: float | None
    statistically_resolved: bool
    implementation_invariants_pass: bool
    recoverable_test_context: bool
    notes: str = ""


@dataclass
class CapabilityRecord:
    capability_id: str
    name: str
    role: ProductRole
    evidence: EvidenceVector = field(default_factory=EvidenceVector)
    working_regions: list[str] = field(default_factory=list)
    failure_regions: list[str] = field(default_factory=list)
    required_fallbacks: list[str] = field(default_factory=list)
    observations: list[BenchmarkObservation] = field(default_factory=list)
    standalone_value_hypothesis: str = "OPEN"
    component_value_hypothesis: str = "OPEN"
    implementation_available: bool = False

    def apply(self, observation: BenchmarkObservation) -> ObservationDisposition:
        self.observations.append(observation)
        if not observation.implementation_invariants_pass:
            self.failure_regions.append(
                f"IMPLEMENTATION_DEFECT | {observation.shell} | {observation.notes}".strip()
            )
            return ObservationDisposition.IMPLEMENTATION_REPAIR_REQUIRED
        if (
            not observation.statistically_resolved
            or observation.candidate_minus_comparator_utility is None
        ):
            return ObservationDisposition.INCONCLUSIVE
        if observation.candidate_minus_comparator_utility > 0:
            self.working_regions.append(
                f"{observation.shell} | beats {observation.comparator} on {observation.metric}"
            )
            return ObservationDisposition.STRENGTHENS_WORKING_REGION

        self.failure_regions.append(
            f"{observation.shell} | loses/ties {observation.comparator} on {observation.metric}"
        )
        fallback = f"Route to {observation.comparator} outside qualified region: {observation.shell}"
        if fallback not in self.required_fallbacks:
            self.required_fallbacks.append(fallback)
        return ObservationDisposition.NARROWS_REGION_AND_REQUIRES_ROUTER


class CoreRegistry:
    def __init__(self, records: Iterable[CapabilityRecord] = ()):
        self._records = {record.capability_id: record for record in records}

    def register(self, record: CapabilityRecord) -> None:
        if record.capability_id in self._records:
            raise ValueError(f"duplicate capability_id: {record.capability_id}")
        self._records[record.capability_id] = record

    def get(self, capability_id: str) -> CapabilityRecord:
        return self._records[capability_id]

    def route(self, capability_id: str, *, qualified_region: bool) -> str:
        record = self.get(capability_id)
        if qualified_region:
            return record.name
        if record.required_fallbacks:
            return record.required_fallbacks[-1]
        return "ABSTAIN_OR_RUN_BASELINE_CALIBRATION"

    def __len__(self) -> int:
        return len(self._records)


def load_unified_registry(path: str | Path) -> list[dict]:
    """Load the evidence registry without pretending each row is production-ready."""
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def build_catalog_search_engine(corpus_path: str | Path | None = None, *, composition_queue_path: str | Path | None = None, safety_margin: float = 1e-12, score_offsets: dict[str,float] | None = None):
    """Construct the interaction-aware certified Lab catalog search engine."""
    from lab_search_engine import CertifiedIncrementalSearch, InteractionGraph, load_search_corpus

    root = Path(__file__).resolve().parent
    path = Path(corpus_path) if corpus_path is not None else root / "generated_search" / "LAB_SEARCH_CORPUS.jsonl"
    queue = Path(composition_queue_path) if composition_queue_path is not None else root / "generated_v2_foundry" / "CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json"
    typed_map = root / "generated_search" / "INTERACTION_MAP_R12.json"
    if composition_queue_path is None and typed_map.exists():
        graph = InteractionGraph.from_typed_map(typed_map)
    else:
        graph = InteractionGraph.from_composition_queue(queue) if queue.exists() else InteractionGraph()
    return CertifiedIncrementalSearch(load_search_corpus(path), interaction_graph=graph, safety_margin=safety_margin, score_offsets=score_offsets)


def build_search_router(corpus_path: str | Path | None = None, *, composition_queue_path: str | Path | None = None, relevance_snapshot=None):
    """Construct the Lab search router: capabilities, primitives, and directed supplier search."""
    from lab_search_engine import InteractionGraph, LabSearchRouter, load_search_corpus

    root = Path(__file__).resolve().parent
    path = Path(corpus_path) if corpus_path is not None else root / "generated_search" / "LAB_SEARCH_CORPUS.jsonl"
    queue = Path(composition_queue_path) if composition_queue_path is not None else root / "generated_v2_foundry" / "CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json"
    typed_map = root / "generated_search" / "INTERACTION_MAP_R12.json"
    if composition_queue_path is None and typed_map.exists():
        graph = InteractionGraph.from_typed_map(typed_map)
    else:
        graph = InteractionGraph.from_composition_queue(queue) if queue.exists() else InteractionGraph()
    if isinstance(relevance_snapshot, (str, Path)):
        from relevance_learning import RelevanceSnapshot
        relevance_snapshot = RelevanceSnapshot.load(relevance_snapshot)
    return LabSearchRouter(load_search_corpus(path), graph, relevance_snapshot=relevance_snapshot)



def compile_search_relevance_snapshot(ledger_path: str | Path, *, target_generation: int, problem_shell: str, shell_tags=(), corpus_path: str | Path | None = None):
    """Compile the frozen relevance prior for one future search generation.

    Same/future-generation outcomes and protected validation are quarantined by
    construction. This changes retrieval priors only; it does not change evidence
    tiers or product promotion state.
    """
    from relevance_learning import FeedbackLedger, compile_relevance_snapshot
    from lab_search_engine import load_search_corpus
    root = Path(__file__).resolve().parent
    path = Path(corpus_path) if corpus_path is not None else root / "generated_search" / "LAB_SEARCH_CORPUS.jsonl"
    return compile_relevance_snapshot(
        FeedbackLedger.load_jsonl(ledger_path),
        load_search_corpus(path),
        target_generation=target_generation,
        problem_shell=problem_shell,
        shell_tags=shell_tags,
    )

def build_foundry_search_packet(problem_contract: dict, **kwargs):
    """Run the Lab search-to-Foundry bridge for a problem contract.

    The returned packet is a retrieval/frontier artifact. It proposes capabilities,
    primitive donors, and interaction-map expansions but does not promote products.
    """
    from search_to_foundry import build_packet
    return build_packet(problem_contract, **kwargs)


def choose_lab_next_experiment(contract, calibration_snapshot=None):
    """Choose the next quantified experiment for a frozen Lab decision contract.

    If a frozen R5 calibration snapshot is supplied, it may fill only UNKNOWN
    routing fields for exact test-signature + problem-shell matches. Same/future
    generation telemetry and protected validation never enter that snapshot.
    """
    from experiment_selector import ExperimentContract, contract_from_dict, choose_next_experiment
    if not isinstance(contract, ExperimentContract):
        contract = contract_from_dict(contract)
    if calibration_snapshot is not None:
        from experiment_telemetry import ExperimentCalibrationSnapshot, hydrate_contract_from_calibration
        if isinstance(calibration_snapshot, (str, Path)):
            calibration_snapshot = ExperimentCalibrationSnapshot.load(calibration_snapshot)
        elif isinstance(calibration_snapshot, dict):
            calibration_snapshot = ExperimentCalibrationSnapshot.from_dict(calibration_snapshot)
        contract = hydrate_contract_from_calibration(contract, calibration_snapshot)
    return choose_next_experiment(contract)


def compile_experiment_calibration_snapshot(ledger_path: str | Path, *, target_generation: int, problem_shell: str, min_attempts: int = 5, min_axis_observations: int = 5, one_sided_z: float = 1.645):
    """Compile a conservative future-generation experiment-channel calibration."""
    from experiment_telemetry import ExperimentTelemetryLedger, compile_calibration_snapshot
    return compile_calibration_snapshot(
        ExperimentTelemetryLedger.load_jsonl(ledger_path),
        target_generation=target_generation, problem_shell=problem_shell,
        min_attempts=min_attempts, min_axis_observations=min_axis_observations, one_sided_z=one_sided_z,
    )


def record_lab_experiment_run(contract, plan, outcome, ledger_path: str | Path, *, event_id: str, compute_seconds: float | None, calibration_eligible: bool, measurement_valid: bool = True, run_status: str = "COMPLETE", release_generation: int | None = None, shell_tags=(), provenance=()):
    """Append one standardized experiment run to the R5 telemetry ledger."""
    from experiment_selector import EvidenceRole, ExperimentContract, ExperimentOutcome, contract_from_dict
    from experiment_telemetry import ExperimentTelemetryLedger, record_from_round
    if not isinstance(contract, ExperimentContract):
        contract = contract_from_dict(contract)
    if isinstance(outcome, dict):
        outcome = ExperimentOutcome(
            event_id=str(outcome['event_id']), decision_id=str(outcome['decision_id']), test_id=str(outcome['test_id']),
            search_generation=int(outcome['search_generation']), selected_round=int(outcome['selected_round']),
            release_round=int(outcome['release_round']),
            realized_uncertainty_by_axis={str(k):float(v) for k,v in dict(outcome.get('realized_uncertainty_by_axis',{})).items()},
            role=EvidenceRole(str(outcome.get('role','DEVELOPMENT'))),
            provenance=tuple(str(x) for x in outcome.get('provenance',())),
        )
    event = record_from_round(
        contract, plan, outcome, event_id=event_id, compute_seconds=compute_seconds,
        calibration_eligible=calibration_eligible, measurement_valid=measurement_valid, run_status=run_status,
        release_generation=release_generation, shell_tags=shell_tags, provenance=provenance,
    )
    ledger=ExperimentTelemetryLedger.load_jsonl(ledger_path)
    ledger.append_jsonl(ledger_path,event)
    return event


def audit_foundry_experiment_readiness(queue_path: str | Path | None = None):
    """Return an explicit readiness audit for experiment routing telemetry."""
    from audit_experiment_readiness import audit
    root = Path(__file__).resolve().parent
    path = Path(queue_path) if queue_path is not None else root / "generated_v2_foundry" / "CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json"
    return audit(json.loads(path.read_text(encoding="utf-8")))


def bootstrap_foundry_experiment_contract(supplier_id: str, consumer_id: str, *, search_generation: int = 0, queue_path: str | Path | None = None):
    """Build a non-fabricated R6 bootstrap draft for one Foundry composition edge.

    Scientific weaknesses remain unquantified.  If an exact completed V2
    composition suite already exists, the draft exposes a fixed non-adaptive
    executable-case pilot whose numeric routing fields are initially UNKNOWN.
    """
    from experiment_contract_bootstrap import bootstrap_queue_row
    root=Path(__file__).resolve().parent
    path=Path(queue_path) if queue_path is not None else root/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    for row in rows:
        if row.get('supplier_id') == supplier_id and row.get('consumer_id') == consumer_id:
            return bootstrap_queue_row(row,root=root,search_generation=search_generation)
    raise KeyError(f'composition edge not found: {supplier_id} -> {consumer_id}')


def audit_foundry_experiment_bootstrap(queue_path: str | Path | None = None):
    """Audit which current queue rows have a real existing composition test suite."""
    from experiment_contract_bootstrap import audit_queue_bootstrap_readiness
    root=Path(__file__).resolve().parent
    path=Path(queue_path) if queue_path is not None else root/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
    return audit_queue_bootstrap_readiness(json.loads(path.read_text(encoding='utf-8')),root=root)
