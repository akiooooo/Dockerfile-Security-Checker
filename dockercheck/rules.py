import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from .models import Finding
from .parser import without_flags
from .shell import commands, download_to_shell


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str
    title: str
    recommendation: str
    scope: str = "instruction"


RULES = {r.code: r for r in [
    Rule("DF001", "warning", "Базовый образ без версии", "Укажите версию образа; для воспроизводимости используйте digest.", "stage"),
    Rule("DF002", "warning", "Плавающий тег latest", "Замените latest выбранной версией и настройте регулярное обновление.", "stage"),
    Rule("DF003", "info", "Базовый образ без digest", "При необходимости строгой воспроизводимости закрепите sha256 digest и обновляйте его автоматически.", "stage"),
    Rule("DF004", "warning", "Не удалось определить базовый образ", "Проверьте значение переменной FROM в конфигурации сборки.", "stage"),
    Rule("DF005", "warning", "Пользователь финальной стадии не задан явно", "Задайте непривилегированного USER либо документируйте пользователя базового образа.", "final"),
    Rule("DF006", "error", "Финальный образ явно запускается от root", "Создайте пользователя и переключитесь на него перед CMD/ENTRYPOINT.", "final"),
    Rule("DF007", "error", "Возможный секрет в ARG или ENV", "Передавайте секрет через BuildKit secret mount или при запуске; проверьте историю образа."),
    Rule("DF008", "error", "Возможное копирование секретов", "Исключите секрет из контекста и используйте secret mount или runtime volume."),
    Rule("DF009", "warning", "Загрузка через ADD", "Предпочтите контролируемую загрузку; для удалённого ADD проверьте checksum."),
    Rule("DF010", "error", "Загруженный скрипт передаётся оболочке", "Скачайте файл отдельно, проверьте подпись/хеш и только затем запускайте."),
    Rule("DF011", "error", "Отключена проверка TLS", "Используйте проверку сертификата и корректный CA bundle."),
    Rule("DF012", "warning", "apt-get update отделён от install", "Объедините update и install через && в одном RUN, чтобы избежать устаревшего кеша."),
    Rule("DF013", "warning", "Установка рекомендуемых пакетов apt", "Добавьте --no-install-recommends, если рекомендуемые пакеты не нужны."),
    Rule("DF014", "warning", "Кеш списков apt остаётся в слое", "В том же RUN после установки удалите /var/lib/apt/lists/* либо используйте cache mount."),
    Rule("DF015", "warning", "Кеш индекса apk остаётся в образе", "Используйте apk add --no-cache или очистите /var/cache/apk в том же RUN."),
    Rule("DF016", "info", "Кеш pip может увеличивать образ", "Используйте --no-cache-dir, PIP_NO_CACHE_DIR либо BuildKit cache mount."),
    Rule("DF017", "warning", "npm install в финальной стадии", "Для lockfile проекта используйте npm ci; глобальные установки оценивайте отдельно."),
    Rule("DF018", "warning", "Shell-форма запуска процесса", "Предпочтите JSON exec-форму CMD/ENTRYPOINT, чтобы процесс корректно получал сигналы."),
    Rule("DF019", "warning", "Относительный WORKDIR", "Укажите абсолютный WORKDIR, чтобы не зависеть от рабочего каталога базового образа."),
    Rule("DF020", "error", "Права на запись для всех пользователей", "Назначьте владельца через COPY --chown и минимальные права для нужных файлов."),
    Rule("DF021", "warning", "sudo внутри сборки", "Выполняйте настройку под нужным USER; sudo в контейнере обычно не нужен."),
    Rule("DF022", "info", "Финальный образ без HEALTHCHECK", "Определите HEALTHCHECK или проверку готовности/жизни на уровне оркестратора.", "final"),
    Rule("DF023", "warning", "Широкий COPY без .dockerignore", "Создайте .dockerignore в корне контекста; исключите .git, секреты, кеши и локальные окружения."),
    Rule("DF024", "info", "Устаревшая инструкция MAINTAINER", "Перенесите автора в LABEL org.opencontainers.image.authors."),
    Rule("DF025", "info", "Непоследовательный регистр инструкций", "Используйте верхний регистр ключевых слов; доступно безопасное --fix."),
    Rule("DF026", "warning", "Скрытые действия ONBUILD", "Документируйте триггер для потребителей образа и избегайте неочевидных действий.")
]}


def finding(code, instruction, stage=""):
    rule = RULES[code]
    return Finding(code, rule.severity, rule.title, rule.recommendation, instruction.line, stage, code == "DF025")


def tokens(value):
    argument = without_flags(value)
    if argument.startswith("["):
        return json.loads(argument)
    try:
        return shlex.split(value)
    except ValueError:
        return []


def secret_name(name):
    return bool(re.search(r"(?:^|_)(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|ACCESS_KEY)(?:$|_)", name.upper()))


