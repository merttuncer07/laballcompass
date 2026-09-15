"""Interaction-aware certified incremental search for LabAllCompass.

Core idea:
    QUERY CHANGE
      -> which catalog scores can move directly?
      -> which connected mechanisms can move through the interaction map?
      -> can any resulting score interval cross the retrieval frontier?
      -> reuse the shortlist or selectively rescore the competitive region

The scoring function is intentionally transparent and linear in declared query
features. That makes score-movement bounds exact for this engine, so incremental
reuse is a certificate about retrieval equivalence to a full execution of the
same scoring function. It is not a claim that the scoring function is itself an
optimal scientific relevance model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import json, math, re, hashlib

SCORER_VERSION = "LAB_SEARCH_R12_2026-08-26"
TOKEN_RE = re.compile(r"[a-z0-9]+")
CAMEL_1 = re.compile(r"([a-z0-9])([A-Z])")
CAMEL_2 = re.compile(r"([A-Z]+)([A-Z][a-z])")
STOP = {
    "the", "and", "or", "to", "of", "a", "an", "in", "on", "for", "with",
    "from", "at", "by", "is", "are", "be", "when", "where", "using", "use",
    "into", "only", "current", "declared", "product", "candidate", "mechanism",
    "state", "evidence", "report", "this", "that", "under", "before", "after",
}
EVIDENCE_PRIOR = {
    "MECHANISM_BENCHMARKED": 4.0,
    "ORIGINAL_EXECUTABLE_PARENT": 4.0,
    "ORIGINAL_EXECUTABLE_MATERIAL": 4.0,
    "COMPLETED_V2_COMPOSITE": 4.0,
    "SALVAGED_SOURCE_WITH_REBUILT_TESTS": 3.0,
    "EXECUTABLE": 3.0,
    "MECHANISM_RECONSTRUCTED_FROM_RESULTS": 2.0,
    "SPEC_EXECUTABLE_FROM_RESULTS": 1.5,
    "NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID": 1.0,
    "PROTOTYPE_ONLY_OR_PENDING": 1.0,
}


def _lexical_text(text: str) -> str:
    text = CAMEL_2.sub(r"\1 \2", text)
    text = CAMEL_1.sub(r"\1 \2", text)
    return text.replace("_", " ").replace("-", " ")


def _raw_tokens(text: str) -> tuple[str, ...]:
    return tuple(t for t in TOKEN_RE.findall(_lexical_text(text).lower()) if len(t) > 2 and t not in STOP)


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_raw_tokens(text))


def _roots(text: str) -> frozenset[str]:
    # Low-weight morphology bridge. Five-character roots align reduce/reducer,
    # sufficient/sufficiency, calibrate/calibration, etc. Exact tokens remain
    # separately scored, so this is only a recall aid.
    return frozenset(t[:5] for t in _raw_tokens(text) if len(t) >= 6)


def _norm_phrase(text: str) -> str:
    return " ".join(TOKEN_RE.findall(_lexical_text(text).lower()))


def _evidence_prior(tier: str) -> float:
    if tier in EVIDENCE_PRIOR: return EVIDENCE_PRIOR[tier]
    u=tier.upper()
    if "MECHANISM_BENCHMARKED" in u or "ORIGINAL_EXECUTABLE" in u: return 4.0
    if "EXECUTABLE" in u: return 3.0
    if "RECONSTRUCTED" in u: return 2.0
    if "SPEC" in u: return 1.5
    return 1.0


@dataclass(frozen=True)
class SearchDocument:
    document_id: str
    name: str
    family: str
    text: str
    strength_tags: frozenset[str] = frozenset()
    input_types: frozenset[str] = frozenset()
    output_types: frozenset[str] = frozenset()
    domains: frozenset[str] = frozenset()
    weakness_tags: frozenset[str] = frozenset()
    evidence_tier: str = ""
    standalone_value: float = 0.0
    component_value: float = 0.0
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def normalized_text(self) -> str: return _norm_phrase(self.text)
    @property
    def text_tokens(self) -> frozenset[str]: return _tokens(self.text)
    @property
    def text_roots(self) -> frozenset[str]: return _roots(self.text)
    @property
    def name_tokens(self) -> frozenset[str]: return _tokens(self.name)
    @property
    def name_roots(self) -> frozenset[str]: return _roots(self.name)
    @property
    def alias_text(self) -> str:
        raw=self.metadata.get("search_aliases",())
        if isinstance(raw,str): return raw
        if isinstance(raw,Sequence): return " ".join(str(x) for x in raw)
        return ""
    @property
    def alias_tokens(self) -> frozenset[str]: return _tokens(self.alias_text)
    @property
    def alias_roots(self) -> frozenset[str]: return _roots(self.alias_text)
    @property
    def kind(self) -> str: return str(self.metadata.get("kind", "unknown"))
    @property
    def static_score(self) -> float:
        # Quality is deliberately a weak prior. Relevance must dominate retrieval.
        if self.family == "PRIMITIVE": return 0.05
        return 0.35*self.component_value + 0.10*self.standalone_value + 0.18*_evidence_prior(self.evidence_tier)


@dataclass(frozen=True)
class SearchQuery:
    text: str = ""
    search_terms: tuple[str, ...] = ()
    priority_phrases: tuple[tuple[str, float], ...] = ()
    preferred_strength_tags: tuple[str, ...] = ()
    available_input_types: tuple[str, ...] = ()
    preferred_output_types: tuple[str, ...] = ()
    preferred_domains: tuple[str, ...] = ()
    seed_document_ids: tuple[str, ...] = ()
    top_k: int = 20

    @classmethod
    def from_dict(cls, obj: Mapping[str, object], *, top_k: int | None = None) -> "SearchQuery":
        text_parts=[]
        for key in ("objective","diagnosed_failure","mechanism_needs","allowed_interventions","text","query"):
            v=obj.get(key)
            if isinstance(v,str): text_parts.append(v)
            elif isinstance(v,list): text_parts.extend(str(x) for x in v)
        priority=obj.get("priority_phrases",{})
        pp=tuple(sorted((str(k),float(v)) for k,v in priority.items())) if isinstance(priority,Mapping) else ()
        def tup(key: str) -> tuple[str,...]:
            v=obj.get(key,())
            if isinstance(v,str): return (v,)
            return tuple(str(x) for x in v) if isinstance(v,Sequence) else ()
        return cls(
            text=" ".join(text_parts), search_terms=tup("search_terms"), priority_phrases=pp,
            preferred_strength_tags=tup("preferred_strength_tags"),
            available_input_types=tup("available_input_types"),
            preferred_output_types=tup("preferred_output_types"),
            preferred_domains=tup("preferred_domains"),
            seed_document_ids=tup("seed_document_ids"),
            top_k=int(top_k if top_k is not None else obj.get("top_k",obj.get("candidate_limit",20))),
        )

    def to_dict(self) -> dict:
        return {
            "text":self.text,
            "search_terms":list(self.search_terms),
            "priority_phrases":{k:v for k,v in self.priority_phrases},
            "preferred_strength_tags":list(self.preferred_strength_tags),
            "available_input_types":list(self.available_input_types),
            "preferred_output_types":list(self.preferred_output_types),
            "preferred_domains":list(self.preferred_domains),
            "seed_document_ids":list(self.seed_document_ids),
            "top_k":self.top_k,
        }

    def feature_weights(self) -> dict[str,float]:
        f: dict[str,float]={}
        for t in _tokens(self.text): f[f"tok:{t}"]=f.get(f"tok:{t}",0.0)+0.48
        for r in _roots(self.text): f[f"root:{r}"]=f.get(f"root:{r}",0.0)+0.16
        for term in self.search_terms:
            p=_norm_phrase(term)
            if p: f[f"phrase:{p}"]=f.get(f"phrase:{p}",0.0)+2.4
        for phrase,w in self.priority_phrases:
            p=_norm_phrase(phrase)
            if p: f[f"phrase:{p}"]=f.get(f"phrase:{p}",0.0)+float(w)
        for tag in self.preferred_strength_tags: f[f"strength:{tag.lower()}"]=f.get(f"strength:{tag.lower()}",0.0)+2.2
        for v in self.available_input_types: f[f"input:{v.lower()}"]=f.get(f"input:{v.lower()}",0.0)+0.45
        for v in self.preferred_output_types: f[f"output:{v.lower()}"]=f.get(f"output:{v.lower()}",0.0)+1.35
        for v in self.preferred_domains: f[f"domain:{v.lower()}"]=f.get(f"domain:{v.lower()}",0.0)+1.2
        for doc_id in self.seed_document_ids: f[f"doc:{doc_id}"]=f.get(f"doc:{doc_id}",0.0)+8.0
        return f


@dataclass(frozen=True)
class SearchHit:
    document_id: str
    name: str
    family: str
    score: float
    score_lower: float
    score_upper: float
    exact_for_current_query: bool
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class SearchResult:
    hits: tuple[SearchHit,...]
    status: str
    documents_total: int
    documents_eligible: int
    query_features_changed: int
    documents_affected_by_delta: int
    exact_rescored_this_update: int
    exact_score_computations_total: int
    reused_without_rescore: int
    competitive_frontier_size: int


class InteractionGraph:
    """Fixed search-time interaction graph. Edge seed->target propagates relevance."""
    def __init__(self, adjacency: Mapping[str,Mapping[str,float]] | None = None):
        self.adjacency={str(s):{str(t):float(w) for t,w in tg.items() if float(w)>0} for s,tg in (adjacency or {}).items()}

    @classmethod
    def from_composition_queue(cls, path: str | Path) -> "InteractionGraph":
        adjacency: dict[str,dict[str,float]]={}
        rows=json.loads(Path(path).read_text(encoding="utf-8"))
        def add(a:str,b:str,w:float) -> None:
            adjacency.setdefault(a,{})[b]=max(w,adjacency.get(a,{}).get(b,0.0))
        for r in rows:
            interface=len(r.get("interface_matches",[])); addressed=len(r.get("addressed_weaknesses",[])); shared=len(r.get("shared_domains",[]))
            w=min(0.48,0.06+0.045*interface+0.060*addressed+0.012*shared+(0.10 if r.get("curated") else 0.0))
            # Search normally starts from a problem/consumer description and asks
            # what can help it, so consumer -> supplier is the strong direction.
            add(r["consumer_id"],r["supplier_id"],w)
            add(r["supplier_id"],r["consumer_id"],0.45*w)
        return cls(adjacency)

    @classmethod
    def from_typed_map(cls, path: str | Path) -> "InteractionGraph":
        from interaction_map import load_interaction_map
        return cls(load_interaction_map(path).search_adjacency())



class CertifiedIncrementalSearch:
    def __init__(self, documents: Iterable[SearchDocument], *, interaction_graph: InteractionGraph | None=None, excluded_ids: Iterable[str]=(), safety_margin: float=1e-12, score_offsets: Mapping[str,float] | None=None):
        docs=list(documents)
        if not docs: raise ValueError("documents must be non-empty")
        ids=[d.document_id for d in docs]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate document_id")
        self.documents={d.document_id:d for d in docs}; self._ids=tuple(ids)
        excluded=frozenset(excluded_ids); self._eligible_ids=tuple(i for i in self._ids if i not in excluded)
        if not self._eligible_ids: raise ValueError("no eligible documents after exclusions")
        self.graph=interaction_graph or InteractionGraph(); self.safety_margin=float(safety_margin)
        raw_offsets={str(k):float(v) for k,v in (score_offsets or {}).items()}
        unknown=set(raw_offsets)-set(self._ids)
        if unknown: raise ValueError(f"score_offsets contain unknown document ids: {sorted(unknown)[:5]}")
        if any(not math.isfinite(v) for v in raw_offsets.values()): raise ValueError("score_offsets must be finite")
        self._score_offsets={i:raw_offsets.get(i,0.0) for i in self._ids}
        self._token_index={}; self._root_index={}; self._alias_token_index={}; self._alias_root_index={}; self._strength_index={}; self._input_index={}; self._output_index={}; self._domain_index={}; self._phrase_cache={}; self._feature_coeff_cache={}
        self._doc_lengths={d.document_id:max(1,len(d.text_tokens)) for d in docs}
        self._avg_doc_length=sum(self._doc_lengths.values())/len(self._doc_lengths)
        self._build_indexes(docs)
        self._query=None; self._feature_weights={}; self._exact_scores={}; self._pending_bound={i:0.0 for i in self._ids}; self._last_top_ids=(); self.exact_score_computations=0
        self._fingerprint=self._compute_fingerprint()

    def _compute_fingerprint(self) -> str:
        payload={
            "scorer_version":SCORER_VERSION,
            "safety_margin":self.safety_margin,
            "eligible_ids":list(self._eligible_ids),
            "documents":[{
                "id":d.document_id,"name":d.name,"family":d.family,"text":d.text,
                "strength":sorted(d.strength_tags),"weakness":sorted(d.weakness_tags),
                "inputs":sorted(d.input_types),"outputs":sorted(d.output_types),"domains":sorted(d.domains),
                "tier":d.evidence_tier,"standalone":d.standalone_value,"component":d.component_value,
                "search_aliases":list(d.metadata.get("search_aliases",())) if not isinstance(d.metadata.get("search_aliases",()),str) else [d.metadata.get("search_aliases")],
            } for d in (self.documents[i] for i in self._ids)],
            "graph":{s:dict(sorted(t.items())) for s,t in sorted(self.graph.adjacency.items()) if s in self.documents},
            "score_offsets":{k:v for k,v in sorted(self._score_offsets.items()) if v!=0.0},
        }
        raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @property
    def fingerprint(self) -> str: return self._fingerprint

    def snapshot(self) -> dict:
        return {
            "snapshot_version":1,
            "engine_fingerprint":self._fingerprint,
            "query":self._query.to_dict() if self._query is not None else None,
            "exact_scores":self._exact_scores,
            "pending_bound":self._pending_bound,
            "last_top_ids":list(self._last_top_ids),
            "exact_score_computations":self.exact_score_computations,
        }

    def restore_snapshot(self,snapshot:Mapping[str,object]) -> bool:
        # Fail closed: stale state is never partially reused.
        if snapshot.get("snapshot_version")!=1 or snapshot.get("engine_fingerprint")!=self._fingerprint:
            return False
        qobj=snapshot.get("query")
        if qobj is None:
            return True
        if not isinstance(qobj,Mapping): return False
        exact=snapshot.get("exact_scores"); pending=snapshot.get("pending_bound"); top=snapshot.get("last_top_ids")
        if not isinstance(exact,Mapping) or not isinstance(pending,Mapping) or not isinstance(top,list): return False
        if set(exact)!=set(self._ids) or set(pending)!=set(self._ids): return False
        if any(x not in self._eligible_ids for x in top): return False
        try:
            q=SearchQuery.from_dict(qobj)
            exact2={str(k):float(v) for k,v in exact.items()}
            pending2={str(k):float(v) for k,v in pending.items()}
            if any(not math.isfinite(v) or v<0 for v in pending2.values()): return False
            if any(not math.isfinite(v) for v in exact2.values()): return False
        except Exception:
            return False
        self._query=q; self._feature_weights=q.feature_weights(); self._exact_scores=exact2; self._pending_bound=pending2; self._last_top_ids=tuple(top); self.exact_score_computations=int(snapshot.get("exact_score_computations",0))
        return True

    def _build_indexes(self,docs):
        for d in docs:
            for t in d.text_tokens: self._token_index.setdefault(t,set()).add(d.document_id)
            for r in d.text_roots: self._root_index.setdefault(r,set()).add(d.document_id)
            for t in d.alias_tokens: self._alias_token_index.setdefault(t,set()).add(d.document_id)
            for r in d.alias_roots: self._alias_root_index.setdefault(r,set()).add(d.document_id)
            for t in d.strength_tags: self._strength_index.setdefault(t.lower(),set()).add(d.document_id)
            for t in d.input_types: self._input_index.setdefault(t.lower(),set()).add(d.document_id)
            for t in d.output_types: self._output_index.setdefault(t.lower(),set()).add(d.document_id)
            for t in d.domains: self._domain_index.setdefault(t.lower(),set()).add(d.document_id)

    def _direct_matching_docs(self,feature:str) -> frozenset[str]:
        kind,value=feature.split(":",1)
        if kind=="tok": return frozenset(set(self._token_index.get(value,()))|set(self._alias_token_index.get(value,())))
        if kind=="root": return frozenset(set(self._root_index.get(value,()))|set(self._alias_root_index.get(value,())))
        if kind=="strength": return frozenset(self._strength_index.get(value,()))
        if kind=="input": return frozenset(self._input_index.get(value,()))
        if kind=="output": return frozenset(self._output_index.get(value,()))
        if kind=="domain": return frozenset(self._domain_index.get(value,()))
        if kind=="doc": return frozenset((value,)) if value in self.documents else frozenset()
        if kind=="phrase":
            if value not in self._phrase_cache:
                needle=f" {value} "; self._phrase_cache[value]=frozenset(d.document_id for d in self.documents.values() if needle in f" {d.normalized_text} ")
            return self._phrase_cache[value]
        raise ValueError(f"unknown search feature kind: {kind}")

    def _base_idf(self,feature:str,df:int) -> float:
        kind=feature.split(":",1)[0]
        if kind in {"tok","root"}:
            return min(4.0,1.0+math.log((len(self._ids)+1)/(df+1)))
        return 1.0

    def _direct_coefficient(self,feature:str,doc_id:str,base_idf:float) -> float:
        kind,value=feature.split(":",1)
        if kind not in {"tok","root"}: return base_idf
        length=self._doc_lengths[doc_id]
        # BM25-like fixed length normalization. It prevents verbose provenance
        # blobs from winning merely because they contain more distinct words.
        length_norm=1.0/(0.45+0.55*(length/self._avg_doc_length))
        length_norm=min(1.55,max(0.35,length_norm))
        doc=self.documents[doc_id]
        name_match=(value in doc.name_tokens) if kind=="tok" else (value in doc.name_roots)
        canonical_match=(value in doc.text_tokens) if kind=="tok" else (value in doc.text_roots)
        alias_match=(value in doc.alias_tokens) if kind=="tok" else (value in doc.alias_roots)
        # Provenance/domain aliases are retrieval bridges only. Canonical primitive
        # wording remains the stronger signal and defines mechanism identity.
        alias_factor=0.45 if alias_match and not canonical_match else 1.0
        return base_idf*length_norm*(1.75 if name_match else 1.0)*alias_factor

    def _feature_coefficients(self,feature:str) -> Mapping[str,float]:
        cached=self._feature_coeff_cache.get(feature)
        if cached is not None: return cached
        direct=self._direct_matching_docs(feature); base=self._base_idf(feature,len(direct))
        coeff: dict[str,float]={}
        for seed in direct:
            direct_c=self._direct_coefficient(feature,seed,base)
            coeff[seed]=coeff.get(seed,0.0)+direct_c
            for target,w in self.graph.adjacency.get(seed,{}).items():
                if target in self.documents:
                    coeff[target]=coeff.get(target,0.0)+direct_c*w
        # Per-feature cap limits graph hubs without breaking linearity.
        cap=2.4*base
        coeff={d:min(v,cap) for d,v in coeff.items()}
        self._feature_coeff_cache[feature]=coeff
        return coeff

    def _score(self,doc_id:str,weights:Mapping[str,float]) -> float:
        s=self.documents[doc_id].static_score+self._score_offsets.get(doc_id,0.0)
        for feature,w in weights.items(): s += w*self._feature_coefficients(feature).get(doc_id,0.0)
        self.exact_score_computations += 1
        return s

    def _exact_rescore(self,ids:Iterable[str]) -> int:
        unique=tuple(dict.fromkeys(ids))
        for d in unique:
            self._exact_scores[d]=self._score(d,self._feature_weights); self._pending_bound[d]=0.0
        return len(unique)

    def _interval(self,d):
        return self._exact_scores[d]-self._pending_bound[d], self._exact_scores[d]+self._pending_bound[d]

    def _hit(self,d):
        lo,hi=self._interval(d); x=self.documents[d]
        return SearchHit(d,x.name,x.family,self._exact_scores[d],lo,hi,self._pending_bound[d]==0.0,x.metadata)

    def full_search(self,query:SearchQuery) -> SearchResult:
        if query.top_k<=0: raise ValueError("top_k must be positive")
        self._query=query; self._feature_weights=query.feature_weights(); before=self.exact_score_computations
        self._exact_rescore(self._ids)
        ranked=sorted(self._eligible_ids,key=lambda d:(-self._exact_scores[d],d)); self._last_top_ids=tuple(ranked[:min(query.top_k,len(ranked))])
        return SearchResult(tuple(self._hit(d) for d in self._last_top_ids),"FULL_SEARCH",len(self._ids),len(self._eligible_ids),len(self._feature_weights),len(self._ids),self.exact_score_computations-before,self.exact_score_computations,0,len(self._eligible_ids))

    def update(self,query:SearchQuery) -> SearchResult:
        if self._query is None: return self.full_search(query)
        if query.top_k!=self._query.top_k: return self.full_search(query)
        new=query.feature_weights(); changed={f:new.get(f,0.0)-self._feature_weights.get(f,0.0) for f in set(new)|set(self._feature_weights) if new.get(f,0.0)!=self._feature_weights.get(f,0.0)}
        affected=set()
        for f,delta in changed.items():
            for d,c in self._feature_coefficients(f).items():
                affected.add(d); self._pending_bound[d]+=abs(delta*c)
        self._query=query; self._feature_weights=new; before=self.exact_score_computations; k=min(query.top_k,len(self._eligible_ids))
        if not affected:
            return SearchResult(tuple(self._hit(d) for d in self._last_top_ids),"QUERY_DELTA_NO_DOCUMENT_DEPENDENCY_REUSE",len(self._ids),len(self._eligible_ids),len(changed),0,0,self.exact_score_computations,len(self._ids),0)
        top=self._last_top_ids; top_set=set(top)
        membership=bool(top)
        if top:
            min_top=min(self._interval(d)[0] for d in top); max_out=max((self._interval(d)[1] for d in self._eligible_ids if d not in top_set),default=-math.inf)
            membership=min_top>max_out+self.safety_margin
        order=membership
        if order:
            for left,right in zip(top,top[1:]):
                if self._interval(left)[0] <= self._interval(right)[1]+self.safety_margin: order=False; break
        if membership and order:
            return SearchResult(tuple(self._hit(d) for d in top),"TOP_K_ORDER_REUSE_CERTIFIED",len(self._ids),len(self._eligible_ids),len(changed),len(affected),0,self.exact_score_computations,len(self._ids),0)
        if membership:
            rescored=self._exact_rescore(top); self._last_top_ids=tuple(sorted(top,key=lambda d:(-self._exact_scores[d],d)))
            return SearchResult(tuple(self._hit(d) for d in self._last_top_ids),"TOP_K_MEMBERSHIP_REUSED_ORDER_REFRESHED",len(self._ids),len(self._eligible_ids),len(changed),len(affected),rescored,self.exact_score_computations,len(self._ids)-rescored,len(top))
        lowers=sorted((self._interval(d)[0] for d in self._eligible_ids),reverse=True); kth=lowers[k-1]
        frontier=[d for d in self._eligible_ids if self._interval(d)[1]>=kth-self.safety_margin]
        rescored=self._exact_rescore(frontier); ranked=sorted(frontier,key=lambda d:(-self._exact_scores[d],d)); self._last_top_ids=tuple(ranked[:k])
        kth_exact=self._exact_scores[self._last_top_ids[-1]]; fset=set(frontier)
        uncertain=[d for d in self._eligible_ids if d not in fset and self._interval(d)[1]>=kth_exact-self.safety_margin]
        if uncertain:
            rescored+=self._exact_rescore(uncertain); frontier.extend(uncertain); self._last_top_ids=tuple(sorted(set(frontier),key=lambda d:(-self._exact_scores[d],d))[:k])
        return SearchResult(tuple(self._hit(d) for d in self._last_top_ids),"COMPETITIVE_FRONTIER_EXACT_REFRESH",len(self._ids),len(self._eligible_ids),len(changed),len(affected),rescored,self.exact_score_computations,len(self._ids)-rescored,rescored)

    def naive_top_ids(self,query:SearchQuery) -> tuple[str,...]:
        weights=query.feature_weights(); old=self.exact_score_computations
        try: scores={d:self._score(d,weights) for d in self._eligible_ids}
        finally: self.exact_score_computations=old
        return tuple(sorted(self._eligible_ids,key=lambda d:(-scores[d],d))[:min(query.top_k,len(self._eligible_ids))])

    def explain_score(self,doc_id:str,query:SearchQuery,limit:int=12) -> dict:
        parts=[]
        for f,w in query.feature_weights().items():
            c=self._feature_coefficients(f).get(doc_id,0.0)
            if c: parts.append((abs(w*c),f,w*c,c))
        parts.sort(reverse=True)
        return {"document_id":doc_id,"static_prior":self.documents[doc_id].static_score,"learned_relevance_prior":self._score_offsets.get(doc_id,0.0),"feature_contributions":[{"feature":f,"contribution":v,"dependency_coefficient":c} for _,f,v,c in parts[:limit]]}


class LabSearchRouter:
    """First-class Lab search surfaces over one corpus and one interaction map."""
    def __init__(self,documents:Iterable[SearchDocument],interaction_graph:InteractionGraph|None=None,relevance_snapshot=None):
        self.documents=tuple(documents); self.graph=interaction_graph or InteractionGraph(); self.by_id={d.document_id:d for d in self.documents}
        self.relevance_snapshot=relevance_snapshot
        offsets=dict(getattr(relevance_snapshot,'document_offsets',{}) or {})
        # Stage 1 is direct relevance. Interaction propagation is deliberately
        # reserved for explicit neighborhood/supplier expansion after a direct hit.
        cap_docs=[d for d in self.documents if d.kind=="capability"]
        prim_docs=[d for d in self.documents if d.kind=="primitive"]
        self.capability_engine=CertifiedIncrementalSearch(cap_docs,score_offsets={d.document_id:offsets[d.document_id] for d in cap_docs if d.document_id in offsets})
        self.primitive_engine=CertifiedIncrementalSearch(prim_docs,score_offsets={d.document_id:offsets[d.document_id] for d in prim_docs if d.document_id in offsets})
        self._supplier_engines={}

    def search_capabilities(self,query:SearchQuery,*,incremental:bool=True) -> SearchResult:
        return self.capability_engine.update(query) if incremental else self.capability_engine.full_search(query)

    def discover_primitives(self,query:SearchQuery,*,incremental:bool=True) -> SearchResult:
        return self.primitive_engine.update(query) if incremental else self.primitive_engine.full_search(query)

    def _supplier_engine(self,consumer_id:str) -> CertifiedIncrementalSearch:
        consumer=self.by_id[consumer_id]
        if consumer.kind!="capability": raise ValueError("consumer_id must identify a capability")
        engine=self._supplier_engines.get(consumer_id)
        if engine is None:
            supplier_offsets=(self.relevance_snapshot.supplier_offsets(consumer_id) if self.relevance_snapshot is not None and hasattr(self.relevance_snapshot,'supplier_offsets') else dict(getattr(self.relevance_snapshot,'document_offsets',{}) or {}))
            cap_docs=[d for d in self.documents if d.kind=="capability"]
            engine=CertifiedIncrementalSearch(cap_docs,interaction_graph=self.graph,excluded_ids={consumer_id},score_offsets={d.document_id:supplier_offsets[d.document_id] for d in cap_docs if d.document_id in supplier_offsets})
            self._supplier_engines[consumer_id]=engine
        return engine

    def search_suppliers(self,consumer_id:str,objective:str="",*,top_k:int=20,incremental:bool=True) -> SearchResult:
        consumer=self.by_id[consumer_id]
        engine=self._supplier_engine(consumer_id)
        q=SearchQuery(
            text=objective,
            preferred_strength_tags=tuple(sorted(consumer.weakness_tags)),
            preferred_output_types=tuple(sorted(consumer.input_types)),
            seed_document_ids=(consumer_id,),
            top_k=top_k,
        )
        return engine.update(q) if incremental else engine.full_search(q)


    def snapshot(self) -> dict:
        return {
            "snapshot_version":1,
            "capability":self.capability_engine.snapshot(),
            "primitive":self.primitive_engine.snapshot(),
            "suppliers":{cid:e.snapshot() for cid,e in self._supplier_engines.items()},
            "relevance_snapshot_fingerprint":getattr(self.relevance_snapshot,"fingerprint",None),
        }

    def restore_snapshot(self,snapshot:Mapping[str,object]) -> dict:
        status={"capability":False,"primitive":False,"suppliers":{}}
        if snapshot.get("snapshot_version")!=1: return status
        c=snapshot.get("capability"); p=snapshot.get("primitive")
        if isinstance(c,Mapping): status["capability"]=self.capability_engine.restore_snapshot(c)
        if isinstance(p,Mapping): status["primitive"]=self.primitive_engine.restore_snapshot(p)
        suppliers=snapshot.get("suppliers",{})
        if isinstance(suppliers,Mapping):
            for cid,snap in suppliers.items():
                if cid not in self.by_id or not isinstance(snap,Mapping): continue
                ok=self._supplier_engine(str(cid)).restore_snapshot(snap)
                status["suppliers"][str(cid)]=ok
        return status

    def save_snapshot(self,path:str|Path) -> None:
        Path(path).write_text(json.dumps(self.snapshot(),ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")

    def load_snapshot(self,path:str|Path) -> dict:
        return self.restore_snapshot(json.loads(Path(path).read_text(encoding="utf-8")))


def load_search_corpus(path:str|Path) -> list[SearchDocument]:
    rows=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        o=json.loads(line)
        rows.append(SearchDocument(
            o["document_id"],o["name"],o["family"],o["text"],
            frozenset(o.get("strength_tags",[])),frozenset(o.get("input_types",[])),
            frozenset(o.get("output_types",[])),frozenset(o.get("domains",[])),frozenset(o.get("weakness_tags",[])),
            o.get("evidence_tier",""),float(o.get("standalone_value",0.0)),float(o.get("component_value",0.0)),o.get("metadata",{}),
        ))
    return rows


def build_lab_search_router(corpus_path:str|Path,composition_queue_path:str|Path) -> LabSearchRouter:
    return LabSearchRouter(load_search_corpus(corpus_path),InteractionGraph.from_composition_queue(composition_queue_path))
