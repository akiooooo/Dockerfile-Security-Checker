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

    def test_015(self):
        self.assertIn('DF015', self.codes('FROM app:1\nRUN apk add --update ca-certificates\n'))

    def test_016(self):
        self.assertIn('DF016', self.codes('FROM app:1\nRUN python3 -m pip install flask\n'))

    def test_017(self):
        self.assertIn('DF017', self.codes('FROM node:22\nRUN npm install --omit=dev\n'))

    def test_018(self):
        self.assertIn('DF018', self.codes('FROM app:1\nENTRYPOINT exec /app/server\n'))

    def test_019(self):
        self.assertIn('DF019', self.codes('FROM app:1\nWORKDIR ./backend\n'))

    def test_020(self):
        self.assertIn('DF020', self.codes('FROM app:1\nRUN /bin/chmod -R 777 /srv/uploads\n'))

    def test_021(self):
        self.assertIn('DF021', self.codes('FROM app:1\nRUN sudo -u app echo hello\n'))

    def test_022(self):
        self.assertIn('DF022', self.codes('FROM app:1\nHEALTHCHECK NONE\n'))

    def test_023(self):
        self.assertIn('DF023', self.codes('FROM app:1\nCOPY ["./*", "/app/"]\n'))

    def test_024(self):
        self.assertIn('DF024', self.codes('FROM app:1\nMAINTAINER Developer <dev@example.test>\n'))

    def test_025(self):
        self.assertIn('DF025', self.codes('FROM app:1\ncOpY app.py /app/\n'))

    def test_026(self):
        self.assertIn('DF026', self.codes('FROM app:1\nONBUILD COPY . /child\n'))

    def test_027(self):
        self.assertNotIn('DF001', self.codes('FROM localhost:5000/team/backend:2\n'))

    def test_028(self):
        self.assertNotIn('DF002', self.codes('FROM team/latest:2\n'))

    def test_029(self):
        self.assertNotIn('DF003', self.codes('FROM team/backend:2@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'))

    def test_030(self):
        self.assertNotIn('DF004', self.codes('ARG IMAGE=alpine:3.21\nFROM $IMAGE\n'))

    def test_031(self):
        self.assertNotIn('DF005', self.codes('FROM app:1\nUSER 12345:12345\n'))

    def test_032(self):
        self.assertNotIn('DF006', self.codes('FROM app:1\nUSER root\nUSER application\n'))

    def test_033(self):
        self.assertNotIn('DF007', self.codes('FROM app:1\nENV DESCRIPTION API_TOKEN=example\n'))

    def test_034(self):
        self.assertNotIn('DF008', self.codes('FROM app:1\nCOPY config/.env.sample /app/\n'))

    def test_035(self):
        self.assertNotIn('DF009', self.codes('FROM app:1\nADD archive.tar.gz /app/\n'))

    def test_036(self):
        self.assertNotIn('DF010', self.codes('FROM app:1\nRUN curl https://example.test/file -o /tmp/file && sha256sum /tmp/file\n'))

    def test_037(self):
        self.assertNotIn('DF011', self.codes('FROM app:1\nRUN wget --ca-certificate=/certs/ca.pem https://example.test\n'))

    def test_038(self):
        self.assertNotIn('DF012', self.codes('FROM app:1\nRUN --mount=type=cache,target=/var/lib/apt apt-get update\n'))

    def test_039(self):
        self.assertNotIn('DF013', self.codes('FROM app:1\nRUN apt-get --yes install --no-install-recommends curl\n'))

    def test_040(self):
        self.assertNotIn('DF014', self.codes('FROM app:1\nRUN --mount=type=cache,target=/var/lib/apt/lists apt-get install curl\n'))

    def test_041(self):
        self.assertNotIn('DF015', self.codes('FROM app:1\nRUN apk add curl && rm -rf /var/cache/apk/*\n'))

    def test_042(self):
        self.assertNotIn('DF016', self.codes('FROM app:1\nENV PIP_NO_CACHE_DIR=true\nRUN pip3 install flask\n'))

    def test_043(self):
        self.assertNotIn('DF017', self.codes('FROM node:22\nRUN npm ci --omit=dev\n'))

    def test_044(self):
        self.assertNotIn('DF018', self.codes('FROM app:1\nCMD ["/app/server", "--port", "8080"]\n'))

    def test_045(self):
        self.assertNotIn('DF019', self.codes('FROM app:1\nWORKDIR C:/app\n'))

    def test_046(self):
        self.assertNotIn('DF020', self.codes('FROM app:1\nRUN chmod 0755 /app/server\n'))

    def test_047(self):
        self.assertNotIn('DF021', self.codes('FROM app:1\nRUN echo "documentation: sudo -u app"\n'))

    def test_048(self):
        self.assertNotIn('DF022', self.codes('FROM app:1\nHEALTHCHECK --interval=30s CMD ["/app/health"]\n'))

    def test_049(self):
        self.assertNotIn('DF023', self.codes('FROM app:1\nCOPY --from=builder /dist /app\n'))

    def test_050(self):
        self.assertNotIn('DF024', self.codes('FROM app:1\nLABEL description="MAINTAINER moved to OCI label"\n'))

    def test_051(self):
        self.assertNotIn('DF025', self.codes('FROM app:1\nRUN echo "from alpine"\n'))

    def test_052(self):
        self.assertNotIn('DF026', self.codes('FROM app:1\nLABEL description="ONBUILD disabled"\n'))

    def test_053(self):
        with self.assertRaises(ParseError):
            parse('')

    def test_054(self):
        with self.assertRaises(ParseError):
            parse('# only comment\n')

    def test_055(self):
        with self.assertRaises(ParseError):
            parse('RUN echo hello\n')

    def test_056(self):
        with self.assertRaises(ParseError):
            parse('FROM\n')

    def test_057(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1 broken alias\n')

    def test_058(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1 AS build\nFROM app:1 AS BUILD\n')

    def test_059(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1\nCMD []\n')

    def test_060(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1\nRUN ["echo", 5]\n')

    def test_061(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1\nCMD ["unterminated"\n')

    def test_062(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1\nRUN echo \\\n')

    def test_063(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1\nRUN <<END\necho hello\n')

    def test_064(self):
        with self.assertRaises(ParseError):
            parse('FROM app:1\n# dockercheck: ignore=DF003 reason=\nRUN true\n')

    def test_065(self):
        document = parse("FROM app:1\nRUN echo one \\\n    && echo two\n")
        instruction = document.instructions[1]
        self.assertEqual((instruction.line, instruction.end_line), (2, 3))

    def test_066(self):
        source = "FROM app:1\nRUN echo one " + "\\" + "\n# comment\n && echo two\n"
        self.assertIn("echo two", parse(source).instructions[1].value)

    def test_067(self):
        document = parse("# escape=`\nFROM app:1\nRUN echo one `\n && echo two\n")
        self.assertEqual(document.instructions[1].end_line, 4)

    def test_068(self):
        document = parse("FROM app:1 AS base\nUSER 1000\nFROM base AS runtime\n")
        self.assertIs(document.stages[1].parent, document.stages[0])
        self.assertEqual(document.stages[1].effective("USER").value, "1000")

    def test_069(self):
        document = parse("FROM --platform=linux/amd64 app:1 AS build\n")
        self.assertEqual((document.stages[0].base, document.stages[0].alias), ("app:1", "build"))

    def test_070(self):
        document = parse('FROM app:1\nRUN echo "<<EOF"\nUSER 1000\n')
        self.assertFalse(document.instructions[1].heredoc)
        self.assertEqual(len(document.instructions), 3)

    def test_071(self):
        document = parse("FROM app:1\nRUN <<-EOF\n\techo hello\n\tEOF\n")
        self.assertTrue(document.instructions[1].heredoc)
        self.assertEqual(document.instructions[1].end_line, 4)

    def test_072(self):
        updated, lines = uppercase_keywords("from app:1")
        self.assertEqual((updated, lines), ("FROM app:1", [1]))

    def test_073(self):
        self.assertEqual(uppercase_keywords("  from app:1\n")[0], "  FROM app:1\n")

    def test_074(self):
        source = 'FROM app:1\ncmd ["echo", "from lowercase"]\n'
        self.assertEqual(uppercase_keywords(source)[0], source.replace("cmd [", "CMD ["))

    def test_075(self):
        updated, _ = uppercase_keywords("# from comment\nfrom app:1\n")
        self.assertTrue(updated.startswith("# from comment\nFROM"))

    def test_076(self):
        source = "# dockercheck: ignore=DF025 reason=style convention\nfrom app:1\n"
        self.assertEqual(uppercase_keywords(source), (source, []))

