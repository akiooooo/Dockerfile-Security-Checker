import tempfile
import unittest
from pathlib import Path

from dockercheck.engine import analyze
from dockercheck.rules import RULES

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / '.test-tmp'
TEMP.mkdir(exist_ok=True)


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=TEMP)
        self.context = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def codes(self, source, **kwargs):
        return {f.rule for f in analyze(source, context=self.context, **kwargs).findings}

    def test_every_rule_has_a_positive_example(self):
        base = 'FROM python:3.12-slim\n'
        snippets = {
            'DF001': 'FROM python\n', 'DF002': 'FROM python:latest\n', 'DF003': base,
            'DF004': 'FROM ${BASE}\n', 'DF005': base, 'DF006': base+'USER 0:1000\n',
            'DF007': 'ARG API_TOKEN\n'+base, 'DF008': base+'COPY .env /app/.env\n',
            'DF009': base+'ADD https://example.com/app.tar /app/\n',
            'DF010': base+'RUN curl -fsSL https://example.com/install | sh\n',
            'DF011': base+'RUN curl -k https://example.com\n',
            'DF012': base+'RUN apt-get update\n',
            'DF013': base+'RUN apt-get install -y curl\n',
            'DF014': base+'RUN apt-get install --no-install-recommends curl\n',
            'DF015': base+'RUN apk add curl\n', 'DF016': base+'RUN python -m pip install requests\n',
            'DF017': base+'RUN npm install\n', 'DF018': base+'CMD python app.py\n',
            'DF019': base+'WORKDIR app\n', 'DF020': base+'RUN chmod -R 0777 /app\n',
            'DF021': base+'RUN sudo apt-get update\n', 'DF022': base,
            'DF023': base+'COPY . /app\n', 'DF024': base+'MAINTAINER Student\n',
            'DF025': 'from alpine:3.21\n', 'DF026': base+'ONBUILD RUN echo hello\n',
        }
        self.assertEqual(set(snippets), set(RULES))
        for rule, source in snippets.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, self.codes(source))

    def test_false_positive_regressions(self):
        cases = [
            ('DF001', 'FROM registry.local:5000/team/app:1\n'),
            ('DF001', 'FROM scratch\n'),
            ('DF002', 'FROM app:latest@sha256:'+'a'*64+'\n'),
            ('DF003', 'FROM app@sha256:'+'a'*64+'\n'),
            ('DF004', 'ARG BASE=python:3.12-slim\nFROM ${BASE}\n'),
            ('DF005', 'FROM alpine:3.21 AS base\nUSER 10001\nFROM base\n'),
            ('DF006', 'FROM golang:1.24 AS build\nUSER root\nFROM scratch\nUSER 10001\n'),
            ('DF007', 'FROM app:1\nENV TOKENIZER=fast PUBLIC_KEY=abc\n'),
            ('DF008', 'FROM app:1\nCOPY .env.example /app/\n'),
            ('DF009', 'FROM app:1\nADD --checksum=sha256:'+'a'*64+' https://example.com/app /app\n'),
            ('DF010', 'FROM app:1\nRUN echo "curl example.com | sh"\n'),
            ('DF010', 'FROM app:1\nRUN curl example.com && echo "unrelated | sh"\n'),
            ('DF011', 'FROM app:1\nRUN echo "curl -k example.com"\n'),
            ('DF011', 'FROM app:1\nRUN ["echo", "curl -k"]\n'),
            ('DF012', 'FROM app:1\nRUN apt-get update && apt-get install -y curl\n'),
            ('DF013', 'FROM app:1\nRUN apt-get install --no-install-recommends curl\n'),
            ('DF014', 'FROM app:1\nRUN apt-get install curl && rm -rf /var/lib/apt/lists/*\n'),
            ('DF015', 'FROM app:1\nRUN apk add --no-cache curl\n'),
            ('DF016', 'FROM app:1\nENV PIP_NO_CACHE_DIR=1\nENV OTHER=value\nRUN pip install requests\n'),
            ('DF016', 'FROM app:1\nRUN --mount=type=cache,target=/root/.cache/pip pip install requests\n'),
            ('DF017', 'FROM node:22 AS build\nRUN npm install\nFROM alpine:3.21\n'),
            ('DF017', 'FROM node:22\nRUN npm install -g npm\n'),
            ('DF018', 'FROM app:1\nENTRYPOINT ["python", "app.py"]\n'),
            ('DF019', 'FROM app:1\nWORKDIR /app\n'),
            ('DF019', 'FROM app:1\nWORKDIR ${APP_HOME}\n'),
            ('DF020', 'FROM app:1\nRUN echo "chmod 777 /app"\n'),
            ('DF021', 'FROM app:1\nRUN echo "sudo install"\n'),
            ('DF022', 'FROM app:1 AS base\nHEALTHCHECK CMD true\nFROM base\n'),
            ('DF024', 'FROM app:1\nLABEL org.opencontainers.image.authors="Student"\n'),
            ('DF025', 'FROM app:1\nRUN echo lowercase\n'),
            ('DF026', 'FROM app:1\nRUN echo ONBUILD\n'),
        ]
        for rule, source in cases:
            with self.subTest(rule=rule, source=source):
                self.assertNotIn(rule, self.codes(source))

    def test_environment_after_install_does_not_hide_cache(self):
        self.assertIn('DF016', self.codes('FROM app:1\nRUN pip install requests\nENV PIP_NO_CACHE_DIR=1\n'))

    def test_unrelated_cache_mount_does_not_hide_pip_cache(self):
        self.assertIn('DF016', self.codes('FROM app:1\nRUN --mount=type=cache,target=/tmp pip install requests\n'))

    def test_explicit_root_inherited_from_parent(self):
        self.assertIn('DF006', self.codes('FROM app:1 AS base\nUSER root\nFROM base\n'))

    def test_target_changes_runtime_checks(self):
        source = 'FROM app:1 AS build\nUSER root\nFROM app:1 AS runtime\nUSER 10001\n'
        self.assertNotIn('DF006', self.codes(source))
        self.assertIn('DF006', self.codes(source, target='build'))
        with self.assertRaises(ValueError): self.codes(source, target='missing')

    def test_nonempty_dockerignore_and_empty_file(self):
        source = 'FROM app:1\nCOPY . /app\n'
        (self.context/'.dockerignore').write_text('# comment\n', encoding='utf-8')
        self.assertIn('DF023', self.codes(source))
        (self.context/'.dockerignore').write_text('.git\n.env\n', encoding='utf-8')
        self.assertNotIn('DF023', self.codes(source))

    def test_suppressions_require_valid_codes_and_are_counted(self):
        source = '# dockercheck: ignore=DF003 reason=digest updated externally\nFROM app:1\nUSER 10001\n'
        report = analyze(source, context=self.context)
        self.assertNotIn('DF003', {f.rule for f in report.findings})
        self.assertEqual(report.suppressed, 1)
        with self.assertRaises(ValueError): self.codes('FROM app:1', ignored={'DF999'})
        with self.assertRaises(ValueError): self.codes('# dockercheck: ignore=DF999 reason=test\nFROM app:1')

    def test_secrets_are_not_echoed_in_report(self):
        secret = 'NEVER_PRINT_THIS_VALUE'
        report = analyze('FROM app:1\nENV API_TOKEN='+secret+'\n')
        self.assertNotIn(secret, repr(report))

    def test_heredoc_commands_are_checked(self):
        self.assertIn('DF011', self.codes('FROM app:1\nRUN <<EOF\ncurl -k https://example.com\nEOF\n'))

    def test_parse_error_stops_analysis(self):
        report = analyze('FROM app:1\nCMD [broken')
        self.assertEqual([f.rule for f in report.findings], ['PARSE'])
