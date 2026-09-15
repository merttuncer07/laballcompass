import unittest
import tempfile
from pathlib import Path
from openpyxl import Workbook
from workbench.content import compare_content


class RecordMatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def compare(self, paths, books):
        paths = [Path(self.tmp.name) / p.name for p in paths]
        for path, book in zip(paths, books):
            book.save(path)
        return compare_content(paths, books)

    def pair(self):
        a,b=Workbook(),Workbook()
        cols=[4,2,5,1,3]
        rows=[7,3,9,1,8,6,10,5,2,4]
        for r in range(1,11):
            for c in range(1,6):
                value=1000*c+17*r
                a.active.cell(r,c,value)
                b.active.cell(rows[r-1],cols[c-1],value)
        return [Path('one.xlsx'),Path('two.xlsx')],[a,b],rows,cols

    def test_reordered_rows_and_columns_locate_changed_value(self):
        paths,books,rows,cols=self.pair()
        books[1].active.cell(rows[3],cols[2],999999)
        result=self.compare(paths,books)
        match=next(b for b in result['blocks'] if b.get('kind')=='row_alignment')
        self.assertEqual(match['matching_rows'],10)
        self.assertEqual(match['matching_cells'],49)
        self.assertEqual(match['different_or_uncompared_cells'],1)
        self.assertEqual({(r['left'],r['right']) for r in match['row_mapping']},{(i+1,r) for i,r in enumerate(rows)})
        different=next(c for c in match['cells'] if not c['equal'])
        self.assertEqual((different['left'],different['right']),('C4','E1'))

    def test_ambiguous_identical_columns_are_not_arbitrarily_mapped(self):
        paths,books,rows,cols=self.pair()
        for book in books:
            for r in range(1,11):
                for c in range(1,6):book.active.cell(r,c,17*r)
        result=self.compare(paths,books)
        self.assertFalse(any(b.get('kind')=='row_alignment' for b in result['blocks']))

    def test_equal_column_bags_without_consistent_records_are_insufficient(self):
        a,b=Workbook(),Workbook()
        for r in range(12):
            for c in range(5):
                a.active.cell(r+1,c+1,1000*c+17*r)
                b.active.cell(r+1,c+1,1000*c+17*((r+c)%12))
        result=self.compare([Path('a.xlsx'),Path('b.xlsx')],[a,b])
        self.assertFalse(any(x.get('kind')=='row_alignment' for x in result['blocks']))

    def test_duplicate_rows_are_omitted_from_unique_correspondences(self):
        paths,books,rows,cols=self.pair()
        for c in range(1,6):
            books[0].active.cell(11,c,books[0].active.cell(1,c).value)
            books[1].active.cell(11,cols[c-1],books[0].active.cell(1,c).value)
        result=self.compare(paths,books)
        block=next(x for x in result['blocks'] if x.get('kind')=='row_alignment')
        self.assertFalse(any(x['left'] in (1,11) for x in block['row_mapping']))
        self.assertEqual(block['unmapped_left_rows'],[1,11])
        self.assertGreaterEqual(result['record_alignment']['ambiguous_rows_omitted'],2)

    def test_reordered_difference_keeps_both_formula_impacts_and_separate_roots(self):
        import json
        from workbench.cli import save_workbook_analysis
        paths,books,rows,cols=self.pair()
        books[1].active.cell(rows[3],cols[2],999999)
        books[0].active['G1']='=SUM(C1:C10)'
        books[1].active['G1']='=SUM(E1:E10)'
        paths=[Path(self.tmp.name)/p.name for p in paths]
        for path,book in zip(paths,books):book.save(path)
        report=save_workbook_analysis(paths,Path(self.tmp.name)/'report')
        content=json.loads(report.with_name('content.json').read_text())
        match=next(b for b in content['blocks'] if b.get('kind')=='row_alignment')
        self.assertEqual(match['difference_formula_targets'],['one.xlsx::Sheet!G1','two.xlsx::Sheet!G1'])
        problem=json.loads(report.with_name('problem.json').read_text())
        self.assertEqual(len(set(problem['bases'].values())),20)


if __name__=='__main__':unittest.main()
