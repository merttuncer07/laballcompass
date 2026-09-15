from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R388 = ROOT / '05_R388_NATIVE_ROUTING'
V2 = ROOT / '01_V2_CORE'
FOUNDRY = ROOT / '02_FOUNDRY_ALL_PRODUCTS'
LOG = R388 / 'R388_CANDIDATE_PACKAGED_REGRESSION.log'
STATUS = R388 / 'R388_CANDIDATE_PACKAGED_REGRESSION.status'
PROGRESS = R388 / 'R388_CANDIDATE_PACKAGED_REGRESSION.progress.json'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(label: str, cwd: Path, script: str) -> dict:
    completed = subprocess.run([sys.executable, script], cwd=cwd, text=True, capture_output=True)
    return {
        'label': label,
        'exit_code': completed.returncode,
        'stdout': completed.stdout.strip(),
        'stderr': completed.stderr.strip(),
    }


def persist_progress(runs: list[dict]) -> None:
    PROGRESS.write_text(json.dumps({
        'updated_at_utc': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'completed_runs': len(runs),
        'runs': runs,
    }, indent=2), encoding='utf-8')


def main() -> None:
    summary_path = FOUNDRY / 'regression_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    foundry_ok = (
        summary.get('parent_test_files') == 69
        and summary.get('product_test_files') == 145
        and summary.get('test_files_passed') == 214
        and summary.get('test_files_failed') == 0
        and summary.get('tests_counted') == 806
        and len(summary.get('results', [])) == 214
        and all(r.get('returncode') == 0 for r in summary.get('results', []))
    )
    foundry_receipt = {
        'label': 'foundry_806',
        'exit_code': 0 if foundry_ok else 1,
        'stdout': json.dumps({k: summary.get(k) for k in ('parent_test_files','product_test_files','test_files_passed','test_files_failed','tests_counted')}, sort_keys=True),
        'stderr': '' if foundry_ok else 'persisted foundry regression summary failed validation',
        'receipt_mode': 'PERSISTED_COMPONENT_RECEIPT_FROM_JUST_COMPLETED_PACKAGED_RUN',
        'receipt_path': str(summary_path.relative_to(ROOT)),
        'receipt_sha256': sha256(summary_path),
        'receipt_mtime_ns': summary_path.stat().st_mtime_ns,
    }
    runs = [foundry_receipt]
    persist_progress(runs)
    if not foundry_ok:
        report = {'status':'FAIL','receipt_rebuild':True,'runs':runs}
        LOG.write_text(json.dumps(report, indent=2), encoding='utf-8')
        STATUS.write_text('1\n', encoding='utf-8')
        raise SystemExit(1)

    core_runs = [
        ('core_v2', 'test_core_v2.py'),
        ('foundry_integration', 'test_core_v2_foundry_integration.py'),
        ('search_engine', 'test_lab_search_engine.py'),
        ('search_corpus', 'test_search_corpus_integration.py'),
        ('relevance_learning', 'test_relevance_learning.py'),
        ('experiment_selector', 'test_experiment_selector.py'),
        ('experiment_telemetry', 'test_experiment_telemetry.py'),
        ('experiment_integration', 'test_experiment_integration.py'),
        ('experiment_contract_bootstrap', 'test_experiment_contract_bootstrap.py'),
    ]
    for label, script in core_runs:
        runs.append(run(label, V2, script)); persist_progress(runs)

    product_test_files = sorted((V2 / 'products').glob('V2P*/test_*.py'))
    for test_path in product_test_files:
        product_dir = test_path.parent
        runs.append(run(f'v2_product::{product_dir.name}/{test_path.name}', product_dir, test_path.name)); persist_progress(runs)

    closure_runs = [
        ('r12_closure_updated', 'test_r12_closure.py'),
        ('r387_product_overlay_history', 'test_r387_product_overlay_closure.py'),
        ('r388_retro50_parent_integration_closure', 'test_r388_retro50_parent_integration_closure.py'),
    ]
    for label, script in closure_runs:
        runs.append(run(label, V2, script)); persist_progress(runs)

    report = {
        'status': 'PASS' if all(r['exit_code'] == 0 for r in runs) else 'FAIL',
        'receipt_rebuild': True,
        'why_rebuilt': 'The original packaged runner exited 0, but its aggregate JSON pathname was unlinked by a stale duplicate launcher. Foundry persisted its own complete component receipt; all other exact runner surfaces were rerun from the final tree.',
        'runner_source': '04_INTEGRITY/run_packaged_regression.py',
        'runner_source_sha256': sha256(ROOT / '04_INTEGRITY' / 'run_packaged_regression.py'),
        'auto_discovered_product_test_files': len(product_test_files),
        'auto_discovered_product_suite_dirs': len({p.parent.name for p in product_test_files}),
        'runs': runs,
    }
    LOG.write_text(json.dumps(report, indent=2), encoding='utf-8')
    STATUS.write_text(('0' if report['status'] == 'PASS' else '1') + '\n', encoding='utf-8')
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
