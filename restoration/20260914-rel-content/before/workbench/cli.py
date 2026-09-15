import argparse
import json
from pathlib import Path
from zipfile import BadZipFile
from .benchmark import new_run, run_benchmark
from .contracts import DependencyProblem
from .methods import mechanism_receipt
from .problems import evidence_demo
from .report import analyze_problem, write_report, write_benchmark_report
from .workbooks import analyze_workbooks


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


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lab problem workbench: measured mechanisms and source dependency pilot')
    sub = parser.add_subparsers(dest='command', required=True)
    bench = sub.add_parser('benchmark'); bench.add_argument('--repeats', type=int, default=3)
    demo = sub.add_parser('demo'); demo.add_argument('--output')
    analyze = sub.add_parser('analyze'); analyze.add_argument('workbooks', nargs='+', help='Workbook files or folders of .xlsx/.xlsm files'); analyze.add_argument('--output')
    inspect = sub.add_parser('inspect'); inspect.add_argument('problem_json'); inspect.add_argument('--output')
    args = parser.parse_args(argv)
    try:
        if args.command == 'benchmark':
            folder, report = run_benchmark(args.repeats)
            write_benchmark_report(report, folder / 'index.html')
            print(folder / 'index.html')
            return int(report['status'] != 'PASS')
        if args.command == 'demo': problem = evidence_demo()
        elif args.command == 'analyze':
            paths = []
            for item in args.workbooks:
                path = Path(item)
                if path.is_dir():
                    paths.extend(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in ('.xlsx','.xlsm') and not p.name.startswith('~$'))
                else: paths.append(path)
            problem = analyze_workbooks(paths)
        else: problem = DependencyProblem.from_dict(json.loads(Path(args.problem_json).read_text()))
        print(save_analysis(problem, args.output))
        return 0
    except (ValueError, OSError, KeyError, BadZipFile) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
