import unittest

from dockercheck.parser import ParseError, parse


class ParserTests(unittest.TestCase):
    def test_continuation_comments_lines_and_inheritance(self):
        source = '# syntax=docker/dockerfile:1\nARG BASE=alpine:3.21\nFROM ${BASE} AS base\nUSER 10001\nRUN apk add \\\n # comment\n --no-cache curl\nFROM base AS final\nCMD ["true"]\n'
        document = parse(source)
        self.assertEqual(len(document.stages), 2)
        self.assertEqual(document.stages[0].instructions[1].line, 5)
        self.assertEqual(document.stages[0].instructions[1].end_line, 7)
        self.assertIs(document.stages[1].parent, document.stages[0])
        self.assertEqual(document.stages[1].effective('USER').value, '10001')

    def test_heredoc_body_not_interpreted_as_docker_instructions(self):
        source = 'FROM alpine:3.21\nRUN <<EOF\necho FROM fake:latest\necho USER root\nEOF\nUSER 10001\n'
        document = parse(source)
        self.assertEqual([i.keyword for i in document.instructions], ['FROM', 'RUN', 'USER'])
        self.assertEqual(document.instructions[1].end_line, 5)

    def test_backtick_escape(self):
        document = parse('# escape=`\nFROM image:1\nRUN echo one `\n two\n')
        self.assertIn('two', document.instructions[1].value)

    def test_quoted_heredoc_text_is_not_a_marker(self):
        document = parse('FROM app:1\nRUN echo "<<EOF"\nUSER 10001\n')
        self.assertFalse(document.instructions[1].heredoc)

    def test_json_with_copy_flags(self):
        document = parse('FROM alpine:3.21\nCOPY --chown=10001 ["app file", "/app/"]\n')
        self.assertEqual(document.instructions[1].keyword, 'COPY')

    def test_scoped_suppression(self):
        document = parse('# dockercheck: ignore=DF003,DF022 reason=accepted for this fixture\nFROM alpine:3.21\nUSER 10001\n')
        self.assertEqual(document.instructions[0].ignored, {'DF003', 'DF022'})
        self.assertEqual(document.instructions[1].ignored, set())

    def test_parse_errors(self):
        cases = ['', 'RUN true', 'FROM', 'FROM a AS', 'FROM a\nWAT value',
                 'FROM a\nCMD ["broken"', 'FROM a\nRUN <<EOF\ntrue',
                 'FROM a\nRUN echo \\', 'FROM a AS build\nFROM b AS build',
                 '# dockercheck: ignore=DF003\nFROM a',
                 'FROM a\n# dockercheck: ignore=DF003 reason=no next instruction',
                 'FROM a\nCOPY --chown=1 ["broken"']
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(ParseError):
                    parse(source)


if __name__ == '__main__':
    unittest.main()
