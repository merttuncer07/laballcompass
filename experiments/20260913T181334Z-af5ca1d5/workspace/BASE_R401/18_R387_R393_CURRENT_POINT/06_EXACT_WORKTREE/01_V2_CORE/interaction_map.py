"""Typed interaction map for LabAllCompass R12.

The map separates facts from hypotheses. It does not collapse every relation into
one fuzzy edge weight.

Relation classes:
- COMPLETED_COMPOSITION: executable V2 adapter exists for supplier -> consumer.
- CURATED_HYPOTHESIS: explicitly curated active edge, not yet proven.
- INFERRED_CANDIDATE: algorithmic queue suggestion; search frontier only.
- REJECTED_CURRENT_INTERFACE: explicit negative edge-local knowledge.
- PARENT_OF: executable Foundry parent provenance.

Search-time exact interaction expansion uses completed + active curated relations.
Inferred candidates remain available through the candidate queue/fuzzy supplier
search and are never mislabeled as known interactions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import csv, hashlib, json, re

from simple_lexicon import CanonicalPrimitive

MODEL_VERSION = "LAB_INTERACTION_MAP_R12_V1"

COMPLETED = "COMPLETED_COMPOSITION"
CURATED = "CURATED_HYPOTHESIS"
INFERRED = "INFERRED_CANDIDATE"
REJECTED = "REJECTED_CURRENT_INTERFACE"
PARENT_OF = "PARENT_OF"


@dataclass(frozen=True)
class InteractionEdge:
    source_id: str
    target_id: str
    relation: str
    active: bool
    provenance: tuple[str, ...] = ()
    product_id: str | None = None
    rationale: str | None = None
    telemetry_events: int = 0

    def key(self) -> tuple[str, str, str]:
        return (self.source_id, self.target_id, self.relation)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "active": self.active,
            "product_id": self.product_id,
            "rationale": self.rationale,
            "telemetry_events": self.telemetry_events,
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class InteractionMap:
    edges: tuple[InteractionEdge, ...]
    fingerprint: str
    nodes: tuple[dict, ...] = ()

    def to_dict(self) -> dict:
        counts = {}
        for e in self.edges:
            counts[e.relation] = counts.get(e.relation, 0) + 1
        node_counts = {}
        for n in self.nodes:
            node_counts[str(n.get("node_type","UNKNOWN"))] = node_counts.get(str(n.get("node_type","UNKNOWN")),0)+1
        return {
            "model_version": MODEL_VERSION,
            "fingerprint": self.fingerprint,
            "node_count": len(self.nodes),
            "node_counts": node_counts,
            "edge_count": len(self.edges),
            "relation_counts": counts,
            "nodes": list(self.nodes),
            "edges": [e.to_dict() for e in self.edges],
            "semantics": {
                "primitive_nodes": "canonical mechanism identity is primitive + constraint shell; domain/source concept are provenance only",
                "inferred_edges": "search hypotheses only; never promoted to known interaction by map construction",
                "rejected_edges": "preserved negative interface knowledge; inactive for propagation",
            },
        }

    def save(self, path: str | Path) -> None:
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)+"\n", encoding="utf-8")

    def neighbors(self, node_id: str, *, relations: Iterable[str] | None = None, active_only: bool = True) -> tuple[dict, ...]:
        allowed = None if relations is None else set(relations)
        out=[]
        for e in self.edges:
            if active_only and not e.active: continue
            if allowed is not None and e.relation not in allowed: continue
            if e.source_id == node_id:
                out.append({"direction":"OUT","neighbor_id":e.target_id,"edge":e.to_dict()})
            elif e.target_id == node_id:
                out.append({"direction":"IN","neighbor_id":e.source_id,"edge":e.to_dict()})
        order={COMPLETED:0,CURATED:1,PARENT_OF:2,INFERRED:3,REJECTED:4}
        out.sort(key=lambda r:(order.get(r["edge"]["relation"],9),r["direction"],r["neighbor_id"]))
        return tuple(out)

    def search_adjacency(self) -> dict[str, dict[str, float]]:
        """Adjacency for identity-seeded supplier search.

        Only relations with explicit map standing propagate. Numeric values encode
        relation class only, not a learned scientific confidence score.
        """
        adj: dict[str, dict[str, float]] = {}
        # Completed edge should dominate a curated hypothesis when both connect the same pair.
        relation_weight={COMPLETED:1.0,CURATED:0.70,PARENT_OF:0.55}
        for e in self.edges:
            if not e.active or e.relation not in relation_weight: continue
            w=relation_weight[e.relation]
            # Consumer -> supplier is the useful repair/complement direction for search.
            if e.relation in {COMPLETED,CURATED}:
                a,b=e.target_id,e.source_id
                adj.setdefault(a,{})[b]=max(w,adj.get(a,{}).get(b,0.0))
                adj.setdefault(b,{})[a]=max(0.40*w,adj.get(b,{}).get(a,0.0))
            elif e.relation==PARENT_OF:
                adj.setdefault(e.target_id,{})[e.source_id]=max(w,adj.get(e.target_id,{}).get(e.source_id,0.0))
                adj.setdefault(e.source_id,{})[e.target_id]=max(0.40*w,adj.get(e.source_id,{}).get(e.target_id,0.0))
        return adj


def _fingerprint(edges: Iterable[InteractionEdge], nodes: Iterable[Mapping[str, object]] = ()) -> str:
    payload=[e.to_dict() for e in sorted(edges,key=lambda x:x.key())]
    node_payload=sorted((dict(n) for n in nodes), key=lambda n:str(n.get("node_id","")))
    raw=json.dumps({"model_version":MODEL_VERSION,"nodes":node_payload,"edges":payload},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _parse_parent_names(path: Path) -> tuple[str, ...]:
    if not path.exists(): return ()
    text=path.read_text(encoding="utf-8",errors="replace")
    names=set()
    # Full current IM parent IDs.
    names.update(m.group(1) for m in re.finditer(r"\b(IM\d+(?:_IM\d+)*_[A-Z0-9]+)\b", text))
    # Historical R... identifiers; retain their trailing mechanism acronym.
    for m in re.finditer(r"\b(R\d+(?:_[A-Z0-9]+)+)\b", text):
        full=m.group(1); names.add(full); names.add(full.rsplit("_",1)[-1])
    # Bullet labels such as SACPS source:, ACSA:, LCM <hash>, etc.
    for line in text.splitlines():
        m=re.match(r"\s*-\s+([A-Z][A-Z0-9]{2,12})(?!_)(?:\s+source)?(?:\s+|\s*[:`/])", line)
        if m:
            label=m.group(1)
            if label != "SHA256" and not re.fullmatch(r"P\d+",label):
                names.add(label)
    return tuple(sorted(names))


def compile_interaction_map(core_root: str | Path, *, telemetry_index: Mapping[str, object] | None = None) -> InteractionMap:
    core=Path(core_root).resolve()
    queue_path=core/"generated_v2_foundry"/"CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json"
    universe_path=core/"generated_v2_foundry"/"CORE_V2_FOUNDRY_CANDIDATE_UNIVERSE.jsonl"
    rejected_path=core/"generated_v2_foundry"/"CORE_V2_FOUNDRY_REJECTED_EDGES.json"
    registry_path=core/"generated_v2_foundry"/"CORE_V2_FOUNDRY_UNIFIED_REGISTRY.jsonl"
    if universe_path.exists():
        rows=[json.loads(x) for x in universe_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        rows=[r for r in rows if r.get('active_for_build',True)]
        candidate_provenance='candidate_universe.inferred'
    else:
        rows=json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.exists() else []
        candidate_provenance='composition_queue.inferred'
    rejected=json.loads(rejected_path.read_text(encoding="utf-8")) if rejected_path.exists() else []

    # Map V2 suite by pair.
    from experiment_contract_bootstrap import discover_existing_composition_suites
    suites=discover_existing_composition_suites(core)
    telemetry_by_edge={}
    if telemetry_index:
        telemetry_by_edge=dict(telemetry_index.get("by_edge",{}))

    edges: dict[tuple[str,str,str],InteractionEdge]={}
    def add(edge: InteractionEdge):
        key=edge.key()
        old=edges.get(key)
        if old is None or (edge.telemetry_events, bool(edge.product_id)) > (old.telemetry_events, bool(old.product_id)):
            edges[key]=edge

    # All active candidate-universe rows remain represented; the top-1000 queue is only a priority window.
    for r in rows:
        pair=(str(r["supplier_id"]),str(r["consumer_id"]))
        suite=suites.get(pair)
        edge_key=f"{pair[0]}->{pair[1]}"
        tcount=int(dict(telemetry_by_edge.get(edge_key,{})).get("event_count",0))
        if suite is not None:
            add(InteractionEdge(pair[0],pair[1],COMPLETED,True,
                provenance=("completed_v2_suite",suite.test_file),product_id=suite.product_id,
                rationale=str(r.get("curated_rationale") or "") or None,telemetry_events=tcount))
        elif bool(r.get("curated")):
            add(InteractionEdge(pair[0],pair[1],CURATED,True,
                provenance=("composition_queue.curated",),rationale=str(r.get("curated_rationale") or "") or None,
                telemetry_events=tcount))
        else:
            add(InteractionEdge(pair[0],pair[1],INFERRED,True,
                provenance=(candidate_provenance,),telemetry_events=tcount))

    for r in rejected:
        add(InteractionEdge(str(r["supplier_id"]),str(r["consumer_id"]),REJECTED,False,
            provenance=("composition_edge_adjudication",str(r.get("adjudication_generation") or "")),
            rationale=str(r.get("adjudication_reason") or r.get("reason") or "") or None))

    # Explicit Foundry parent provenance. Match parent directory names exactly to registry nodes.
    registry=[]
    if registry_path.exists():
        registry=[json.loads(x) for x in registry_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    parent_by_alias={}
    if (core/"generated"/"FOUNDRY_PARENT_INTERFACE_REGISTRY.json").exists():
        rich_parents=json.loads((core/"generated"/"FOUNDRY_PARENT_INTERFACE_REGISTRY.json").read_text(encoding="utf-8"))
    else: rich_parents=[]
    by_cap={r["capability_id"]:r for r in registry}
    for r in rich_parents:
        cap="PARENT:"+str(r.get("product_dir"))
        aliases={str(r.get("product_dir",""))}
        if "_" in str(r.get("product_dir","")): aliases.add(str(r.get("product_dir")).rsplit("_",1)[-1])
        for mod in r.get("source_modules",[]):
            stem=Path(str(mod.get("file",""))).stem.upper()
            if stem: aliases.add(stem)
        for a in aliases:
            if a: parent_by_alias.setdefault(a,cap)
    products_root=core.parent/"02_FOUNDRY_ALL_PRODUCTS"/"products"
    if products_root.exists():
        for pdir in products_root.iterdir():
            if not pdir.is_dir(): continue
            m=re.match(r"(P\d+)_",pdir.name)
            if not m: continue
            consumer="FOUNDRY:"+m.group(1).upper()
            prov=pdir/"PARENT_PROVENANCE.md"
            seen_parent=set()
            for name in _parse_parent_names(prov):
                pid=parent_by_alias.get(name)
                if pid is None:
                    # Keep explicit historical parent provenance in the map even when
                    # that parent is not one of the 69 current searchable parents.
                    if name.startswith("R"):
                        pid="HISTORICAL_PARENT:"+name
                    elif any(name==x.rsplit("_",1)[-1] for x in _parse_parent_names(prov) if x.startswith("R")):
                        # Prefer the full historical R... ID when available; short alias
                        # will be represented by that same source rather than duplicated.
                        continue
                    else:
                        pid="HISTORICAL_PARENT:"+name
                if pid in seen_parent: continue
                seen_parent.add(pid)
                add(InteractionEdge(pid,consumer,PARENT_OF,True,provenance=(str(prov),)))

    # Complete node registry. Edges remain evidence-typed; node inclusion never
    # invents a mechanism interaction. Every searchable capability and primitive
    # is therefore present in the map even when it has no certified neighbor yet.
    nodes=[]
    for r in registry:
        nodes.append({
            "node_id": str(r["capability_id"]),
            "node_type": "CAPABILITY",
            "name": str(r.get("name") or r["capability_id"]),
            "family": str(r.get("family") or ""),
            "provenance": r.get("source",{}),
        })
    primitive_path=core/"search_data"/"LABALLCOMPASS_CANONICAL_INVENTORY_4000.tsv"
    if primitive_path.exists():
        with primitive_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cp=CanonicalPrimitive.from_row(row)
                nodes.append({
                    "node_id":"PRIMITIVE:"+str(row["id"]),
                    "node_type":"PRIMITIVE",
                    "canonical_id":cp.canonical_fingerprint,
                    "mechanism":cp.canonical_text,
                    "primitive":str(row["primitive"]),
                    "constraint_shell":str(row["constraint_shell"]),
                    "provenance":{
                        "domain":str(row["domain"]),
                        "source_concept":str(row["source_concept"]),
                    },
                })
    nodes=tuple(sorted(nodes,key=lambda n:str(n["node_id"])))
    ordered=tuple(sorted(edges.values(),key=lambda e:(e.relation,e.source_id,e.target_id)))
    return InteractionMap(ordered,_fingerprint(ordered,nodes),nodes)


def load_interaction_map(path: str | Path) -> InteractionMap:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    edges=tuple(InteractionEdge(
        source_id=str(e["source_id"]),target_id=str(e["target_id"]),relation=str(e["relation"]),active=bool(e["active"]),
        provenance=tuple(str(x) for x in e.get("provenance",())),product_id=e.get("product_id"),rationale=e.get("rationale"),telemetry_events=int(e.get("telemetry_events",0)),
    ) for e in obj.get("edges",()))
    nodes=tuple(dict(n) for n in obj.get("nodes",()))
    fp=str(obj.get("fingerprint") or _fingerprint(edges,nodes))
    return InteractionMap(edges,fp,nodes)
