# Dockercheck

Учебный проект на Python. Проверяет Dockerfile и подсказывает, что стоит поправить. Например, замечает запуск от root, тег `latest` и переменные, в которых могут храниться секреты.

Для запуска нужен Python 3.11 или новее. Устанавливать пакеты не нужно. Программа читает Dockerfile как текст, поэтому установленный Docker для проверки тоже не нужен.

## Как запустить

```sh
git clone https://github.com/akiooooo/Dockerfile-Security-Checker.git
cd Dockerfile-Security-Checker
python -m dockercheck examples/bad/root/Dockerfile
```

На Windows вместо `python` можно использовать `py -3`.

В этом примере среди замечаний будет такая строка:

```text
  6: ERROR   DF006 [стадия 0]: Финальный образ явно запускается от root
```

Для проверки своей папки передайте её путь. Программа найдёт `Dockerfile`, `Dockerfile.*` и `*.Dockerfile` во вложенных папках.

```sh
python -m dockercheck .
```

Если запустить команду без пути, она проверит `Dockerfile` в текущей папке. Все 26 правил можно посмотреть через `python -m dockercheck --list-rules` или в [чек-листе](docs/checklist.md).

## Отчёты и настройки

```sh
python -m dockercheck Dockerfile --format json --output reports/result.json
python -m dockercheck Dockerfile --format sarif --output reports/result.sarif
python -m dockercheck Dockerfile --fail-on error
```

По умолчанию ошибки и предупреждения дают код выхода `1`. С `--fail-on error` порогом будут только ошибки. При ошибке разбора файла программа тоже вернёт `1`, даже с `--fail-on none`. Если всё прошло по выбранному порогу, код будет `0`. Проблемы с аргументами, настройками или чтением и записью файлов дают `2`.

С `--context .` можно указать папку сборки для поиска `.dockerignore`. Без этого параметра он ищется рядом с каждым Dockerfile. Для многостадийного файла можно указать `--target имя_стадии`, чтобы выбрать, какую стадию считать финальной.

Отдельное правило можно отключить для всей проверки через `--ignore DF022` или только для следующей инструкции. Для локального исключения нужна причина.

```dockerfile
# dockercheck: ignore=DF022 reason=Health checks are set in Kubernetes
FROM alpine:3.21
USER 10001
CMD ["true"]
```

## Что можно исправить автоматически

Пока `--fix` только меняет регистр инструкций, например `from` на `FROM`. Сначала можно посмотреть изменения через `--dry-run`. При записи рядом с исходником создаётся копия `.bak`.

```sh
python -m dockercheck examples/bad/legacy/Dockerfile --dry-run
python -m dockercheck path/to/Dockerfile --fix
```

## Тесты

```sh
python -m unittest discover -s tests -v
python scripts/evaluate.py
python -m dockercheck examples/good
```

В `examples` лежат 18 файлов, на которых удобно посмотреть, как срабатывают правила. `evaluate.py` сравнивает результаты с ожидаемыми находками из `examples/manifest.json`. GitHub Actions запускает тесты на Windows и Ubuntu и сохраняет пример отчёта SARIF.

## Запуск через Docker

Соберите образ из папки проекта.

```sh
docker build -t dockercheck-local .
```

Пример запуска из PowerShell в папке с проверяемым Dockerfile:

```powershell
docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/work,readonly" dockercheck-local /work/Dockerfile
```

Та же команда для Bash:

```bash
docker run --rm --mount "type=bind,source=$(pwd),target=/work,readonly" dockercheck-local /work/Dockerfile
```

Если нужно применить `--fix` или записать отчёт в подключённую папку, уберите `readonly` и дайте контейнеру права на запись.

## Ещё о проекте

По одному Dockerfile можно заметить типичные проблемы. Для поиска CVE понадобится проверка собранного образа. Сложные команды в `RUN` лучше просмотреть вручную.

- [Как устроен код](docs/architecture.md)
- [Какие есть примеры](docs/examples.md)
- [Как подключить в CI](docs/ci.md)
- [Результаты проверок](docs/validation.md)
- [Источники](docs/sources.md)
- [Подготовленные изменения](docs/prepared-improvements.md)

Архив проекта можно собрать командой `python scripts/package.py`. Он появится в `dist`.

В работе над проектом использовался ИИ. В задании есть отдельное требование к самостоятельному написанию кода.
