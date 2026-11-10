import json
import re
import shlex

from .parser import without_flags


def commands(value, depth=0):
    if depth > 3:
        return []
    value = without_flags(value)
    if value.startswith("["):
        groups = [json.loads(value)]
    else:
        value = re.sub(r"<<-?(?:'[^']+'|\"[^\"]+\"|[A-Za-z_][\w-]*)", "", value)
        lexer = shlex.shlex(value.replace("\n", ";"), posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        groups, current = [], []
        try:
            for token in lexer:
                if token and all(c in ";&|" for c in token):
                    if current:
                        groups.append(current)
                    current = []
                else:
                    current.append(token)
            if current:
                groups.append(current)
        except ValueError:
            return []
    result = []
    for group in groups:
        while group and (re.match(r"^[A-Za-z_]\w*=", group[0]) or group[0] in ("then", "do", "exec", "command", "env")):
            group = group[1:]
        if not group:
            continue
        result.append(group)
        name = group[0].rsplit("/", 1)[-1]
        if name == "sudo" and len(group) > 1 and not group[1].startswith("-"):
            result.append(group[1:])
        if name in ("sh", "bash", "ash", "zsh") and len(group) >= 3 and group[1] == "-c":
            result.extend(commands(group[2], depth + 1))
    return result


def download_to_shell(value):
    for group in commands(value):
        if len(group) >= 3 and group[0].rsplit("/", 1)[-1] in ("sh", "bash", "ash", "zsh") and group[1] == "-c":
            if download_to_shell(group[2]):
                return True
    value = without_flags(value)
    if value.startswith("["):
        return False
    lexer = shlex.shlex(value, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    previous, current, connector = [], [], ""
    try:
        for token in list(lexer) + [";"]:
            if token and all(c in ";&|" for c in token):
                if connector == "|" and previous and current:
                    if previous[0].rsplit("/", 1)[-1] in ("curl", "wget") and current[0].rsplit("/", 1)[-1] in ("sh", "bash", "ash", "zsh"):
                        return True
                previous, current, connector = current, [], token
            else:
                current.append(token)
    except ValueError:
        return False
    return False
