import json
import re
import shlex

from .models import Document, Instruction, Stage

KEYWORDS = set("ADD ARG CMD COPY ENTRYPOINT ENV EXPOSE FROM HEALTHCHECK LABEL MAINTAINER ONBUILD RUN SHELL STOPSIGNAL USER VOLUME WORKDIR".split())
DIRECTIVE = re.compile(r"^\s*#\s*dockercheck:\s*ignore=([A-Z0-9,]+)\s+reason=(\S.*)$")


class ParseError(ValueError):
    def __init__(self, line, message):
        self.line = line
        super().__init__(message)


def words(value, line):
    try:
        return shlex.split(value)
    except ValueError:
        raise ParseError(line, "Незакрытая кавычка в аргументах инструкции")


def without_flags(value):
    return re.sub(r"^(?:--[\w-]+(?:=\S+)?\s+)+", "", value)


def heredoc_markers(value):
    markers, quote, index = [], None, 0
    pattern = re.compile(r"<<(-?)(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_][\w-]*))")
    while index < len(value):
        char = value[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        else:
            match = pattern.match(value, index)
            if match:
                markers.append(match.groups())
                index = match.end()
                continue
        index += 1
    return markers


def parse(source, path="Dockerfile"):
    lines = source.splitlines()
    instructions, stages = [], []
    escape = "\\"
    pending = set()
    index = 0
    before_instruction = True
    while index < len(lines):
        raw = lines[index]
        line = index + 1
        index += 1
        if not raw.strip():
            continue
        if raw.lstrip().startswith("#"):
            directive = re.match(r"^\s*#\s*escape\s*=\s*([`\\])\s*$", raw, re.I)
            if directive and before_instruction:
                escape = directive.group(1)
            if "dockercheck:" in raw:
                suppression = DIRECTIVE.fullmatch(raw)
                if not suppression:
                    raise ParseError(line, "Исключение требует ignore=DFxxx и непустой reason=...")
                pending.update(suppression.group(1).split(","))
            continue
        before_instruction = False
        logical = raw
        while logical.rstrip().endswith(escape):
            logical = logical.rstrip()[:-1] + " "
            while index < len(lines) and (not lines[index].strip() or lines[index].lstrip().startswith("#")):
                index += 1
            if index >= len(lines):
                raise ParseError(line, "Незавершённый перенос инструкции")
            logical += lines[index].lstrip()
            index += 1
        match = re.match(r"^\s*([A-Za-z]+)(?:\s+(.*))?$", logical)
        if not match or match.group(1).upper() not in KEYWORDS:
            raise ParseError(line, "Неизвестная инструкция Dockerfile")
        original, value = match.group(1), (match.group(2) or "").strip()
        keyword = original.upper()
        if not value:
            raise ParseError(line, "Отсутствуют аргументы инструкции")
        heredocs = heredoc_markers(value) if keyword in ("RUN", "COPY", "ADD") else []
        bodies = []
        for strip_tabs, quoted, double, plain in heredocs:
            delimiter = quoted or double or plain
            body = []
            while index < len(lines):
                candidate = lines[index].lstrip("\t") if strip_tabs else lines[index]
                index += 1
                if candidate == delimiter:
                    break
                body.append(lines[index - 1])
            else:
                raise ParseError(line, "Не завершён here-document")
            bodies.append("\n".join(body))
        if keyword == "RUN" and bodies:
            value += "\n" + "\n".join(bodies)
        argument = without_flags(value)
        if keyword in ("CMD", "ENTRYPOINT", "SHELL", "RUN", "COPY", "ADD", "VOLUME") and argument.startswith("["):
            try:
                array = json.loads(argument)
                if not isinstance(array, list) or not array or not all(isinstance(x, str) for x in array):
                    raise ValueError()
            except (ValueError, json.JSONDecodeError):
                raise ParseError(line, "Некорректная JSON-форма инструкции")
        instruction = Instruction(keyword, value, line, index, original, pending, bool(heredocs))
        pending = set()
        instructions.append(instruction)
        if keyword == "FROM":
            tokens = words(value, line)
            while tokens and tokens[0].startswith("--"):
                tokens.pop(0)
            if len(tokens) not in (1, 3) or len(tokens) == 3 and tokens[1].upper() != "AS":
                raise ParseError(line, "Ожидается FROM image [AS stage]")
            base = tokens[0]
            alias = tokens[2] if len(tokens) == 3 else str(len(stages))
            if any(s.alias.lower() == alias.lower() for s in stages):
                raise ParseError(line, "Повторное имя стадии")
            parent = next((s for s in stages if s.alias.lower() == base.lower()), None)
            stages.append(Stage(len(stages), base, alias, instruction, parent=parent))
        elif stages:
            stages[-1].instructions.append(instruction)
        elif keyword != "ARG":
            raise ParseError(line, "До первой FROM допустимы только ARG и комментарии")
    if not stages:
        raise ParseError(1, "Не найдена инструкция FROM")
    if pending:
        raise ParseError(len(lines), "После исключения нет инструкции")
    return Document(path, source, instructions, stages)
