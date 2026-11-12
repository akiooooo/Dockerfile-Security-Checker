# Источники и границы стандарта

Материалы проверены 10 ноября 2026 года. Правила DFxxx и уровни серьёзности - решения этого учебного проекта. Они не являются номерами проверок Docker, Hadolint или CIS.

| ID | Первичный источник | Для чего использован |
| --- | --- | --- |
| S1 | [Docker: Building best practices](https://docs.docker.com/build/building/best-practices/) | Образы, слои, пакетный менеджер, пользователь |
| S2 | [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) | Синтаксис и семантика инструкций |
| S3 | [Docker: SecretsUsedInArgOrEnv](https://docs.docker.com/reference/build-checks/secrets-used-in-arg-or-env/) | Почему ARG/ENV не подходят для секретов |
| S4 | [Docker: Build secrets](https://docs.docker.com/build/building/secrets/) | Передача build-time секретов через mounts |
| S5 | [Docker: Build context / .dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files) | Граница контекста и исключения файлов |
| S6 | [Docker: Rootless mode](https://docs.docker.com/engine/security/rootless/) | Различие USER контейнера и режима daemon |
| S7 | [curl: --insecure](https://curl.se/docs/manpage.html#-k) | Последствия отключения проверки TLS |
| S8 | [GNU Wget: HTTPS options](https://www.gnu.org/software/wget/manual/html_node/HTTPS-_0028SSL_002fTLS_0029-Options.html) | Проверка сертификатов загрузчика |
| S9 | [Docker: Optimize cache usage](https://docs.docker.com/build/cache/optimize/) | Cache mounts вне итогового слоя |
| S10 | [Alpine: apk](https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper) | Модель установки и кеша apk |
| S11 | [pip: Caching](https://pip.pypa.io/en/stable/topics/caching/) | Влияние кеша и осознанное отключение |
| S12 | [npm: npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci) | Установка по lockfile |
| S13 | [Docker: JSONArgsRecommended](https://docs.docker.com/reference/build-checks/json-args-recommended/) | Exec-форма и сигналы |
| S14 | [Docker: WorkdirRelativePath](https://docs.docker.com/reference/build-checks/workdir-relative-path/) | Зависимость от рабочего каталога base image |
| S15 | [OCI Image annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md) | Метаданные автора |
| S16 | [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker) | Общая структура hardening-проверок образов и среды |
| S17 | [Docker Engine security](https://docs.docker.com/engine/security/) | Namespaces, cgroups, daemon и capabilities |
| S18 | [SARIF 2.1.0, OASIS](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html) | Формат машинного отчёта |

На публичной странице CIS представлено семейство Docker Benchmark; полный текст и условия получения зависят от CIS. В работе не заявляется проверка по конкретной редакции CIS и не приводятся непроверенные номера её пунктов. Документ не воспроизводит полный Benchmark и не заменяет аудит Docker host.

Минимальный размер образа - полезная цель, но сам по себе небольшой образ не доказывает безопасность. Аналогично, digest помогает воспроизводимости, но без процесса обновления может закрепить уязвимую версию. Поэтому стандарт отделяет автоматические признаки от ручного ревью и управления обновлениями.
