import re
import os
import tempfile
from pathlib import Path

from .parser import parse


def uppercase_keywords(source):
    document = parse(source)
    lines = source.splitlines(keepends=True)
    changed = []
    for instruction in document.instructions:
        if instruction.original_keyword != instruction.keyword and "DF025" not in instruction.ignored:
            index = instruction.line - 1
            lines[index] = re.sub(r"^(\s*)[A-Za-z]+", lambda m: m.group(1) + instruction.keyword, lines[index], count=1)
            changed.append(instruction.line)
    return "".join(lines), changed


def apply_fix(path, source):
    updated, changed = uppercase_keywords(source)
    if not changed:
        return changed
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Автоисправление символических ссылок не поддерживается")
    original = path.read_bytes()
    if original.decode("utf-8-sig") != source:
        raise ValueError("Файл изменился после чтения; повторите проверку")
    backup = path.with_name(path.name + ".bak")
    # Не перезаписываем старую резервную копию при повторном запуске.
    with backup.open("xb") as stream:
        stream.write(original)
    bom = original.startswith(b"\xef\xbb\xbf")
    data = updated.encode("utf-8-sig" if bom else "utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return changed


def masked_preview(source):
    lines = source.splitlines(keepends=True)
    for item in parse(source).instructions:
        for index in range(item.line - 1, item.end_line):
            ending = "\r\n" if lines[index].endswith("\r\n") else "\n" if lines[index].endswith("\n") else ""
            prefix = item.original_keyword if index == item.line - 1 else "#"
            lines[index] = prefix + " [аргументы скрыты]" + ending
    return "".join(lines)
