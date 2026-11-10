import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dockercheck.cli import main
from dockercheck.engine import analyze
from dockercheck.fixer import apply_fix, masked_preview, uppercase_keywords
from dockercheck.models import Finding, Report
from dockercheck.parser import ParseError, parse
from dockercheck.reporters import json_report, sarif_report, text_report


class PreparedRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.context = Path(self.temp.name)
        self.path = self.context / "Dockerfile"

    def tearDown(self):
        self.temp.cleanup()

    def codes(self, source, **kwargs):
        return {f.rule for f in analyze(source, context=self.context, **kwargs).findings}

    def cli(self, source, *args):
        self.path.write_bytes(source.encode("utf-8"))
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([str(self.path), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_001(self):
        self.assertIn('DF001', self.codes('FROM docker.io/library/ubuntu\n'))

    def test_002(self):
        self.assertIn('DF002', self.codes('FROM ubuntu:LATEST\n'))

    def test_003(self):
        self.assertIn('DF003', self.codes('FROM registry.local:5000/team/app:2.1\n'))

    def test_004(self):
        self.assertIn('DF004', self.codes('FROM $BUILD_IMAGE\n'))

    def test_005(self):
        self.assertIn('DF005', self.codes('FROM scratch\nCOPY app /app\n'))

    def test_006(self):
        self.assertIn('DF006', self.codes('FROM app:1\nUSER 000:1000\n'))

    def test_007(self):
        self.assertIn('DF007', self.codes('FROM app:1\nENV DATABASE_PASSWORD_FILE=/run/password\n'))

    def test_008(self):
        self.assertIn('DF008', self.codes('FROM app:1\nCOPY --chown=1000:1000 keys/id_ed25519 /keys/\n'))

    def test_009(self):
        self.assertIn('DF009', self.codes('FROM app:1\nADD git://example.test/repo /src\n'))

    def test_010(self):
        self.assertIn('DF010', self.codes('FROM app:1\nRUN wget -qO- https://example.test/install | bash\n'))

    def test_011(self):
        self.assertIn('DF011', self.codes('FROM app:1\nRUN /usr/bin/curl -fsSk https://example.test\n'))

    def test_012(self):
        self.assertIn('DF012', self.codes('FROM app:1\nRUN sh -c "apt-get update"\n'))

    def test_013(self):
        self.assertIn('DF013', self.codes('FROM app:1\nRUN apt-get install --yes ca-certificates\n'))

    def test_014(self):
        self.assertIn('DF014', self.codes('FROM app:1\nRUN apt-get install --no-install-recommends -y curl && echo done\n'))

