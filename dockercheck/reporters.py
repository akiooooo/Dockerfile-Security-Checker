from dataclasses import asdict
from urllib.parse import quote
import re

from . import __version__
from .rules import RULES


def json_report(reports):
    return {"tool": "dockercheck", "version": __version__, "files": [asdict(r) for r in reports],
        "summary": {level: sum(f.severity == level for r in reports for f in r.findings) for level in ("error", "warning", "info")}}


def sarif_report(reports):
    codes = sorted({f.rule for r in reports for f in r.findings})
    descriptors = [{"id": code, "shortDescription": {"text": RULES[code].title if code in RULES else "Ошибка синтаксиса"},
                    "helpUri": "https://docs.docker.com/reference/dockerfile/"} for code in codes]
    results = []
    for report in reports:
        path = report.path.replace('\\', '/')
        uri = quote(path, safe='/.:')
        if re.match(r'^[A-Za-z]:/', path):
            uri = 'file:///' + uri
        elif path.startswith('/'):
            uri = 'file://' + uri
        for item in report.findings:
            results.append({"ruleId": item.rule, "level": {"error":"error", "warning":"warning", "info":"note"}[item.severity],
                "message": {"text": item.message + ". " + item.recommendation},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri},
                    "region": {"startLine": item.line}}}]})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "dockercheck", "version": __version__, "rules": descriptors}}, "results": results}]}


def text_report(reports):
    lines = []
    for report in reports:
        lines.append(f"\n{report.path} (стадий: {report.stages})")
        if not report.findings:
            lines.append("  Замечаний нет")
        for item in report.findings:
            stage = f" [стадия {item.stage}]" if item.stage else ""
            lines.append(f"  {item.line}: {item.severity.upper():7} {item.rule}{stage}: {item.message}")
            lines.append(f"      {item.recommendation}")
        if report.suppressed:
            lines.append(f"  Пропущено по исключениям: {report.suppressed}")
    summary = json_report(reports)["summary"]
    lines.append(f"\nФайлов: {len(reports)} | ошибок: {summary['error']} | предупреждений: {summary['warning']} | рекомендаций: {summary['info']}")
    return "\n".join(lines)
