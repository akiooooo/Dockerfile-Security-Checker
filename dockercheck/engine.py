from pathlib import Path

from .models import Finding, Report
from .parser import ParseError, parse
from .rules import RULES, check_final, check_instruction, check_stage, finding


def analyze(source, path="Dockerfile", context=None, ignored=None, target=None):
    ignored = set(ignored or [])
    unknown = ignored - RULES.keys()
    if unknown:
        raise ValueError("Неизвестные правила: " + ", ".join(sorted(unknown)))
    try:
        document = parse(source, path)
    except ParseError as error:
        return Report(str(path), [Finding("PARSE", "error", str(error),
            "Исправьте синтаксис. Анализ этого файла остановлен, чтобы не выдавать недостоверные результаты.", error.line)])
    for item in document.instructions:
        unknown = item.ignored - RULES.keys()
        if unknown:
            raise ValueError(f"Строка {item.line}: неизвестные правила в исключении: " + ", ".join(sorted(unknown)))
    final = document.stages[-1]
    if target:
        final = next((stage for stage in document.stages if stage.alias.lower() == target.lower()), None)
        if not final:
            raise ValueError("Целевая стадия не найдена")
    context = context or Path(path).parent
    results = []
    suppressed = 0
    for stage in document.stages:
        matches = check_stage(stage, document)
        matches.extend(check_instruction(stage.start, stage, context, final))
        for item in stage.instructions:
            matches.extend(check_instruction(item, stage, context, final))
        if stage is final:
            matches.extend(check_final(stage))
        for code, item in matches:
            if code in ignored or code in item.ignored:
                suppressed += 1
                continue
            results.append(finding(code, item, stage.alias))
    # В ARG до первой FROM тоже могут быть секреты
    first = document.stages[0].start.line
    for item in document.instructions:
        if item.line >= first:
            break
        for code, checked in check_instruction(item, document.stages[0], context, final):
            if code in ignored or code in item.ignored:
                suppressed += 1
            else:
                results.append(finding(code, checked))
    return Report(str(path), sorted(results, key=lambda item: (item.line, item.rule)), len(document.stages), suppressed)
