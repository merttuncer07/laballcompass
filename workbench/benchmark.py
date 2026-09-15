"""Independent scoring and paired, end-to-end timing on the same task inputs."""
import csv
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
import uuid
from .methods import METHODS, load_r207, mechanism_receipt
from .problems import suite, failure_scenarios, reference_truth

BASE = Path(__file__).resolve().parents[1]


def new_run(kind):
    name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    folder = BASE / 'workbench_runs' / (name + '-' + kind)
    folder.mkdir(parents=True)
    return folder


def run_benchmark(repeats=3):
    if not 1 <= repeats <= 10:
        raise ValueError('Timing repetitions must be between 1 and 10')
    folder = new_run('benchmark')
    report = {'schema_version': 1, 'status': 'RUNNING', 'problem_suite': 'dependency-v1',
              'started_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Synthetic engineering fixtures. Timing repeats are not independent statistical evidence. No audit field or novelty validation.',
              'semantics': 'Source availability in declared acyclic AND/OR support rules; not probabilities.',
              'timing': 'Median of paired repetitions of construction plus all queries. Python and R207 import warmed once; input parsing and oracle computation excluded for every method.',
              'environment': {'python': sys.version, 'platform': platform.platform()},
              'mechanism': mechanism_receipt(include_scalar=True), 'cases': []}
    load_r207()
    observations = []
    for problem in suite():
        scenarios = failure_scenarios(problem)
        expected = [reference_truth(problem, removed) for removed in scenarios]
        (folder / (problem.id + '.json')).write_text(json.dumps(problem.to_dict(), indent=2))
        case = {'id': problem.id, 'family': problem.metadata.get('family', problem.id),
                'input_sha256': problem.digest(), 'sources': len(problem.sources),
                'rules': len(problem.rules), 'queries': len(scenarios),
                'target_checks': len(scenarios) * len(problem.targets), 'methods': {}}
        for name, method in METHODS.items():
            timings = []
            for _ in range(repeats):
                start = time.perf_counter_ns()
                solver = method(problem)
                actual = solver.solve(scenarios)
                timings.append((time.perf_counter_ns() - start) / 1e6)
                if len(actual) != len(expected): raise RuntimeError(name + ': missing query output')
            fp = fn = 0
            for i, (observed, wanted) in enumerate(zip(actual, expected)):
                for target in problem.targets:
                    prediction = observed[target]
                    if type(prediction) is not bool: raise RuntimeError('Boolean predictions required')
                    fp += int(prediction and not wanted[target])
                    fn += int(not prediction and wanted[target])
                    observations.append([problem.id, name, i, '|'.join(sorted(scenarios[i])), target, wanted[target], prediction])
            stats = {'false_supported': fp, 'false_unsupported': fn,
                     'correct': case['target_checks'] - fp - fn,
                     'total_ms_median': statistics.median(timings), 'timing_repeats_ms': timings}
            if hasattr(solver, 'circuit'): stats['compiled_nodes'] = len(solver.circuit.nodes)
            case['methods'][name] = stats
        report['cases'].append(case)
        print(problem.id + ': ' + ('PASS' if all(m['false_supported'] + m['false_unsupported'] == 0 for m in case['methods'].values()) else 'FAIL'), flush=True)
    report['summary'] = {}
    for name in METHODS:
        rows = [c['methods'][name] for c in report['cases']]
        report['summary'][name] = {'correct': sum(r['correct'] for r in rows),
                                   'errors': sum(r['false_supported'] + r['false_unsupported'] for r in rows),
                                   'sum_case_median_ms': sum(r['total_ms_median'] for r in rows)}
    report['status'] = 'PASS' if all(r['errors'] == 0 for r in report['summary'].values()) else 'FAIL'
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['source_hashes'] = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((BASE / 'workbench').rglob('*.py'))}
    with (folder / 'predictions.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['case', 'method', 'scenario', 'removed_sources', 'target', 'reference_supported', 'predicted_supported'])
        writer.writerows(observations)
    (folder / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    return folder, report
