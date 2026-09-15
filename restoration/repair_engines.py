from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]/'LAC_REPRO_R210'
changes=[]
def repair(name,transform):
 canonical=next(p for p in ROOT.rglob(name+'.py') if 'parent_products' in str(p)) if name not in ('symbolic_favorable','spec_runtime') else next(ROOT.rglob(name+'.py'))
 old=canonical.read_bytes();text=old.decode();new=transform(text).encode()
 if new==old:raise RuntimeError('No change '+name)
 for p in ROOT.rglob(name+'.py'):
  if p.read_bytes()==old:
   p.write_bytes(new);changes.append({'path':str(p.relative_to(ROOT)),'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(new).hexdigest(),'repair':name})
def sacps(s):
 s=s.replace('holdout_returns: Sequence[Sequence[float]] | None = None,','holdout_returns: Sequence[Sequence[float]] | None = None,\n    validation_returns: Sequence[Sequence[float]] | None = None,')
 s=s.replace('"""Estimate a supported covariance and expose its downstream minimum-variance decision."""','"""Fit on training data, optionally tune on validation, evaluate only on holdout.\n\n    With no validation, choose the smallest numerically admissible shrinkage.\n    The legacy gaussian_validation_scores field then contains the shrinkage\n    selection objective, not held-out Gaussian scores.\n    """')
 s=s.replace('if not grid or min(grid) < 0 or max(grid) > 1 or eigenvalue_floor <= 0 or maximum_condition_number <= 1:', 'if not grid or not np.all(np.isfinite(grid)) or min(grid) < 0 or max(grid) > 1 or not np.isfinite(eigenvalue_floor) or not np.isfinite(maximum_condition_number) or eigenvalue_floor <= 0 or maximum_condition_number <= 1:')
 insert='''    validation = None if validation_returns is None else np.asarray(validation_returns, dtype=float)
    if validation is not None and (validation.ndim != 2 or validation.shape[0] < 2 or validation.shape[1] != p or not np.all(np.isfinite(validation))):
        raise ValueError("validation_returns must be finite and have the same variables")
    if validation is not None and holdout is not None and (np.shares_memory(validation, holdout) or np.array_equal(validation, holdout)):
        raise ValueError("validation and holdout must be separate data, not the same matrix")
'''
 s=s.replace('    mean = train.mean(axis=0)',insert+'\n    mean = train.mean(axis=0)')
 s=s.replace('        if holdout is not None:\n            validation_centered = holdout - mean','        if validation is not None:\n            validation_centered = validation - mean')
 return s
repair('sacps',sacps)
def rel(s):
 s=s.replace('        if not 0 < self.alteration_prior < 1:', '        if not self.name or not self.party or not math.isfinite(self.value):\n            raise ValueError("record name, party and finite value are required")\n        if not 0 < self.alteration_prior < 1:')
 s=s.replace('    tolerance: float = 0.0\n','    tolerance: float = 0.0\n\n    def __post_init__(self):\n        if not self.name or not math.isfinite(self.tolerance) or self.tolerance < 0:\n            raise ValueError("relation name and finite non-negative tolerance are required")\n')
 s=s.replace('        pattern: dict[str, bool] = {}','        if len({r.name for r in relations}) != len(relations):\n            raise ValueError("Relation names must be unique")\n        pattern: dict[str, bool] = {}')
 s=s.replace('        if max_colluding_records < 1:', '        if not records:\n            raise ValueError("At least one evidence record is required")\n        if not isinstance(max_colluding_records, int) or max_colluding_records < 1:')
 return s
repair('rel',rel)
def csid(s):
 s=s.replace('from itertools import combinations','from itertools import combinations\nimport math')
 s=s.replace('if self.consequence < 0:', 'if not math.isfinite(self.consequence) or self.consequence < 0:')
 s=s.replace('if self.cost < 0:', 'if not math.isfinite(self.cost) or self.cost < 0:')
 s=s.replace('if any(value < 0 or value > 1 for value in self.coverage.values()):','if any(not math.isfinite(value) or value < 0 or value > 1 for value in self.coverage.values()):')
 s=s.replace('        failure_names = {failure.name for failure in self.failures}','        failure_names = {failure.name for failure in self.failures}\n        if len(failure_names) != len(self.failures) or any(not n for n in failure_names):\n            raise ValueError("Failure names must be nonempty and unique")\n        if len({s.name for s in self.safeguards}) != len(self.safeguards) or any(not s.name for s in self.safeguards):\n            raise ValueError("Safeguard names must be nonempty and unique")')
 s=s.replace('        if budget < 0:', '        if not math.isfinite(budget) or budget < 0:')
 return s
repair('csid',csid)
def aicc(s):
 s=s.replace('    cost: float = 0.0\n','''    cost: float = 0.0

    def __post_init__(self):
        h = np.asarray(self.measurement_vector, dtype=float)
        if h.ndim != 1 or not h.size or not np.all(np.isfinite(h)):
            raise ValueError("measurement_vector must be a finite state vector")
        if not self.name or not np.isfinite(self.noise_variance) or self.noise_variance < 0 or not np.isfinite(self.cost) or self.cost < 0:
            raise ValueError("channel name, non-negative finite noise and cost are required")
''')
 s=s.replace('        self.nodes, self.weights = hermgauss(quadrature_points)','''        if self.mean.ndim != 1 or not self.mean.size or not np.all(np.isfinite(self.mean)):
            raise ValueError("belief mean must be a finite state vector")
        d = self.mean.size
        if self.covariance.shape != (d, d) or not np.all(np.isfinite(self.covariance)) or not np.allclose(self.covariance, self.covariance.T):
            raise ValueError("belief covariance must be finite and symmetric")
        if np.linalg.eigvalsh(self.covariance).min() < -1e-12:
            raise ValueError("belief covariance must be positive semidefinite")
        if self.action_slopes.ndim != 2 or not self.action_slopes.shape[0] or self.action_intercepts.shape != (self.action_slopes.shape[0],) or not np.all(np.isfinite(self.action_slopes)) or not np.all(np.isfinite(self.action_intercepts)):
            raise ValueError("finite action slopes and matching intercepts are required")
        if len({c.name for c in self.channels}) != len(self.channels):
            raise ValueError("channel names must be unique")
        if any(np.asarray(c.measurement_vector).shape != (d,) for c in self.channels):
            raise ValueError("channel and state dimensions differ")
        if not isinstance(quadrature_points, int) or quadrature_points < 2:
            raise ValueError("quadrature_points must be an integer at least two")
        self.nodes, self.weights = hermgauss(quadrature_points)''')
 s=s.replace('        h = np.asarray(channel.measurement_vector, dtype=float)','        h = np.asarray(channel.measurement_vector, dtype=float)\n        if h.shape != self.mean.shape:\n            raise ValueError("channel and state dimensions differ")')
 s=s.replace('        gain = self.covariance @ h / predictive_variance','''        if not np.isfinite(observation):
            raise ValueError("observation must be finite")
        if predictive_variance <= 0:
            if not np.isclose(observation, float(h @ self.mean), rtol=0, atol=1e-12):
                raise ValueError("observation contradicts a deterministic zero-variance belief")
            return
        gain = self.covariance @ h / predictive_variance''')
 return s
repair('aicc',aicc)
def hfad(s):
 s=s.replace('        edge_count = self.boundary_1.shape[1]', '        if self.boundary_1.ndim != 2 or not np.all(np.isfinite(self.boundary_1)):\n            raise ValueError("node-edge incidence must be a finite matrix")\n        edge_count = self.boundary_1.shape[1]')
 s=s.replace('if self.boundary_1.ndim != 2 or self.boundary_2.ndim != 2:','if self.boundary_2.ndim != 2 or not np.all(np.isfinite(self.boundary_2)):')
 s=s.replace('if flow.shape != (self.boundary_1.shape[1],):','if flow.shape != (self.boundary_1.shape[1],) or not np.all(np.isfinite(flow)):')
 s=s.replace('float(np.max(np.abs(reconstructed - flow)))','float(np.max(np.abs(reconstructed - flow))) if flow.size else 0.0')
 s=s.replace('    incidence = np.zeros((node_count, len(oriented_edges)))','    if not isinstance(node_count, int) or node_count < 0:\n        raise ValueError("node_count must be a non-negative integer")\n    incidence = np.zeros((node_count, len(oriented_edges)))')
 s=s.replace('        incidence[source, edge_index] = -1.0\n        incidence[target, edge_index] = 1.0','        if not isinstance(source, (int, np.integer)) or not isinstance(target, (int, np.integer)) or not 0 <= source < node_count or not 0 <= target < node_count:\n            raise ValueError("edge endpoint outside node range")\n        incidence[source, edge_index] -= 1.0\n        incidence[target, edge_index] += 1.0')
 return s
repair('hfad',hfad)
def maslov(s):
 start=s.index('        @lru_cache(maxsize=None)',s.index('class MonotoneCircuit'))
 end=s.index('\n    def reachable_count',start)
 s=s[:start]+'''        if not isinstance(root, int) or not 0 <= root < len(self.nodes):
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
''' +s[end:]
 s=s.replace('    circuit = MonotoneCircuit()\n    values = {','''    heads = set(rule.head for rule in rules)
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
    values = {''')
 return s
repair('symbolic_favorable',maslov)
Path(__file__).with_name('engine-changes.json').write_text(json.dumps(changes,indent=2))
print(len(changes),'source copies repaired')
