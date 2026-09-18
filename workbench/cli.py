import argparse
import json
from pathlib import Path
from zipfile import BadZipFile
from .benchmark import new_run, run_benchmark
from .contracts import DependencyProblem
from .methods import mechanism_receipt
from .problems import evidence_demo
from .report import analyze_problem, write_report, write_benchmark_report
from .workbooks import open_workbooks, _analyze_loaded, LineageUnavailable
from .content import compare_content
from .content_report import write_content_report


def save_analysis(problem, directory=None):
    result = analyze_problem(problem)
    result['mechanism_receipt'] = mechanism_receipt()
    if directory is None:
        folder = new_run('analysis')
    else:
        folder = Path(directory)
        if folder.exists() and any(folder.iterdir()):
            raise ValueError('Output folder must be new or empty; existing reports are preserved')
        folder.mkdir(parents=True, exist_ok=True)
    (folder / 'problem.json').write_text(json.dumps(problem.to_dict(), indent=2, ensure_ascii=False) + '\n')
    (folder / 'analysis.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    write_report(result, folder / 'index.html')
    return folder / 'index.html'


def save_workbook_analysis(paths, directory=None, same_layout=False):
    with open_workbooks(paths, preserve_order=same_layout) as (paths, books):
        content = compare_content(paths, books, same_layout=same_layout)
        try:
            problem = _analyze_loaded(paths, books)
            # The interactive lineage viewer has a smaller source budget than
            # the bounded content comparison. Keep the useful diff when a
            # large workbook cannot be rendered as one source checklist.
            if len(problem.sources) > 4000:
                content['lineage_view_available'] = False
                content['lineage_unavailable_reason'] = (
                    'Interactive lineage view limit: 4,000 source cells; '
                    'bounded formula impact tracing remains available.')
            else:
                content['lineage_view_available'] = True
        except (LineageUnavailable, ValueError) as error:
            problem = None
            content['lineage_view_available'] = False
            content['lineage_unavailable_reason'] = str(error)
    folder = Path(directory) if directory is not None else new_run('workbooks')
    if folder.exists() and any(folder.iterdir()):
        raise ValueError('Output folder must be new or empty; existing reports are preserved')
    folder.mkdir(parents=True, exist_ok=True)
    content['lineage_available'] = problem is not None
    if problem is not None:
        # Keep observed similarities separate from the actual formula graph.
        if content.get('lineage_view_available', True):
            try:
                report = save_analysis(problem, folder)
            except ValueError as error:
                content['lineage_view_available'] = False
                content['lineage_unavailable_reason'] = str(error)
            else:
                report.rename(folder / 'lineage.html')
        dependents = {}
        for head, body in problem.rules:
            for node in body:
                dependents.setdefault(node, set()).add(head)
        formula_targets = set(problem.targets)
        def impacts(nodes):
            seen = set(nodes)
            pending = list(nodes)
            while pending:
                for node in dependents.get(pending.pop(), ()):
                    if node not in seen:
                        seen.add(node)
                        pending.append(node)
            return sorted(seen & formula_targets)
        for block in content['blocks']:
            matched = set()
            different = set()
            uncompared = set()
            for side in ('left', 'right'):
                loc = block[side]
                prefix = loc['workbook']+'::' if len(paths)>1 else ''
                for cell in block['cells']:
                    node = prefix+loc['sheet']+'!'+cell[side]
                    if cell['equal']:
                        matched.add(node)
                    elif same_layout:
                        if cell['comparison'] == 'uncompared': uncompared.add(node)
                        elif cell['comparison'] != 'same_formula': different.add(node)
                    else:
                        different.add(node)
            block['formula_targets'] = impacts(matched)
            block['difference_formula_targets'] = impacts(different)
            if same_layout:
                block['uncompared_formula_targets'] = impacts(uncompared)
    (folder / 'content.json').write_text(json.dumps(content, indent=2, ensure_ascii=False)+'\n')
    write_content_report(content, folder / 'index.html')
    return folder / 'index.html'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lab problem workbench: measured mechanisms and source dependency pilot')
    sub = parser.add_subparsers(dest='command', required=True)
    bench = sub.add_parser('benchmark'); bench.add_argument('--repeats', type=int, default=3)
    demo = sub.add_parser('demo'); demo.add_argument('--output')
    analyze = sub.add_parser('analyze'); analyze.add_argument('workbooks', nargs='+', help='Workbook files or folders of .xlsx/.xlsm files'); analyze.add_argument('--output'); analyze.add_argument('--same-layout', action='store_true', help='Compare exactly two workbooks cell-by-cell at identical sheet names and coordinates')
    inspect = sub.add_parser('inspect'); inspect.add_argument('problem_json'); inspect.add_argument('--output')
    workspace = sub.add_parser('workspace', help='Persistent local evidence-version workspace')
    workspace_sub = workspace.add_subparsers(dest='workspace_command', required=True)
    workspace_create = workspace_sub.add_parser('create'); workspace_create.add_argument('path'); workspace_create.add_argument('--name')
    workspace_import = workspace_sub.add_parser('import'); workspace_import.add_argument('path'); workspace_import.add_argument('folder')
    workspace_confirm = workspace_sub.add_parser('confirm'); workspace_confirm.add_argument('path'); workspace_confirm.add_argument('candidate_id'); workspace_confirm.add_argument('--before', required=True); workspace_confirm.add_argument('--artifact-name'); workspace_confirm.add_argument('--artifact-id'); workspace_confirm.add_argument('--override-no-match', action='store_true')
    workspace_reject = workspace_sub.add_parser('reject'); workspace_reject.add_argument('path'); workspace_reject.add_argument('candidate_id')
    workspace_report = workspace_sub.add_parser('report'); workspace_report.add_argument('path'); workspace_report.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'workspace':
            from .evidence_workspace import (create_workspace, import_folder, confirm_candidate,
                                             reject_candidate, workspace_state)
            from .workspace_report import write_workspace_report
            if args.workspace_command == 'create': result = create_workspace(args.path, args.name)
            elif args.workspace_command == 'import': result = import_folder(args.path, args.folder)
            elif args.workspace_command == 'confirm':
                result = confirm_candidate(args.path, args.candidate_id, args.before,
                                           args.artifact_name, args.artifact_id,
                                           args.override_no_match)
            elif args.workspace_command == 'reject': result = reject_candidate(args.path, args.candidate_id)
            elif args.json:
                print(json.dumps(workspace_state(args.path), indent=2, ensure_ascii=False))
                return 0
            else:
                result = {'report': str(write_workspace_report(args.path))}
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        if args.command == 'benchmark':
            folder, report = run_benchmark(args.repeats)
            write_benchmark_report(report, folder / 'index.html')
            print(folder / 'index.html')
            return int(report['status'] != 'PASS')
        if args.command == 'demo': problem = evidence_demo()
        elif args.command == 'analyze':
            if args.same_layout and (len(args.workbooks) != 2 or any(Path(p).is_dir() for p in args.workbooks)):
                raise ValueError('--same-layout requires two explicit files in before/after order')
            paths = []
            for item in args.workbooks:
                path = Path(item)
                if path.is_dir():
                    paths.extend(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in ('.xlsx','.xlsm') and not p.name.startswith('~$'))
                else: paths.append(path)
            print(save_workbook_analysis(paths, args.output, same_layout=args.same_layout))
            return 0
        else: problem = DependencyProblem.from_dict(json.loads(Path(args.problem_json).read_text()))
        print(save_analysis(problem, args.output))
        return 0
    except (ValueError, OSError, KeyError, BadZipFile) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
