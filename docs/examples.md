# Демонстрационные файлы

Набор содержит **18 Dockerfile**: 8 good, 6 bad и 4 edge. Ожидаемые наборы кодов записаны в `examples/manifest.json`. Метка good означает отсутствие ошибок и предупреждений выбранной политики, а не доказанное отсутствие уязвимостей.

| Каталог | Сценарий |
| --- | --- |
| good/python | Минимальный Python HTTP-сервис с USER и HEALTHCHECK |
| good/node | Установка npm ci в builder и перенос node_modules |
| good/go | Компиляция в builder, scratch runtime и числовой USER |
| good/inherited | Наследование USER и HEALTHCHECK из предыдущей стадии |
| good/apt | Update/install/очистка в одном слое |
| good/buildkit | Cache mount pip и secret mount вместо ARG |
| good/arg | Простой глобальный ARG со значением образа по умолчанию |
| good/heredoc | RUN heredoc, текст FROM внутри скрипта |
| bad/root | root, latest, относительный каталог, apt и chmod 777 |
| bad/secrets | Только фиктивные значения, опасные имена ENV/ARG и пути COPY |
| bad/download | Отключённый TLS, pipe-to-shell, удалённый ADD |
| bad/context | COPY . без ignore, npm install, shell ENTRYPOINT |
| bad/cache | Кеши apk и pip |
| bad/legacy | MAINTAINER, ONBUILD, sudo и регистр |
| edge/unresolved | FROM зависит от неизвестного build-arg |
| edge/suppression | Обоснованные исключения перед FROM |
| edge/invalid-json | Ошибка JSON, ожидается PARSE |
| edge/false-positive | Опасные слова в echo и безопасный .env.example |

## Как показывать на защите

```bash
python -m dockercheck examples/bad/root/Dockerfile
python -m dockercheck examples/good/python/Dockerfile
python -m dockercheck examples/edge/false-positive/Dockerfile
python -m dockercheck examples/bad/legacy/Dockerfile --dry-run
python scripts/evaluate.py
```

Для демонстрации реальной сборки есть самостоятельный `examples/good/python` с app.py:

```bash
docker build -t dockercheck-python-demo examples/good/python
docker run --rm -p 127.0.0.1:8080:8080 dockercheck-python-demo
```

Открыть http://127.0.0.1:8080. Другие файлы предназначены прежде всего для статического анализа; часть из них - шаблоны, требующие файлов приложения или параметров сборки. Все bad-примеры следует анализировать, а не собирать и запускать. Домен example.invalid выбран для фиктивных удалённых адресов; реальные секреты в корпус не включены.