def check_instruction(instruction, stage, context, final):
    key, value = instruction.keyword, instruction.value
    low = value.lower()
    codes = []
    if instruction.original_keyword != key:
        codes.append("DF025")
    if key in ("ARG", "ENV"):
        parts = tokens(value)
        names = [part.split("=", 1)[0] for part in parts if "=" in part]
        if parts and (key == "ARG" or not names):
            names.append(parts[0].split("=", 1)[0])
        if any(secret_name(name) for name in names):
            codes.append("DF007")
    if key in ("COPY", "ADD"):
        parts = [p for p in tokens(value) if not p.startswith("--")]
        sources = parts[:-1]
        if any(re.search(r"(?:^|/)(?:\.env(?:\.(?!example$|sample$)[^/]+)?|\.git|\.ssh|id_rsa|id_ed25519)(?:/|$)|(?:^|/)private[^/]*\.key$", s, re.I) for s in sources):
            codes.append("DF008")
        if key == "ADD" and any(s.startswith(("http://", "https://", "git@", "git://")) for s in sources) and "--checksum=" not in low:
            codes.append("DF009")
        broad = any(s in (".", "./", "*", "./*") for s in sources)
        ignore = Path(context) / ".dockerignore"
        has_ignore = ignore.is_file() and any(line.strip() and not line.lstrip().startswith("#") for line in ignore.read_text(encoding="utf-8-sig").splitlines())
        if broad and "--from=" not in low and not has_ignore:
            codes.append("DF023")
    if key == "RUN":
        # Ищем типовые команды в RUN
        shell = low
        groups = commands(value)
        tools = [(group[0].rsplit("/", 1)[-1].lower(), group[1:]) for group in groups]
        if download_to_shell(value):
            codes.append("DF010")
        if any(name == "curl" and any(a == "--insecure" or re.fullmatch(r"-[A-Za-z]*k[A-Za-z]*", a) for a in args)
               or name == "wget" and "--no-check-certificate" in args for name, args in tools):
            codes.append("DF011")
        apt = [args for name, args in tools if name == "apt-get"]
        install = any("install" in args for args in apt)
        update = any("update" in args for args in apt)
        apt_cache = "--mount=type=cache" in shell and "/var/lib/apt" in shell
        if update and not install and not apt_cache:
            codes.append("DF012")
        if install:
            if any("install" in args and "--no-install-recommends" not in args for args in apt):
                codes.append("DF013")
            if not apt_cache and not any(name == "rm" and "/var/lib/apt/lists/*" in args for name, args in tools):
                codes.append("DF014")
        if any(name == "apk" and "add" in args and "--no-cache" not in args for name, args in tools) and not any(name == "rm" and any(a.startswith("/var/cache/apk") for a in args) for name, args in tools):
            codes.append("DF015")
        lineage = []
        current = stage
        while current:
            lineage.insert(0, current)
            current = current.parent
        environment = {}
        for ancestor in lineage:
            for item in ancestor.instructions:
                if item is instruction:
                    break
                if item.keyword == "ENV":
                    parts = tokens(item.value)
                    if parts and "=" not in parts[0]:
                        environment[parts[0]] = " ".join(parts[1:])
                    else:
                        environment.update(part.split("=", 1) for part in parts if "=" in part)
        pip_cache_disabled = environment.get("PIP_NO_CACHE_DIR", "").lower() in ("1", "true", "on")
        pip_install = any((name in ("pip", "pip2", "pip3") and "install" in args)
                          or (name in ("python", "python3") and args[:3] == ["-m", "pip", "install"]) for name, args in tools)
        if pip_install and not any("--no-cache-dir" in args for _, args in tools) and not ("--mount=type=cache" in shell and ".cache/pip" in shell) and not pip_cache_disabled:
            codes.append("DF016")
        if stage is final and any(name == "npm" and args and args[0] == "install" and not {"-g", "--global"}.intersection(args) for name, args in tools):
            codes.append("DF017")
        if any(name == "chmod" and next((a for a in args if not a.startswith("-")), "") in ("777", "0777") for name, args in tools):
            codes.append("DF020")
        if any(name == "sudo" for name, _ in tools):
            codes.append("DF021")
    if key in ("CMD", "ENTRYPOINT") and not value.startswith("["):
        codes.append("DF018")
    if key == "WORKDIR" and not value.startswith(("/", "$")) and not re.match(r"[A-Za-z]:[\\/]", value):
        codes.append("DF019")
    if key == "MAINTAINER":
        codes.append("DF024")
    if key == "ONBUILD":
        codes.append("DF026")
    return [(code, instruction) for code in codes]


def check_stage(stage, document):
    if stage.parent:
        return []
    base = stage.base
    defaults = {}
    for instruction in document.instructions:
        if instruction.keyword == "FROM":
            break
        if instruction.keyword == "ARG" and "=" in instruction.value:
            name, value = instruction.value.split("=", 1)
            defaults[name] = value.strip('"\'')
    base = re.sub(r"\$\{(\w+)\}|\$(\w+)", lambda m: defaults.get(m.group(1) or m.group(2), m.group(0)), base)
    if "$" in base:
        return [("DF004", stage.start)]
    if base.lower() == "scratch":
        return []
    codes = []
    if "@sha256:" not in base:
        codes.append("DF003")
        last = base.rsplit("/", 1)[-1]
        if ":" not in last:
            codes.append("DF001")
        elif last.rsplit(":", 1)[-1].lower() == "latest":
            codes.append("DF002")
    return [(code, stage.start) for code in codes]


def check_final(stage):
    result = []
    user = stage.effective("USER")
    if not user:
        result.append(("DF005", stage.start))
    else:
        name = user.value.split(":", 1)[0].strip().lower()
        if name == "root" or name.isdigit() and int(name) == 0:
            result.append(("DF006", user))
    health = stage.effective("HEALTHCHECK")
    if not health or health.value.upper() == "NONE":
        result.append(("DF022", health or stage.start))
    return result
