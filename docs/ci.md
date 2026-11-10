# Интеграция в CI/CD

## Минимальный pipeline

```yaml
name: Dockerfile policy
on: [push, pull_request]
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m dockercheck Dockerfile --fail-on warning
```

Такой вариант предполагает, что исходники анализатора есть в репозитории. Для другого проекта можно подключить проверенный релиз инструмента отдельным checkout или использовать собранный контейнер. Для воспроизводимости зависимость от внешнего инструмента стоит закрепить по версии/commit.

## Публикация отчёта

```yaml
      - run: python -m dockercheck Dockerfile --format sarif --output reports/dockercheck.sarif
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dockercheck-report
          path: reports/dockercheck.sarif
```

Сохранение артефакта не равно загрузке в GitHub Code Scanning. Для Code Scanning нужно отдельно настроить upload-sarif, подходящие разрешения и доступность функции в репозитории. По умолчанию проект только сохраняет отчёт, не выдавая workflow лишние права.

Для GitLab, Jenkins и других систем смысл тот же: запустить CLI и использовать код завершения шага. Не добавляйте `|| true` в блокирующую проверку, если хотите реально останавливать pipeline.

## Рекомендуемый порядок

1. Dockercheck: локальная политика, очевидные риски и рекомендации.
2. `docker build --check .`: встроенные проверки BuildKit для поддерживаемой версии Docker.
3. Сборка образа с правильным контекстом и build secrets.
4. Сканирование зависимостей и итогового образа на CVE.
5. Тестовый запуск: пользователь, сигналы остановки, доступность, нужные права.
6. Публикация в registry после успешных проверок.

Встроенные проверки описаны в [Docker build checks](https://docs.docker.com/build/checks/). Dockercheck дополняет этот этап локальными требованиями, но не заменяет его.

## Где не запускать --fix

В CI лучше использовать обычную проверку или `--dry-run`. Автоматическая запись коммитов и push в чужую ветку здесь не реализованы. Исправления удобнее посмотреть локально, проверить .bak и включить в обычный review.
