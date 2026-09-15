from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from typing import Hashable, Iterable, Mapping, Sequence


Support = frozenset[Hashable]
Family = frozenset[Support]


def minimal_family(supports: Iterable[Support]) -> Family:
    """Return the subset-minimal members of a finite support family."""
    unique = set(supports)
    if not unique:
        return frozenset()
    by_size: dict[int, set[Support]] = {}
    for support in unique:
        by_size.setdefault(len(support), set()).add(support)
    retained: set[Support] = set()
    retained_sizes: list[int] = []
    for size in sorted(by_size):
        for support in by_size[size]:
            absorbed = False
            for smaller_size in retained_sizes:
                for subset in combinations(support, smaller_size):
                    if frozenset(subset) in retained:
                        absorbed = True
                        break
                if absorbed:
                    break
            if not absorbed:
                retained.add(support)
        if any(len(item) == size for item in retained):
            retained_sizes.append(size)
    return frozenset(retained)


def family_or(left: Family, right: Family) -> Family:
    return minimal_family((*left, *right))


def family_and(left: Family, right: Family) -> Family:
    if not left or not right:
        return frozenset()
    return minimal_family(a | b for a in left for b in right)


@dataclass(frozen=True)
class Rule:
    head: Hashable
    body: tuple[Hashable, ...]


class MonotoneCircuit:
    """Hash-consed factored proof circuit; deliberately not canonical."""

    def __init__(self):
        self.nodes: list[tuple[str, tuple[int, ...] | Hashable | None]] = [
            ("false", None),
            ("true", None),
        ]
        self.unique: dict[tuple[str, tuple[int, ...] | Hashable | None], int] = {
            self.nodes[0]: 0,
            self.nodes[1]: 1,
        }

    def _intern(self, node):
        if node in self.unique:
            return self.unique[node]
        index = len(self.nodes)
        self.nodes.append(node)
        self.unique[node] = index
        return index

    def variable(self, label: Hashable) -> int:
        return self._intern(("var", label))

    def combine(self, operation: str, operands: Iterable[int]) -> int:
        if operation not in ("and", "or"):
            raise ValueError(operation)
        absorbing = 0 if operation == "and" else 1
        identity = 1 if operation == "and" else 0
        flattened: set[int] = set()
        for operand in operands:
            if operand == absorbing:
                return absorbing
            if operand == identity:
                continue
            node_operation, children = self.nodes[operand]
            if node_operation == operation:
                flattened.update(children)  # type: ignore[arg-type]
            else:
                flattened.add(operand)
        if not flattened:
            return identity
        if len(flattened) == 1:
            return next(iter(flattened))
        return self._intern((operation, tuple(sorted(flattened))))

    def conjunction(self, operands: Iterable[int]) -> int:
        return self.combine("and", operands)

    def disjunction(self, operands: Iterable[int]) -> int:
        return self.combine("or", operands)

    def evaluate(self, root: int, enabled: set[Hashable]) -> bool:
        if not isinstance(root, int) or not 0 <= root < len(self.nodes):
            raise ValueError("invalid circuit root")
        # Interning creates children before parents; evaluate reachable DAG iteratively.
        reachable = set()
        stack = [root]
        while stack:
            index = stack.pop()
            if index in reachable:
                continue
            reachable.add(index)
            operation, payload = self.nodes[index]
            if operation in ("and", "or"):
                stack.extend(payload)
        values = {}
        for index in sorted(reachable):
            operation, payload = self.nodes[index]
            if operation == "false": values[index] = False
            elif operation == "true": values[index] = True
            elif operation == "var": values[index] = payload in enabled
            elif operation == "and": values[index] = all(values[c] for c in payload)
            else: values[index] = any(values[c] for c in payload)
        return values[root]

    def reachable_count(self, root: int) -> int:
        seen: set[int] = set()
        stack = [root]
        while stack:
            index = stack.pop()
            if index in seen:
                continue
            seen.add(index)
            operation, payload = self.nodes[index]
            if operation in ("and", "or"):
                stack.extend(payload)  # type: ignore[arg-type]
        return len(seen)


