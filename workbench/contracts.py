"""One bounded task contract; source identity is distinct from document identity."""
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from graphlib import TopologicalSorter, CycleError
import hashlib
import json
from .limits import LINEAGE_NODES, LINEAGE_RULE_INPUTS


@dataclass(frozen=True)
class DependencyProblem:
    id: str
    bases: Mapping[str, str]
    rules: tuple[tuple[str, tuple[str, ...]], ...]
    targets: tuple[str, ...]
    mode: str = 'declared_support'
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        # Own semantic inputs before validation; compiled adapters must see stable data.
        object.__setattr__(self, 'bases', MappingProxyType(dict(self.bases)))
        object.__setattr__(self, 'rules', tuple((head, tuple(body)) for head, body in self.rules))
        object.__setattr__(self, 'targets', tuple(self.targets))
        # Annotations remain editable, but caller-owned input/export data is detached.
        object.__setattr__(self, 'metadata', deepcopy(self.metadata))
        if not self.id or self.mode not in ('declared_support', 'static_formula_lineage'):
            raise ValueError('A problem ID and supported semantics are required')
        identifiers = list(self.bases) + list(self.bases.values()) + list(self.targets)
        for head, body in self.rules:
            identifiers.extend((head, *body))
        if any(not isinstance(v, str) or not v for v in identifiers):
            raise ValueError('All proposition and source identities must be nonempty strings')
        heads = {h for h, _ in self.rules}
        if heads & self.bases.keys():
            raise ValueError('An input proposition cannot also be a derived proposition')
        known = set(self.bases) | heads
        if len(known) > LINEAGE_NODES or sum(len(b) for _, b in self.rules) > LINEAGE_RULE_INPUTS:
            raise ValueError(
                f'Pilot task size exceeded: {LINEAGE_NODES:,} nodes / {LINEAGE_RULE_INPUTS:,} rule inputs')
        if not self.targets or len(set(self.targets)) != len(self.targets):
            raise ValueError('Targets must be nonempty and unique')
        if not set(self.targets) <= known or any(not set(b) <= known for _, b in self.rules):
            raise ValueError('Unknown target or rule premise')
        self.order()

    @property
    def sources(self):
        return tuple(sorted(set(self.bases.values())))

    def order(self):
        graph = {p: set() for p in self.bases}
        for head, body in self.rules:
            graph.setdefault(head, set()).update(body)
        try:
            return tuple(TopologicalSorter(graph).static_order())
        except CycleError as exc:
            raise ValueError('Cyclic dependencies require a different task adapter') from exc

    def to_dict(self):
        return {'schema_version': 1, 'id': self.id, 'mode': self.mode,
                'bases': dict(self.bases), 'rules': [{'head': h, 'body': list(b)} for h, b in self.rules],
                'targets': list(self.targets), 'metadata': deepcopy(self.metadata)}

    @classmethod
    def from_dict(cls, data):
        if data.get('schema_version') != 1:
            raise ValueError('Unsupported problem schema')
        return cls(data['id'], dict(data['bases']),
                   tuple((r['head'], tuple(r['body'])) for r in data['rules']),
                   tuple(data['targets']), data.get('mode', 'declared_support'), data.get('metadata', {}))

    def digest(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()


def check_scenarios(problem, scenarios):
    if len(scenarios) > 8192:
        raise ValueError('At most 8192 failure scenarios per batch')
    known = set(problem.sources)
    if any(not set(s) <= known for s in scenarios):
        raise ValueError('A failure scenario references an unknown source')
