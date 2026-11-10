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

