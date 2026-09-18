import json
import tempfile
from pathlib import Path
from openpyxl import Workbook
from workbench.cli import save_workbook_analysis

with tempfile.TemporaryDirectory(dir='/var/folders/87/7zcwj9x95fq3g0bv00f1t_gh0000gn/T/opencode') as td:
    root = Path(td)
    for mode in ('literal', 'formula'):
        paths = []
        for side in ('left', 'right'):
            book = Workbook()
            sheet = book.active
            for r in range(1, 6):
                for c in range(1, 6):
                    sheet.cell(r, c, 1000*c+17*r)
            sheet['C3'] = (999999 if side == 'right' else 3051) if mode == 'literal' else ('=Z1+1' if side == 'right' else '=Z1')
            sheet['Z1'] = 3051
            sheet['G1'] = '=C3*2'
            path = root / f'{mode}_{side}.xlsx'
            book.save(path)
            paths.append(path)
        report = save_workbook_analysis(paths, root / f'{mode}_report')
        content = json.loads(report.with_name('content.json').read_text())
        analysis = json.loads(report.with_name('analysis.json').read_text())
        block = next(b for b in content['blocks'] if b['left']['range'] == 'A1:E5')
        expected = [f'{mode}_{s}.xlsx::Sheet!G1' for s in ('left', 'right')]
        print(json.dumps({'probe': mode, 'kind': block['kind'], 'differences': [c for c in block['cells'] if not c['equal']], 'actual': block['difference_formula_targets'], 'expected': expected, 'source_impacts': analysis['source_impacts'], 'rules': analysis['problem']['rules']}))
