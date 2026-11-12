import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dockercheck.cli import main
from dockercheck.fixer import apply_fix, uppercase_keywords
from dockercheck.reporters import sarif_report
from dockercheck.engine import analyze

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / '.test-tmp'
TEMP.mkdir(exist_ok=True)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=TEMP)
        self.root = Path(self.directory.name)
        self.path = self.root/'Dockerfile'
        self.path.write_text('FROM alpine:3.21\nUSER 10001\nCMD ["true"]\n', encoding='utf-8')

    def tearDown(self):
        self.directory.cleanup()

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_json_and_thresholds(self):
        code, output, _ = self.run_cli(str(self.path), '--format', 'json')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)['summary']['error'], 0)
        self.assertEqual(self.run_cli(str(self.path), '--fail-on', 'info')[0], 1)
        self.path.write_text('FROM alpine\nUSER root\n', encoding='utf-8')
        self.assertEqual(self.run_cli(str(self.path), '--fail-on', 'error')[0], 1)
        self.assertEqual(self.run_cli(str(self.path), '--fail-on', 'none')[0], 0)

    def test_parse_error_fails_even_with_none(self):
        self.path.write_text('INVALID syntax', encoding='utf-8')
        self.assertEqual(self.run_cli(str(self.path), '--fail-on', 'none')[0], 1)

    def test_output_and_recursive_discovery(self):
        (self.root/'Dockerfile.bad').write_text('FROM app:latest\n', encoding='utf-8')
        (self.root/'Dockerfile.bak').write_text('INVALID ignored', encoding='utf-8')
        report = self.root/'results.json'
        code, stdout, _ = self.run_cli(str(self.root), '--format', 'json', '--output', str(report))
        self.assertEqual(code, 1)
        self.assertEqual(stdout, '')
        self.assertEqual(len(json.loads(report.read_text(encoding='utf-8'))['files']), 2)

    def test_sarif_has_locations(self):
        output = sarif_report([analyze('FROM app:1\nUSER root\n', 'examples/Dockerfile')])
        self.assertEqual(output['version'], '2.1.0')
        root = next(r for r in output['runs'][0]['results'] if r['ruleId']=='DF006')
        self.assertEqual(root['locations'][0]['physicalLocation']['region']['startLine'], 2)

    def test_sarif_absolute_paths_are_file_uris(self):
        for path in ('C:\\My Project\\Dockerfile', '/tmp/My Project/Dockerfile'):
            with self.subTest(path=path):
                result = sarif_report([analyze('FROM app:1\n', path)])['runs'][0]['results'][0]
                uri = result['locations'][0]['physicalLocation']['artifactLocation']['uri']
                self.assertTrue(uri.startswith('file:///'))
                self.assertIn('My%20Project', uri)

    def test_fix_preserves_crlf_bom_and_heredoc_payload(self):
        raw = b'\xef\xbb\xbffrom alpine:3.21\r\nrun <<EOF\r\necho from text\r\nEOF\r\n'
        self.path.write_bytes(raw)
        source = raw.decode('utf-8-sig')
        self.assertEqual(apply_fix(self.path, source), [1, 2])
        self.assertEqual(self.path.with_name('Dockerfile.bak').read_bytes(), raw)
        fixed = self.path.read_bytes()
        self.assertTrue(fixed.startswith(b'\xef\xbb\xbfFROM'))
        self.assertIn(b'echo from text\r\n', fixed)
        self.assertEqual(fixed.count(b'\r\n'), 4)
        self.assertEqual(uppercase_keywords(fixed.decode('utf-8-sig'))[1], [])

    def test_existing_backup_blocks_fix(self):
        self.path.write_text('from app:1\n', encoding='utf-8')
        self.path.with_name('Dockerfile.bak').write_text('keep', encoding='utf-8')
        before = self.path.read_bytes()
        self.assertEqual(self.run_cli(str(self.path), '--fix')[0], 2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_dry_run_does_not_change_source(self):
        self.path.write_text('from app:1\n', encoding='utf-8')
        before = self.path.read_bytes()
        _, _, diff = self.run_cli(str(self.path), '--dry-run')
        self.assertIn('+FROM', diff)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.path.with_name('Dockerfile.bak').exists())

    def test_dry_run_does_not_print_secret_values(self):
        self.path.write_text('from app:1\nenv API_TOKEN=NEVER_PRINT_TOKEN\n', encoding='utf-8')
        _, stdout, stderr = self.run_cli(str(self.path), '--dry-run')
        self.assertNotIn('NEVER_PRINT_TOKEN', stdout + stderr)

    def test_overwriting_input_as_report_is_rejected(self):
        with self.assertRaises(SystemExit) as error:
            self.run_cli(str(self.path), '--output', str(self.path))
        self.assertEqual(error.exception.code, 2)

    def test_report_cannot_overwrite_backup_during_fix(self):
        before = b'from app:1\n'
        self.path.write_bytes(before)
        backup = self.path.with_name('Dockerfile.bak')
        with self.assertRaises(SystemExit) as error:
            self.run_cli(str(self.path), '--fix', '--output', str(backup))
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(backup.exists())

    def test_unknown_ignore_and_missing_paths(self):
        for args in ([str(self.path), '--ignore', 'DF999'], [str(self.root/'missing')]):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                self.run_cli(*args)

    def test_list_rules(self):
        code, output, _ = self.run_cli('--list-rules')
        self.assertEqual(code, 0)
        self.assertEqual(len(output.strip().splitlines()), 26)
