"""Minimal campaign memory for LabAllCompass R12.

This is intentionally not a new ontology. It records what the Lab actually did:
edge adjudications, completed executable compositions, and future explicit campaign
outcomes. Mechanics telemetry is never auto-promoted to scientific success.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import hashlib, json

MODEL_VERSION="LAB_CAMPAIGN_MEMORY_R12_V1"
PROTECTED_LEVELS={"PROTECTED_VALIDATION"}
LEARNING_LEVELS={"DEVELOPMENT","OOS","OPERATIONAL","SHADOW"}

@dataclass(frozen=True)
class CampaignEvent:
    event_id: str
    campaign_id: str
    generation: int
    subject_type: str
    subject_id: str
    outcome: str
    evidence_level: str
    problem_shell: str
    supplier_id: str|None=None
    consumer_id: str|None=None
    product_id: str|None=None
    failure_code: str|None=None
    learning_eligible: bool=False
    release_generation: int|None=None
    provenance: tuple[str,...]=()

    def __post_init__(self):
        if not self.event_id or not self.subject_id: raise ValueError("event_id and subject_id required")
        if self.generation<0: raise ValueError("generation must be non-negative")
        if self.evidence_level in PROTECTED_LEVELS and self.learning_eligible:
            raise ValueError("protected validation cannot be learning_eligible")
        if self.learning_eligible and self.evidence_level not in LEARNING_LEVELS:
            raise ValueError("mechanics/bootstrap evidence cannot train empirical relevance")
        if self.learning_eligible and self.release_generation is None:
            raise ValueError("learning-eligible campaign evidence requires explicit release_generation")
        if self.release_generation is not None and self.release_generation < self.generation:
            raise ValueError("release_generation cannot precede selection generation")

    def to_dict(self)->dict:
        return {"model_version":MODEL_VERSION,"event_id":self.event_id,"campaign_id":self.campaign_id,
            "generation":self.generation,"subject_type":self.subject_type,"subject_id":self.subject_id,
            "outcome":self.outcome,"evidence_level":self.evidence_level,"problem_shell":self.problem_shell,
            "supplier_id":self.supplier_id,"consumer_id":self.consumer_id,"product_id":self.product_id,
            "failure_code":self.failure_code,"learning_eligible":self.learning_eligible,"release_generation":self.release_generation,"provenance":list(self.provenance)}

    @classmethod
    def from_dict(cls,obj:Mapping[str,object])->"CampaignEvent":
        return cls(
            event_id=str(obj["event_id"]),campaign_id=str(obj.get("campaign_id","UNSPECIFIED")),
            generation=int(obj.get("generation",0)),subject_type=str(obj.get("subject_type","UNKNOWN")),
            subject_id=str(obj["subject_id"]),outcome=str(obj.get("outcome","INCONCLUSIVE")),
            evidence_level=str(obj.get("evidence_level","UNSPECIFIED")),problem_shell=str(obj.get("problem_shell","UNSPECIFIED")),
            supplier_id=(str(obj["supplier_id"]) if obj.get("supplier_id") else None),
            consumer_id=(str(obj["consumer_id"]) if obj.get("consumer_id") else None),
            product_id=(str(obj["product_id"]) if obj.get("product_id") else None),
            failure_code=(str(obj["failure_code"]) if obj.get("failure_code") else None),
            learning_eligible=bool(obj.get("learning_eligible",False)),
            release_generation=(None if obj.get("release_generation") is None else int(obj["release_generation"])),
            provenance=tuple(str(x) for x in obj.get("provenance",())),
        )


def load_events(path:str|Path)->tuple[CampaignEvent,...]:
    p=Path(path)
    if not p.exists(): return ()
    return tuple(CampaignEvent.from_dict(json.loads(x)) for x in p.read_text(encoding="utf-8").splitlines() if x.strip())


def save_events(path:str|Path,events:Iterable[CampaignEvent])->None:
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    rows=sorted(events,key=lambda e:e.event_id)
    if len({e.event_id for e in rows})!=len(rows): raise ValueError("duplicate campaign event_id")
    p.write_text(''.join(json.dumps(e.to_dict(),sort_keys=True,ensure_ascii=False)+'\n' for e in rows),encoding='utf-8')


def bootstrap_current_memory(core_root:str|Path, telemetry_index:Mapping[str,object]) -> tuple[CampaignEvent,...]:
    core=Path(core_root).resolve(); out=[]
    # Exact negative knowledge from adjudication ledger.
    adj=core/"COMPOSITION_EDGE_ADJUDICATIONS.jsonl"
    if adj.exists():
        for line in adj.read_text(encoding='utf-8').splitlines():
            if not line.strip():continue
            r=json.loads(line); pair=f"{r['supplier_id']}->{r['consumer_id']}"
            out.append(CampaignEvent(
                event_id=f"ADJ::{r.get('adjudication_generation','UNKNOWN')}::{pair}",campaign_id="LAB_CORE",
                generation=0,subject_type="COMPOSITION_EDGE",subject_id=pair,outcome="REJECTED_CURRENT_INTERFACE",
                evidence_level="INTERFACE_ADJUDICATION",problem_shell="CURRENT_INTERFACE_ONLY",
                supplier_id=r['supplier_id'],consumer_id=r['consumer_id'],failure_code="EXPLICIT_INTERFACE_REJECTION",
                learning_eligible=False,provenance=("COMPOSITION_EDGE_ADJUDICATIONS.jsonl",)))
    # Completed executable composites are mechanics evidence only.
    from experiment_contract_bootstrap import discover_existing_composition_suites
    by_edge=dict(telemetry_index.get('by_edge',{}))
    for (supplier,consumer),suite in sorted(discover_existing_composition_suites(core).items()):
        pair=f"{supplier}->{consumer}"; n=int(dict(by_edge.get(pair,{})).get('event_count',0))
        out.append(CampaignEvent(
            event_id=f"MECH::{suite.product_id}::{suite.source_hash[:16]}",campaign_id="LAB_CORE",generation=0,
            subject_type="COMPOSITION",subject_id=pair,outcome="EXECUTABLE_CONTRACT_PASS",
            evidence_level="MECHANICS",problem_shell=suite.problem_shell,supplier_id=supplier,consumer_id=consumer,
            product_id=suite.product_id,learning_eligible=False,
            provenance=(f"suite:{suite.test_file}",f"standardized_telemetry_events:{n}")))
    return tuple(out)


def append_event(path:str|Path,event:CampaignEvent)->None:
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    existing=[]
    if p.exists():
        existing=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    if any(str(x.get("event_id"))==event.event_id for x in existing):
        raise ValueError(f"duplicate campaign event_id: {event.event_id}")
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event.to_dict(),sort_keys=True,ensure_ascii=False)+"\n")


def to_feedback_events(events:Iterable[CampaignEvent]):
    """Convert only explicitly learning-eligible empirical outcomes to R3 feedback.

    Interface rejections and mechanics telemetry remain campaign memory/negative map
    knowledge; protected validation never becomes adaptive retrieval feedback.
    """
    from relevance_learning import FeedbackEvent,HELPED,HURT,NEUTRAL,LEARN_AFTER_GENERATION
    outcome_map={"PASS":HELPED,"HELPED":HELPED,"FAIL":HURT,"HURT":HURT,"NEUTRAL":NEUTRAL}
    out=[]
    for e in events:
        if not e.learning_eligible or e.outcome not in outcome_map:
            continue
        subject=e.supplier_id if e.subject_type in {"COMPOSITION","COMPOSITION_EDGE"} and e.supplier_id else e.subject_id
        consumer=e.consumer_id if e.subject_type in {"COMPOSITION","COMPOSITION_EDGE"} else None
        out.append(FeedbackEvent(
            event_id="CAMPAIGN::"+e.event_id,subject_id=subject,selection_generation=e.generation,
            release_generation=int(e.release_generation),problem_shell=e.problem_shell,outcome=outcome_map[e.outcome],
            role=LEARN_AFTER_GENERATION,consumer_id=consumer,
            provenance={"campaign_id":e.campaign_id,"campaign_subject":e.subject_id,"evidence_level":e.evidence_level},
        ))
    return tuple(out)


def build_summary(events:Iterable[CampaignEvent])->dict:
    rows=list(events); counts={}; evidence={}; failures={}
    for e in rows:
        counts[e.outcome]=counts.get(e.outcome,0)+1
        evidence[e.evidence_level]=evidence.get(e.evidence_level,0)+1
        if e.failure_code: failures[e.failure_code]=failures.get(e.failure_code,0)+1
    payload={"model_version":MODEL_VERSION,"events":len(rows),"outcomes":counts,"evidence_levels":evidence,
        "failure_codes":failures,"learning_eligible_events":sum(e.learning_eligible for e in rows),
        "policy":"Mechanics/bootstrap events remain mechanics; only explicitly eligible non-protected empirical outcomes may train future relevance."}
    payload['fingerprint']=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return payload
