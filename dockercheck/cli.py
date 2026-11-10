import argparse
import difflib
import json
import sys
from pathlib import Path

from . import __version__
from .engine import analyze
from .fixer import apply_fix, masked_preview, uppercase_keywords
from .parser import ParseError
from .reporters import json_report, sarif_report, text_report
from .rules import RULES


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Dockercheck — проверка Dockerfile без Docker и внешних зависимостей")
    parser.add_argument("paths", nargs="*", help="Dockerfile или каталоги для рекурсивного поиска")
    parser.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    parser.add_argument("--output", type=Path, help="Записать отчёт в файл")
    parser.add_argument("--fail-on", choices=("error", "warning", "info", "none"), default="warning")
    parser.add_argument("--ignore", default="", help="Исключить правила, например DF003,DF022")
    parser.add_argument("--context", type=Path, help="Корень build context для проверки .dockerignore")
    parser.add_argument("--target", help="Считать указанную стадию финальной; все стадии по-прежнему анализируются")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--fix", action="store_true", help="Исправить регистр ключевых слов; создать .bak")
    actions.add_argument("--dry-run", action="store_true", help="Показать diff безопасных исправлений, не менять файл")
    parser.add_argument("--list-rules", action="store_true")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    if args.list_rules:
        print("\n".join(f"{r.code}  {r.severity:7}  {r.title}" for r in RULES.values()))
        return 0
    ignored = {code.strip() for code in args.ignore.split(",") if code.strip()}
    if ignored - RULES.keys():
        parser.error("Неизвестные правила в --ignore")
    if args.fix and "DF025" in ignored:
        parser.error("--fix несовместим с исключением DF025")
    paths = []
    for raw in args.paths or ["Dockerfile"]:
        path = Path(raw)
        if not path.exists():
            parser.error(f"Путь не найден: {path}")
        if path.is_dir():
            paths.extend(p for p in path.rglob("*") if p.is_file()
                and (p.name == "Dockerfile" or p.name.startswith("Dockerfile.") or p.name.endswith(".Dockerfile"))
                and not p.name.endswith(".bak") and not {".git", ".venv", "node_modules", ".tools"}.intersection(p.parts))
        else:
            paths.append(path)
    paths = sorted(set(paths), key=str)
    if not paths:
        parser.error("Dockerfile не найдены")
    if args.output and any(args.output.resolve() == p.resolve() for p in paths):
        parser.error("Отчёт не может перезаписывать исходный Dockerfile")
    reports = []
    try:
        for path in paths:
            source = path.read_bytes().decode("utf-8-sig")
            if args.dry_run:
                updated, _ = uppercase_keywords(source)
                diff = "".join(difflib.unified_diff(masked_preview(source).splitlines(True), masked_preview(updated).splitlines(True),
                               fromfile=str(path), tofile=str(path) + " (исправлено)"))
                print(diff or f"{path}: безопасных исправлений нет", file=sys.stderr)
            if args.fix:
                changed = apply_fix(path, source)
                if changed:
                    print(f"{path}: исправлены строки {', '.join(map(str, changed))}; создана .bak", file=sys.stderr)
                    source = path.read_bytes().decode("utf-8-sig")
            reports.append(analyze(source, str(path), args.context, ignored, args.target))
        if args.format == "text":
            output = text_report(reports)
        else:
            output = json.dumps((json_report if args.format == "json" else sarif_report)(reports), ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
    except (OSError, ValueError, ParseError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2
    levels = {"none": set(), "error": {"error"}, "warning": {"error", "warning"}, "info": {"error", "warning", "info"}}
    return int(any(f.rule == "PARSE" or f.severity in levels[args.fail_on] for report in reports for f in report.findings))