class BDD:
    """Small canonical ROBDD manager for exact finite fixed-point quotienting."""

    def __init__(self, variable_order: Sequence[Hashable]):
        if len(set(variable_order)) != len(variable_order):
            raise ValueError("variable order must not contain duplicates")
        self.order = tuple(variable_order)
        self.rank = {variable: index for index, variable in enumerate(self.order)}
        self.nodes: list[tuple[int, int, int] | None] = [None, None]
        self.unique: dict[tuple[int, int, int], int] = {}
        self.apply_cache: dict[tuple[str, int, int], int] = {}

    def _make(self, rank: int, low: int, high: int) -> int:
        if low == high:
            return low
        key = (rank, low, high)
        if key in self.unique:
            return self.unique[key]
        index = len(self.nodes)
        self.nodes.append(key)
        self.unique[key] = index
        return index

    def variable(self, label: Hashable) -> int:
        return self._make(self.rank[label], 0, 1)

    def _terminal(self, operation: str, left: int, right: int) -> int | None:
        if operation == "and":
            if left == 0 or right == 0:
                return 0
            if left == 1:
                return right
            if right == 1 or left == right:
                return left
        elif operation == "or":
            if left == 1 or right == 1:
                return 1
            if left == 0:
                return right
            if right == 0 or left == right:
                return left
        else:
            raise ValueError(operation)
        return None

    def apply(self, operation: str, left: int, right: int) -> int:
        if left > right:
            left, right = right, left
        terminal = self._terminal(operation, left, right)
        if terminal is not None:
            return terminal
        key = (operation, left, right)
        if key in self.apply_cache:
            return self.apply_cache[key]
        left_node = self.nodes[left]
        right_node = self.nodes[right]
        assert left_node is not None and right_node is not None
        top = min(left_node[0], right_node[0])

        def cofactors(index: int, node):
            if node is not None and node[0] == top:
                return node[1], node[2]
            return index, index

        left_low, left_high = cofactors(left, left_node)
        right_low, right_high = cofactors(right, right_node)
        low = self.apply(operation, left_low, right_low)
        high = self.apply(operation, left_high, right_high)
        result = self._make(top, low, high)
        self.apply_cache[key] = result
        return result

    def conjunction(self, operands: Iterable[int]) -> int:
        result = 1
        for operand in operands:
            result = self.apply("and", result, operand)
        return result

    def disjunction(self, operands: Iterable[int]) -> int:
        result = 0
        for operand in operands:
            result = self.apply("or", result, operand)
        return result

    def evaluate(self, root: int, enabled: set[Hashable]) -> bool:
        index = root
        while index > 1:
            rank, low, high = self.nodes[index]  # type: ignore[misc]
            index = high if self.order[rank] in enabled else low
        return bool(index)

    def reachable_count(self, root: int) -> int:
        seen: set[int] = set()
        stack = [root]
        while stack:
            index = stack.pop()
            if index in seen:
                continue
            seen.add(index)
            if index > 1:
                _, low, high = self.nodes[index]  # type: ignore[misc]
                stack.extend((low, high))
        return len(seen)


def compile_explicit(
    rules: Sequence[Rule], base_labels: Mapping[Hashable, Hashable]
) -> dict[Hashable, Family]:
    propositions = set(base_labels)
    propositions.update(rule.head for rule in rules)
    propositions.update(item for rule in rules for item in rule.body)
    values = {proposition: frozenset() for proposition in propositions}
    for proposition, label in base_labels.items():
        values[proposition] = frozenset((frozenset((label,)),))
    changed = True
    while changed:
        changed = False
        for rule in rules:
            candidate: Family = frozenset((frozenset(),))
            for premise in rule.body:
                candidate = family_and(candidate, values[premise])
            updated = family_or(values[rule.head], candidate)
            if updated != values[rule.head]:
                values[rule.head] = updated
                changed = True
    return values


def compile_circuit_acyclic(
    rules: Sequence[Rule],
    base_labels: Mapping[Hashable, Hashable],
    topological_heads: Sequence[Hashable],
):
    heads = set(rule.head for rule in rules)
    if len(set(topological_heads)) != len(topological_heads) or not heads.issubset(topological_heads):
        raise ValueError("topological_heads must include every rule head exactly once")
    positions = {head: index for index, head in enumerate(topological_heads)}
    for rule in rules:
        for premise in rule.body:
            if premise in heads and positions[premise] >= positions[rule.head]:
                raise ValueError("rule graph is cyclic or topological order is invalid")
            if premise not in heads and premise not in base_labels:
                raise ValueError("rule premise has no base label or deriving rule")
    circuit = MonotoneCircuit()
    values = {
        proposition: circuit.variable(label)
        for proposition, label in base_labels.items()
    }
    by_head: dict[Hashable, list[Rule]] = {}
    for rule in rules:
        by_head.setdefault(rule.head, []).append(rule)
    for head in topological_heads:
        alternatives = [
            circuit.conjunction(values[premise] for premise in rule.body)
            for rule in by_head.get(head, ())
        ]
        if head in values:
            alternatives.append(values[head])
        values[head] = circuit.disjunction(alternatives)
    return circuit, values


def compile_bdd_fixed_point(
    rules: Sequence[Rule],
    base_labels: Mapping[Hashable, Hashable],
    variable_order: Sequence[Hashable],
):
    bdd = BDD(variable_order)
    propositions = set(base_labels)
    propositions.update(rule.head for rule in rules)
    propositions.update(item for rule in rules for item in rule.body)
    values = {proposition: 0 for proposition in propositions}
    for proposition, label in base_labels.items():
        values[proposition] = bdd.variable(label)
    iterations = 0
    changed = True
    while changed:
        iterations += 1
        changed = False
        for rule in rules:
            candidate = bdd.conjunction(values[premise] for premise in rule.body)
            updated = bdd.apply("or", values[rule.head], candidate)
            if updated != values[rule.head]:
                values[rule.head] = updated
                changed = True
    return bdd, values, iterations


def independent_choice_program(pair_count: int):
    base_labels: dict[str, str] = {}
    rules: list[Rule] = []
    pair_heads: list[str] = []
    topological_heads: list[str] = []
    for index in range(pair_count):
        left = f"a{index}"
        right = f"b{index}"
        pair = f"pair{index}"
        base_labels[left] = left
        base_labels[right] = right
        rules.extend((Rule(pair, (left,)), Rule(pair, (right,))))
        pair_heads.append(pair)
        topological_heads.append(pair)
    rules.append(Rule("goal", tuple(pair_heads)))
    topological_heads.append("goal")
    return rules, base_labels, topological_heads

