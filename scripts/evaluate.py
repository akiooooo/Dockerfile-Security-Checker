"""Сравнение результатов с вручную размеченным демонстрационным корпусом."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dockercheck.engine import analyze


def main():
    examples = ROOT/'examples'
    manifest = json.loads((examples/'manifest.json').read_text(encoding='utf-8'))
    tp = fp = fn = 0
    for relative, expected in manifest.items():
        path = examples/relative
        actual = {f.rule for f in analyze(path.read_text(encoding='utf-8'), str(path)).findings}
        expected = set(expected)
        tp += len(actual & expected)
        fp += len(actual - expected)
        fn += len(expected - actual)
        if actual != expected:
            print(relative, 'extra:', sorted(actual-expected), 'missing:', sorted(expected-actual))
    print(json.dumps({'files':len(manifest), 'true_positive_pairs':tp, 'false_positive_pairs':fp,
        'false_negative_pairs':fn, 'precision':tp/(tp+fp) if tp+fp else None,
        'recall':tp/(tp+fn) if tp+fn else None}, indent=2))
    return int(bool(fp or fn))


if __name__ == '__main__':
    raise SystemExit(main())
