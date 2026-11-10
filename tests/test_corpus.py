import json
import unittest
from pathlib import Path

from dockercheck.engine import analyze

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


class CorpusTests(unittest.TestCase):
    def test_expected_findings_for_every_example(self):
        manifest = json.loads((EXAMPLES/'manifest.json').read_text(encoding='utf-8'))
        actual_files = {p.relative_to(EXAMPLES).as_posix() for p in EXAMPLES.rglob('Dockerfile')}
        self.assertEqual(set(manifest), actual_files)
        for relative, expected in manifest.items():
            with self.subTest(file=relative):
                path = EXAMPLES/relative
                report = analyze(path.read_text(encoding='utf-8'), str(path))
                self.assertEqual(sorted({f.rule for f in report.findings}), sorted(expected))

    def test_good_examples_have_no_errors_or_warnings(self):
        for path in (EXAMPLES/'good').rglob('Dockerfile'):
            with self.subTest(file=path):
                report = analyze(path.read_text(encoding='utf-8'), str(path))
                self.assertFalse([f for f in report.findings if f.severity in ('error', 'warning')])
