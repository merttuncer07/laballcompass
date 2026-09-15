"""Non-fabricated experiment-contract bootstrap for LabAllCompass R6.

R6 solves the circular cold-start problem left by R5:

    candidate/composition has explicit weaknesses + executable tests
    -> preserve those weaknesses as unquantified structural questions
    -> discover an existing fixed executable test suite
    -> create an UNKNOWN numeric test channel
    -> run a predeclared, non-adaptive pilot schedule over the suite cases
    -> record real runtime/pass telemetry and design-defined case coverage
    -> let R5 calibrate only a later generation

No scientific uncertainty, information gain, reliability, or cost is inferred from prose.
The only numeric uncertainty used by the bootstrap pilot is the fraction of the
predeclared executable contract cases that remain unprobed.  That quantity is a
finite-set coverage measure, not a claim about real-world scientific uncertainty.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import ast
import hashlib
import json
import re
import subprocess
import sys
import time

from experiment_selector import EvidenceRole, ExperimentContract, TestChannel, UncertaintyAxis
from experiment_telemetry import ExperimentRunRecord, ExperimentTelemetryLedger, compile_calibration_snapshot, hydrate_contract_from_calibration
from experiment_selector import choose_next_experiment

MODEL_VERSION = "LAB_EXPERIMENT_BOOTSTRAP_R6_V1"
RUNNER_VERSION = "FIXED_UNIT_CASE_SCHEDULE_V1"


@dataclass(frozen=True)
class ExecutableSuite:
    product_id: str
    supplier_id: str
    consumer_id: str
    product_dir: str
    test_file: str
    cases: tuple[str, ...]
    test_id: str
    test_signature: str
    problem_shell: str
    source_hash: str

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "supplier_id": self.supplier_id,
            "consumer_id": self.consumer_id,
            "product_dir": self.product_dir,
            "test_file": self.test_file,
            "cases": list(self.cases),
            "test_id": self.test_id,
            "test_signature": self.test_signature,
            "problem_shell": self.problem_shell,
            "source_hash": self.source_hash,
        }


@dataclass(frozen=True)
class ComponentTestSurface:
    capability_id: str
    product_id: str
    product_dir: str
    test_files: tuple[str, ...]
    case_count: int
    source_hash: str

    def to_dict(self) -> dict:
        return {
            "capability_id":self.capability_id,"product_id":self.product_id,"product_dir":self.product_dir,
            "test_files":list(self.test_files),"case_count":self.case_count,"source_hash":self.source_hash,
        }


@dataclass(frozen=True)
class BootstrapDraft:
    status: str
    supplier_id: str
    consumer_id: str
    decision_id: str
    structural_questions: tuple[Mapping[str, object], ...]
    suite: ExecutableSuite | None
    contract: ExperimentContract | None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        c = self.contract
        return {
            "model_version": MODEL_VERSION,
            "status": self.status,
            "supplier_id": self.supplier_id,
            "consumer_id": self.consumer_id,
            "decision_id": self.decision_id,
            "structural_questions": [dict(x) for x in self.structural_questions],
            "suite": None if self.suite is None else self.suite.to_dict(),
            "experiment_contract": None if c is None else _contract_to_dict(c),
            "notes": list(self.notes),
        }


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value[:96] or "question"


def _sha256_bytes(parts: Iterable[bytes]) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part)
        h.update(b"\0")
    return h.hexdigest()


def _product_tree_hash(product_dir: Path) -> str:
    chunks=[]
    for path in sorted(p for p in product_dir.rglob("*.py") if "__pycache__" not in p.parts):
        chunks.append(str(path.relative_to(product_dir)).encode())
        chunks.append(path.read_bytes())
    return _sha256_bytes(chunks)


def _discover_unittest_cases(test_file: Path) -> tuple[str, ...]:
    tree=ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
    cases=[]
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    cases.append(f"{node.name}.{child.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            cases.append(node.name)
    return tuple(cases)


def _composition_from_result(text: str, kernel_name_to_id: Mapping[str,str]) -> tuple[str,str] | None:
    # Legacy fallback for pre-R13 products that encoded identity only in prose.
    m=re.search(r"LCB\s+`([^`]+)`\s*\+\s*Foundry\s+`(P\d+)\b", text, flags=re.I)
    if not m: return None
    supplier=kernel_name_to_id.get(m.group(1))
    if not supplier: return None
    return supplier, "FOUNDRY:"+m.group(2).upper()


def _composition_from_product_dir(product_dir: Path, text: str, kernel_name_to_id: Mapping[str,str]) -> tuple[str,str] | None:
    meta=product_dir/"COMPOSITION.json"
    if meta.exists():
        row=json.loads(meta.read_text(encoding="utf-8"))
        supplier=str(row.get("supplier_id","")).strip()
        consumer=str(row.get("consumer_id","")).strip()
        if not supplier or not consumer:
            raise ValueError(f"invalid COMPOSITION.json in {product_dir}")
        return supplier,consumer
    return _composition_from_result(text,kernel_name_to_id)


def discover_foundry_component_test_surfaces(root: str | Path | None = None) -> dict[str, ComponentTestSurface]:
    core=Path(root).resolve() if root is not None else Path(__file__).resolve().parent
    products=core.parent/"02_FOUNDRY_ALL_PRODUCTS"/"products"
    out={}
    if not products.exists(): return out
    for product_dir in sorted(p for p in products.iterdir() if p.is_dir()):
        m=re.match(r"(P\d+)_",product_dir.name)
        if not m: continue
        test_files=sorted(product_dir.glob("test_*.py"))
        if not test_files: continue
        count=sum(len(_discover_unittest_cases(p)) for p in test_files)
        if count < 1: continue
        pid=m.group(1).upper(); cap="FOUNDRY:"+pid
        out[cap]=ComponentTestSurface(
            capability_id=cap,product_id=pid,product_dir=str(product_dir),
            test_files=tuple(str(p) for p in test_files),case_count=count,source_hash=_product_tree_hash(product_dir),
        )
    return out


def discover_existing_composition_suites(root: str | Path | None = None) -> dict[tuple[str,str], ExecutableSuite]:
    core=Path(root).resolve() if root is not None else Path(__file__).resolve().parent
    registry=json.loads((core/"generated"/"core_registry_raw.json").read_text(encoding="utf-8"))
    kernel_name_to_id={str(r.get("class_name")):str(r.get("kernel_id")) for r in registry if r.get("class_name") and r.get("kernel_id")}
    out={}
    for product_dir in sorted((core/"products").glob("V2P*")):
        result=product_dir/"PRODUCT_RESULT.md"
        if not result.exists(): continue
        pair=_composition_from_product_dir(product_dir,result.read_text(encoding="utf-8"),kernel_name_to_id)
        if pair is None: continue
        test_files=sorted(product_dir.glob("test_*.py"))
        if not test_files: continue
        # One suite per completed V2 product.  If multiple test modules appear later,
        # they receive separate suite IDs; current R6 products each have one.
        test_file=test_files[0]
        cases=_discover_unittest_cases(test_file)
        if not cases: continue
        source_hash=_product_tree_hash(product_dir)
        product_id=product_dir.name.split("_",1)[0]
        sig=_sha256_bytes([
            MODEL_VERSION.encode(), RUNNER_VERSION.encode(), source_hash.encode(),
            test_file.name.encode(), "\n".join(cases).encode(),
        ])
        test_id=f"BOOTSTRAP_UNIT_CASE::{product_id}"
        shell=f"BOOTSTRAP_EXECUTABLE_CONTRACT::{product_id}::{source_hash[:16]}"
        out[pair]=ExecutableSuite(
            product_id=product_id,supplier_id=pair[0],consumer_id=pair[1],
            product_dir=str(product_dir),test_file=str(test_file),cases=cases,
            test_id=test_id,test_signature=sig,problem_shell=shell,source_hash=source_hash,
        )
    return out


def _load_foundry_weaknesses(core: Path, consumer_id: str) -> list[str]:
    pid=consumer_id.split(":",1)[-1]
    inv=core.parent/"02_FOUNDRY_ALL_PRODUCTS"/"audit"/"PRODUCT_EVIDENCE_INVENTORY.jsonl"
    if not inv.exists(): return []
    for line in inv.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        row=json.loads(line)
        if row.get("product_id") == pid:
            return [str(x) for x in row.get("weaknesses",()) if str(x).strip()]
    return []


def _structural_questions(core: Path, row: Mapping[str,object]) -> tuple[Mapping[str,object], ...]:
    questions=[]; seen=set()
    def add(text: str, source: str):
        key=text.strip().lower()
        if not key or key in seen: return
        seen.add(key)
        questions.append({
            "question_id":_slug(text),"source_text":text.strip(),"source":source,
            "numeric_uncertainty":"UNKNOWN","decision_leverage":"UNKNOWN",
            "status":"PRESERVED_UNQUANTIFIED",
        })
    for x in row.get("addressed_weaknesses") or (): add(str(x),"composition_queue.addressed_weaknesses")
    for x in _load_foundry_weaknesses(core,str(row.get("consumer_id",""))): add(x,"foundry_product_evidence.weaknesses")
    rationale=row.get("curated_rationale")
    if rationale: add(str(rationale),"composition_queue.curated_rationale")
    return tuple(questions)


def _contract_to_dict(c: ExperimentContract) -> dict:
    return {
        "decision_id":c.decision_id,"search_generation":c.search_generation,"selection_round":c.selection_round,
        "problem_shell":c.problem_shell,"stop_unresolved_mass":c.stop_unresolved_mass,
        "compute_ceiling_seconds":c.compute_ceiling_seconds,"provenance":list(c.provenance),
        "axes":[{"axis_id":a.axis_id,"label":a.label,"uncertainty":a.uncertainty,"decision_leverage":a.decision_leverage,"importance":a.importance} for a in c.axes],
        "tests":[{
            "test_id":t.test_id,"title":t.title,"expected_resolution_by_axis":dict(t.expected_resolution_by_axis),
            "compute_seconds":t.compute_seconds,"reliability":t.reliability,"evidence_role":t.evidence_role.value,
            "selection_generation":t.selection_generation,"measurement_backreaction":t.measurement_backreaction,
            "backreaction_adjusted":t.backreaction_adjusted,"calibration_id":t.calibration_id,
            "test_signature":t.test_signature,"notes":t.notes,
        } for t in c.tests],
    }


def bootstrap_queue_row(row: Mapping[str,object], *, root: str | Path | None = None, search_generation: int = 0) -> BootstrapDraft:
    core=Path(root).resolve() if root is not None else Path(__file__).resolve().parent
    supplier=str(row.get("supplier_id","")); consumer=str(row.get("consumer_id",""))
    decision_id=f"COMPOSITION::{supplier}->{consumer}"
    questions=_structural_questions(core,row)
    suite=discover_existing_composition_suites(core).get((supplier,consumer))
    if suite is None:
        component_surfaces=discover_foundry_component_test_surfaces(core)
        consumer_surface=component_surfaces.get(consumer)
        supplier_surface=component_surfaces.get(supplier)
        if consumer_surface is not None:
            status="ADAPTER_REQUIRED_CONSUMER_INVARIANT_SUITE_AVAILABLE"
            notes=(
                f"Consumer {consumer} has {consumer_surface.case_count} executable invariant cases, but no composed adapter/harness exists for this edge.",
                "Use that suite as a post-adapter preservation surface; do not treat it as evidence for the unbuilt composition.",
                "No numeric experiment contract was synthesized.",
            )
        elif supplier_surface is not None:
            status="SUPPLIER_INVARIANT_SUITE_AVAILABLE_NO_COMPOSITION_HARNESS"
            notes=(
                f"Supplier {supplier} has {supplier_surface.case_count} executable invariant cases, but they do not test the proposed consumer interaction.",
                "No numeric experiment contract was synthesized.",
            )
        else:
            status="NO_EXECUTABLE_TEST_SURFACE_DISCOVERED"
            notes=("No numeric experiment contract was synthesized.",)
        return BootstrapDraft(
            status=status,supplier_id=supplier,consumer_id=consumer,
            decision_id=decision_id,structural_questions=questions,suite=None,contract=None,notes=notes,
        )
    axis=UncertaintyAxis(
        axis_id="declared_executable_contract_case_coverage",
        label="fraction of the predeclared executable contract cases not yet probed",
        uncertainty=1.0,decision_leverage=1.0,importance=1.0,
    )
    channel=TestChannel(
        test_id=suite.test_id,
        title=f"Run one fixed case from {suite.product_id} executable contract suite",
        expected_resolution_by_axis={axis.axis_id:None},compute_seconds=None,reliability=None,
        evidence_role=EvidenceRole.DEVELOPMENT,selection_generation=search_generation,
        measurement_backreaction=False,backreaction_adjusted=False,calibration_id=None,
        test_signature=suite.test_signature,
        notes=("R6 bootstrap channel. Numeric fields intentionally UNKNOWN until a fixed non-adaptive pilot schedule is executed. "
               "Calibration is exact-shell and exact-signature only; it measures suite-case behavior, not general-world validity."),
    )
    contract=ExperimentContract(
        decision_id=decision_id,search_generation=search_generation,selection_round=0,
        axes=(axis,),tests=(channel,),problem_shell=suite.problem_shell,
        provenance=(f"R6_BOOTSTRAP:{suite.product_id}",suite.test_file),
    )
    return BootstrapDraft(
        status="FIXED_PILOT_SCHEDULE_AVAILABLE",supplier_id=supplier,consumer_id=consumer,
        decision_id=decision_id,structural_questions=questions,suite=suite,contract=contract,
        notes=(
            "Structural scientific questions remain unquantified.",
            "Only finite executable-suite case coverage receives a numeric bootstrap axis.",
            "Pilot schedule is frozen before execution and is not adaptively selected.",
        ),
    )


def run_fixed_suite_pilot(draft: BootstrapDraft, *, release_generation: int = 1, timeout_seconds: float = 30.0, event_namespace: str = "R6") -> tuple[ExperimentRunRecord, ...]:
    if draft.suite is None or draft.contract is None:
        raise ValueError("draft has no executable suite")
    suite=draft.suite; contract=draft.contract
    test_file=Path(suite.test_file); cwd=test_file.parent; module=test_file.stem
    n=len(suite.cases)
    if n < 1: raise ValueError("suite has no cases")
    events=[]
    for idx,case in enumerate(suite.cases):
        target=f"{module}.{case}"
        start=time.perf_counter()
        try:
            cp=subprocess.run([sys.executable,"-m","unittest",target],cwd=cwd,text=True,capture_output=True,timeout=timeout_seconds)
            elapsed=max(time.perf_counter()-start,1e-9)
            status="COMPLETE" if cp.returncode==0 else "FAILED"
            valid=True
            detail=(cp.stdout+"\n"+cp.stderr).strip()[-2000:]
        except subprocess.TimeoutExpired as exc:
            elapsed=max(time.perf_counter()-start,1e-9)
            status="CENSORED"; valid=False; detail=f"TIMEOUT:{exc}"
        before=1.0
        after=max(0.0,1.0-1.0/n) if status=="COMPLETE" else 1.0
        event=ExperimentRunRecord(
            event_id=f"{event_namespace}::{suite.product_id}::{idx:03d}::{_slug(case)}",
            decision_id=contract.decision_id,test_id=suite.test_id,test_signature=suite.test_signature,
            problem_shell=suite.problem_shell,shell_tags=("bootstrap","executable_contract",suite.product_id),
            search_generation=contract.search_generation,selection_round=idx,
            release_generation=release_generation,release_round=idx+1,
            contract_fingerprint=contract.fingerprint(),evidence_role=EvidenceRole.DEVELOPMENT,
            calibration_eligible=True,measurement_backreaction=False,backreaction_adjusted=False,
            before_uncertainty_by_axis={"declared_executable_contract_case_coverage":before},
            after_uncertainty_by_axis={"declared_executable_contract_case_coverage":after},
            compute_seconds=elapsed,run_status=status,measurement_valid=valid,
            provenance=(f"test_case:{target}",f"runner:{RUNNER_VERSION}",f"return_status:{status}",f"detail:{detail}"),
        )
        events.append(event)
    return tuple(events)


def compile_bootstrap_and_route(draft: BootstrapDraft, events: Iterable[ExperimentRunRecord], *, target_generation: int = 2):
    if draft.contract is None or draft.suite is None: raise ValueError("draft is not pilotable")
    events=tuple(events)
    snapshot=compile_calibration_snapshot(events,target_generation=target_generation,problem_shell=draft.suite.problem_shell)
    base=draft.contract
    future=ExperimentContract(
        decision_id=base.decision_id,search_generation=target_generation,selection_round=0,
        axes=base.axes,
        tests=tuple(TestChannel(
            test_id=t.test_id,title=t.title,expected_resolution_by_axis=dict(t.expected_resolution_by_axis),
            compute_seconds=None,reliability=None,evidence_role=t.evidence_role,selection_generation=target_generation,
            measurement_backreaction=t.measurement_backreaction,backreaction_adjusted=t.backreaction_adjusted,
            calibration_id=None,test_signature=t.test_signature,notes=t.notes,
        ) for t in base.tests),problem_shell=base.problem_shell,provenance=base.provenance,
    )
    hydrated=hydrate_contract_from_calibration(future,snapshot)
    plan=choose_next_experiment(hydrated)
    return future, hydrated, snapshot, plan


def audit_queue_bootstrap_readiness(queue: Iterable[Mapping[str,object]], *, root: str | Path | None = None) -> dict:
    core=Path(root).resolve() if root is not None else Path(__file__).resolve().parent
    suites=discover_existing_composition_suites(core)
    component_surfaces=discover_foundry_component_test_surfaces(core)
    rows=list(queue); matches=[]; status_counts={}
    for i,row in enumerate(rows):
        key=(str(row.get("supplier_id","")),str(row.get("consumer_id","")))
        suite=suites.get(key)
        if suite:
            status="FIXED_PILOT_SCHEDULE_AVAILABLE"
            detail={"queue_index":i,"supplier_id":key[0],"consumer_id":key[1],"product_id":suite.product_id,"case_count":len(suite.cases),"problem_shell":suite.problem_shell}
            matches.append(detail)
        elif key[1] in component_surfaces:
            status="ADAPTER_REQUIRED_CONSUMER_INVARIANT_SUITE_AVAILABLE"
        elif key[0] in component_surfaces:
            status="SUPPLIER_INVARIANT_SUITE_AVAILABLE_NO_COMPOSITION_HARNESS"
        else:
            status="NO_EXECUTABLE_TEST_SURFACE_DISCOVERED"
        status_counts[status]=status_counts.get(status,0)+1
    return {
        "model_version":MODEL_VERSION,"queue_rows":len(rows),
        "pilotable_existing_suite_rows":status_counts.get("FIXED_PILOT_SCHEDULE_AVAILABLE",0),
        "not_pilotable_existing_suite_rows":len(rows)-status_counts.get("FIXED_PILOT_SCHEDULE_AVAILABLE",0),
        "status_counts":status_counts,"foundry_component_test_surfaces":len(component_surfaces),
        "pilotable_rows":matches,
        "policy":"Completed composition suites can run fixed pilots now. Component-only suites are preserved as adapter/harness targets and are not counted as composition evidence.",
    }
