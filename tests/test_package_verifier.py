import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from LAC_REPRO_R210 import verify_package


class PackageVerifierTests(unittest.TestCase):
    def make_package(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        payload = root / 'payload.txt'
        payload.write_text('payload')
        digest = verify_package.sha256(payload)
        manifest = root / '04_FILE_MANIFEST_SHA256.tsv'
        manifest.write_text(
            f'path\tsha256\tbytes\tcomponent\n'
            f'payload.txt\t{digest}\t{payload.stat().st_size}\ttest\n'
        )
        return temp, root, manifest

    def run_verifier(self, root, manifest):
        output = io.StringIO()
        with patch.object(verify_package, 'ROOT', root), \
             patch.object(verify_package, 'MANIFEST', manifest), \
             patch.object(verify_package, 'REQUIRED', ()), \
             contextlib.redirect_stdout(output):
            code = verify_package.main()
        return code, output.getvalue()

    def test_complete_manifest_passes(self):
        temp, root, manifest = self.make_package()
        try:
            code, output = self.run_verifier(root, manifest)
            self.assertEqual(code, 0)
            self.assertIn('PACKAGE VERIFY: PASS', output)
        finally:
            temp.cleanup()

    def test_unmanifested_file_fails(self):
        temp, root, manifest = self.make_package()
        try:
            (root / 'extra.txt').write_text('not sealed')
            code, output = self.run_verifier(root, manifest)
            self.assertEqual(code, 1)
            self.assertIn('unmanifested package file: extra.txt', output)
        finally:
            temp.cleanup()

    def test_unmanifested_forbidden_path_cannot_be_reported_absent(self):
        temp, root, manifest = self.make_package()
        try:
            retired = root / 'R179_FORBIDDEN' / 'file.txt'
            retired.parent.mkdir()
            retired.write_text('retired')
            code, output = self.run_verifier(root, manifest)
            self.assertEqual(code, 1)
            self.assertIn('retired/discarded path present: R179_FORBIDDEN', output)
        finally:
            temp.cleanup()


if __name__ == '__main__':
    unittest.main()
