"""File replacement must not relabel already parsed workbook data."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
from workbench.workbooks import open_workbooks, _analyze_loaded
from workbench.content import compare_content


class WorkbookSnapshotTests(unittest.TestCase):
    def test_lineage_and_content_hash_the_bytes_actually_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'unit.xlsx'
            book=Workbook();book.active['A1']=5;book.active['B1']='=A1';book.save(path);book.close()
            original_hash=hashlib.sha256(path.read_bytes()).hexdigest()
            with open_workbooks([path]) as (paths, books):
                path.write_bytes(b'file replaced after loading')
                lineage=_analyze_loaded(paths, books)
                content=compare_content(paths, books)
            self.assertEqual(lineage.metadata['input_files'][0]['sha256'], original_hash)
            self.assertEqual(content['input_files'][0]['sha256'], original_hash)
            self.assertEqual(lineage.sources, ('Sheet!A1',))

    def test_unsnapshotted_in_memory_content_is_not_given_a_disk_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'different-on-disk.xlsx';path.write_bytes(b'unrelated')
            book=Workbook();book.active['A1']=5
            result=compare_content([path], [book]);book.close()
            self.assertIsNone(result['input_files'][0]['sha256'])


if __name__=='__main__':unittest.main()
