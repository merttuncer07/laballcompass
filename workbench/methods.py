"""Adapters share the task contract, not their evaluation implementation."""
import hashlib
import importlib.util
from pathlib import Path
import sys
from .contracts import check_scenarios

LAB_SOURCE = Path(__file__).resolve().parents[1] / 'LAC_REPRO_R210/ACTIVE_RESEARCH/R207_MASLOV_SYMBOLIC_FAVORABLE_SETS/symbolic_favorable.py'


def load_r207():
    name = '_workbench_actual_r207'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, LAB_SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def mechanism_receipt(include_scalar=False):
    return {'id': 'R207', 'source': str(LAB_SOURCE.relative_to(LAB_SOURCE.parents[3])),
            'sha256': hashlib.sha256(LAB_SOURCE.read_bytes()).hexdigest(),
            'invoked_functions': ['Rule', 'compile_circuit_acyclic'] + (['MonotoneCircuit.evaluate'] if include_scalar else []),
            'extension': 'R207Batch evaluates the compiled circuit over integer bitsets; it is a new adapter, not historical R207 code.'}


class ForwardRules:
    """Strong baseline: topological AND/OR propagation with shared source identities."""
    id = 'and_or_forward'

    def __init__(self, problem):
        self.problem = problem
        self.order = problem.order()
        self.groups = {}
        for head, body in problem.rules:
            self.groups.setdefault(head, []).append(body)

    def solve(self, scenarios):
        check_scenarios(self.problem, scenarios)
        results = []
        for removed in scenarios:
            values = {p: s not in removed for p, s in self.problem.bases.items()}
            for head in self.order:
                if head not in values:
                    values[head] = any(all(values[p] for p in body) for body in self.groups[head])
            results.append({t: values[t] for t in self.problem.targets})
        return results


class R207Scalar:
    id = 'r207_scalar'

    def __init__(self, problem):
        self.problem = problem
        engine = load_r207()
        heads = {h for h, _ in problem.rules}
        self.circuit, self.roots = engine.compile_circuit_acyclic(
            [engine.Rule(h, b) for h, b in problem.rules], problem.bases,
            [h for h in problem.order() if h in heads])

    def solve(self, scenarios):
        check_scenarios(self.problem, scenarios)
        sources = set(self.problem.sources)
        return [{t: self.circuit.evaluate(self.roots[t], sources - set(removed))
                 for t in self.problem.targets} for removed in scenarios]


class ForwardBatch(ForwardRules):
    """Control for the batching technique, independently of R207 compilation."""
    id = 'and_or_bitset'

    def solve(self, scenarios):
        check_scenarios(self.problem, scenarios)
        full = (1 << len(scenarios)) - 1
        masks = dict.fromkeys(self.problem.sources, full)
        for i, removed in enumerate(scenarios):
            for source in removed: masks[source] &= ~(1 << i)
        values = {p: masks[source] for p, source in self.problem.bases.items()}
        for head in self.order:
            if head in values: continue
            alternatives = 0
            for body in self.groups[head]:
                conjunction = full
                for premise in body: conjunction &= values[premise]
                alternatives |= conjunction
            values[head] = alternatives
        return [{t: bool(values[t] & (1 << i)) for t in self.problem.targets} for i in range(len(scenarios))]


class R207Batch(R207Scalar):
    id = 'r207_bitset'

    def solve(self, scenarios):
        masks = self.solve_masks(scenarios)
        return [{t: bool(masks[t] & (1 << i)) for t in self.problem.targets}
                for i in range(len(scenarios))]

    def solve_masks(self, scenarios):
        """One integer per target; reports need not allocate a full Boolean matrix."""
        check_scenarios(self.problem, scenarios)
        full = (1 << len(scenarios)) - 1
        masks = dict.fromkeys(self.problem.sources, full)
        for i, removed in enumerate(scenarios):
            for source in removed:
                masks[source] &= ~(1 << i)
        values = []
        for op, payload in self.circuit.nodes:
            if op == 'false': value = 0
            elif op == 'true': value = full
            elif op == 'var': value = masks[payload]
            elif op == 'and':
                value = full
                for child in payload: value &= values[child]
            elif op == 'or':
                value = 0
                for child in payload: value |= values[child]
            else: raise ValueError('Unsupported R207 operation: ' + op)
            values.append(value)
        return {t: values[self.roots[t]] for t in self.problem.targets}


METHODS = {m.id: m for m in (ForwardRules, ForwardBatch, R207Scalar, R207Batch)}
