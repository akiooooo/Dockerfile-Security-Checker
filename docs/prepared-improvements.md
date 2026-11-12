# Подготовленные улучшения

Ветка [prepared-improvements](https://github.com/akiooooo/Dockerfile-Security-Checker/tree/prepared-improvements) содержит 100 реальных коммитов, подготовленных заранее. Большинство изменений расширяет регрессионные тесты; отдельные шаги исправляют обнаруженные дефекты. Это не 100 новых возможностей приложения.

Каждый шаг добавляет самостоятельный проверяемый сценарий. Все 100 сценариев вместе с исходными тестами прошли проверку; отдельно проверялся каждый добавляемый тест в соответствующей версии кода. Названия и состав изменений приведены ниже. Номер соответствует методу `test_NNN` в `tests/test_prepared_regressions.py`.

## Публикация

Каждый московский календарный день для каждого репозитория выбираются **от 1 до 4 публикаций** и соответствующее число разных часов в диапазоне 09:00-22:59. В выбранный час запуск дополнительно смещается на случайное число секунд: номинально публикация начинается между :07 и :17. Часы и секунды меняются по дням и отличаются между репозиториями. План воспроизводится из даты и имени репозитория, поэтому повторные запуски не меняют дневную норму.

Workflow проверяет план раз в час с 09:07 до 22:07 по Москве; в невыбранные часы он завершается без изменения файлов. В выбранный час ожидается запланированное время (не более 10 минут), обновляется main и выполняется следующий патч с тестами. После 23:00 автоматическая публикация запрещена, в том числе если GitHub задержал запуск. Время самого коммита дополнительно зависит от длительности проверок. Ручные публикации также расходуют дневной лимит, а `check_only` его не расходует. Уже обработанный час повторно не используется.

GitHub Actions может задерживать запуски и пропускать их при высокой нагрузке; пропущенные шаги не догоняются массово. Поэтому 1-4 - выбранный план на день, а при сбое фактических публикаций может оказаться меньше. Исходные коммиты перечислены в таблице ниже; номер применённого шага сохраняется в состоянии очереди.

Перед публикацией проверяются хеш патча, родитель, название и список файлов, затем выполняется полный набор тестов проекта. Ошибка тестов, конфликт, изменение рабочей копии или отказ push прерывают запуск. Принудительная отправка и автоматическое разрешение конфликтов не используются. После 100 шагов новых коммитов не будет.

Очередь: `.ghostcommit/queue.json`; состояние: `.ghostcommit/state.json`; исполнитель: `scripts/publish_prepared.py`. Изменять счётчик вручную нельзя - порядок зависит от предыдущих патчей. Текущая ветка `main` может содержать пользовательские изменения: если они конфликтуют с очередью, потребуется вручную проверить и пересобрать оставшиеся патчи.

Для ручной проверки откройте **Actions → Проверенные изменения по расписанию → Run workflow**. Флажок `check_only` проверяет следующий патч без публикации. Без флажка применяется один шаг с тестами. Локально `python scripts/publish_prepared.py --check-only` только проверяет; команда без флага создаёт и отправляет коммит, поэтому её следует запускать в отдельной чистой копии.

Для остановки выберите **Disable workflow** в меню Actions. Токены в коде и локальной панели отсутствуют: workflow использует временный `GITHUB_TOKEN` с правом `contents: write`. Публикация через этот токен не запускает другие workflows на push, поэтому тесты выполняются непосредственно перед отправкой. Дополнительный PAT не требуется.

Защита очереди проверяется командой `python -m unittest discover -s .ghostcommit -p test_queue_worker.py -q`. Тесты используют временные локальные репозитории, без обращений к GitHub.

## Состав очереди

| № | Изменение | Исходный коммит |
|---|---|---|
| 1 | Проверка Dockerfile без версии базового образа | [651256e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/651256e5ddca862bff177c229c8c2519308333c3) |
| 2 | Тест тега LATEST в верхнем регистре | [9e99075](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/9e990757d3218727a2ca566be96db4653c624b67) |
| 3 | Тест образа без digest из своего реестра | [2e6562c](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/2e6562cd111563d7ca014a26e36119076d20cfa5) |
| 4 | Неизвестная переменная в FROM | [f64f6dd](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/f64f6dd41747bca27cd0dc306439ff7c0c356185) |
| 5 | Проверка USER в образе scratch | [45d1841](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/45d18412476fd67e4e8c690f6dcd685222099004) |
| 6 | Нулевой UID с ведущими нулями | [91592b0](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/91592b0667603aa83d5757a6ebf6022e91992671) |
| 7 | Секретное имя переменной окружения | [407ca9d](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/407ca9ded8b38e020b7bf9692b39f241edc2a0da) |
| 8 | Копирование закрытого ключа Ed25519 | [9dfb1a3](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/9dfb1a3b1aecbb025e9913cdc88763f8c0e0c303) |
| 9 | Загрузка Git-репозитория через ADD | [5faad39](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/5faad393b84bb0509f58eaea25afe0abbd68c7b8) |
| 10 | Передача загрузки wget в bash | [5d1ecd1](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/5d1ecd1f168cf21240a409ce2bbdd272a7858760) |
| 11 | Проверка коротких флагов curl | [63ba629](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/63ba6297c6ce2c2531154c7c8c3f9d7410e4e65d) |
| 12 | apt-get update во вложенной оболочке | [de2e185](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/de2e185f702c940c68d5ffcea7fab8ffdb27746a) |
| 13 | Установка рекомендуемых пакетов apt | [3472114](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/3472114aa75dcc309e2baeca174c8a5e3f8b127b) |
| 14 | Списки apt после установки пакетов | [38522d8](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/38522d85a52dec52edc660d186825e886fe9acec) |
| 15 | Кеш apk при обновлении индекса | [5a1604a](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/5a1604aed3be5663de6018615b527443120728fc) |
| 16 | Кеш установки через python3 -m pip | [6d79363](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/6d793638d5fa249a3d8de2130fa02bb13c5aa235) |
| 17 | npm install без dev-зависимостей | [0155b54](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/0155b545877c8b5f4b6d670cf752d965d4e9a60d) |
| 18 | Shell ENTRYPOINT с командой exec | [fa37b26](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/fa37b266425c10859c3bdf0527bd16647699acdc) |
| 19 | Относительный путь WORKDIR | [d5e5a1e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/d5e5a1ed8ea5a050c89ebb060f1433b3d844c5d9) |
| 20 | Рекурсивные права 777 | [4e0230e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/4e0230ebb9b2b35c943dc2a0385bea200bb3ca0c) |
| 21 | sudo с выбором пользователя | [e1b0e2c](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e1b0e2cd79a2de6097ea4e51ea378c9b7eeb7be7) |
| 22 | Явное отключение HEALTHCHECK | [b060c14](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/b060c144e9e0e43e62467f79d1f89223bb914e80) |
| 23 | Широкий COPY в JSON-формате | [e2eb5a9](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e2eb5a93776c3728dfeecacd6931e28e95998c66) |
| 24 | MAINTAINER с адресом автора | [e25d8d8](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e25d8d820a2e345125751867a1df432fc142571d) |
| 25 | Смешанный регистр COPY | [a72e492](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a72e4921be4662d4b30a6a127a718a49acd6eca2) |
| 26 | Копирование через ONBUILD | [979c3fd](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/979c3fde39573f61fec4c8be9fdd645775467778) |
| 27 | Порт реестра в имени образа | [a8d7082](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a8d7082fa2196f605ad750d2c4d7e1756977eb3a) |
| 28 | Образ с именем latest и обычным тегом | [ccc0d8d](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/ccc0d8ddd234583149461fa27ea81d98dc4f09c3) |
| 29 | Тег и digest в одном FROM | [cc24606](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/cc246068e340a8d4480ce8c86687445aa3989d8e) |
| 30 | Значение ARG по умолчанию в FROM | [c8c6e52](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/c8c6e5256626c27135f39d0dbb24f9f7a3e82be9) |
| 31 | Непривилегированный числовой USER | [88ed757](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/88ed757dfb8db85b84890ae8c2476eb1c3978ca4) |
| 32 | Последнее переключение пользователя в стадии | [3765b22](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/3765b22b666ea8f1ffa4f662b3b9f9c53733f0ab) |
| 33 | Исправлена проверка ENV со старым синтаксисом | [1193265](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/11932654caaad9abea9c054c8b1b2d10ac53b887) |
| 34 | Шаблон env.sample при копировании | [50e09c6](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/50e09c6fd76cea05d935715af8038b161de10b1f) |
| 35 | Локальная распаковка через ADD | [fbb565c](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/fbb565c0b41919c1c95bf7892ae5b37c6488781a) |
| 36 | Отдельная загрузка файла с проверкой хеша | [6e80d92](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/6e80d92369b51aef3a424ed53a1e2f3f01faf6f2) |
| 37 | Загрузка с собственным CA-сертификатом | [f7b7398](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/f7b7398913dd420291560b13c33891c43b254f61) |
| 38 | Cache mount для apt-get update | [b6195f7](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/b6195f7e72a6edf14040baee0b58da61b100d198) |
| 39 | Флаг no-install-recommends при установке | [7c5a973](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/7c5a9731416aef2a93303e5a6af8910513dbc358) |
| 40 | Cache mount для списков apt | [cdc6d32](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/cdc6d32c60fcb9d86e5c9e685a5a12bc4ff78325) |
| 41 | Очистка кеша apk в том же слое | [7b7658c](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/7b7658cd96bbc24ee02c0976929f4fdfb2da21be) |
| 42 | Отключение кеша pip через ENV | [e144fe9](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e144fe93c146e567f988bf78bb607ec30a36e928) |
| 43 | Установка зависимостей через npm ci | [0d2a9bc](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/0d2a9bc13ad033ed85263d0a270c2bfbd05a2c43) |
| 44 | Exec-форма CMD с аргументами | [388777b](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/388777b162892e227f3b298682d40e193ec46da8) |
| 45 | Абсолютный WORKDIR в Windows | [a35a793](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a35a793fcb3bbcfba01809cf850e016d5cc187ed) |
| 46 | Права 0755 для исполняемого файла | [e187ca5](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e187ca54fff2cd09ea85c60f3f91fce8bc06a2b1) |
| 47 | Слово sudo в тексте команды echo | [47573a4](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/47573a49daf090318b10223b08a105e09f417b18) |
| 48 | Exec-форма HEALTHCHECK | [812b38b](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/812b38b0525daaac0e4d7d503f44362ee9580bc9) |
| 49 | COPY из другой стадии без dockerignore | [a0f45b1](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a0f45b19147f345c506a836a672039d9e6272c2a) |
| 50 | Слово MAINTAINER в метаданных | [bdc66ca](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/bdc66ca5226784eca3796d504873ea4257b236ff) |
| 51 | Строчные инструкции внутри аргумента RUN | [6c519b3](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/6c519b39d1e29af2e0b5def022adcf4855de6798) |
| 52 | Слово ONBUILD в метаданных | [22d9b7a](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/22d9b7a025f6f761e7d46b13b42c375b451db9ed) |
| 53 | Пустой Dockerfile | [6218529](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/621852900e1d9b7d81f35a8fd2d999bf7aa4a5f7) |
| 54 | Dockerfile только с комментариями | [6c407a9](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/6c407a95d57c5259fa2d46db30cd78fb914cce02) |
| 55 | Инструкция RUN до FROM | [8d492a6](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/8d492a6f64c8affb0ee96f8e76e6515a450350b6) |
| 56 | FROM без имени образа | [b719842](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/b7198429d4128c8661429bedf58a5e6fbe37b366) |
| 57 | Ошибка объявления стадии | [f3e7411](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/f3e7411445027d1b13840166adea22aa9dc23914) |
| 58 | Повтор имени стадии с другим регистром | [71fbab4](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/71fbab4523804f1912e71df1d59c5bbb7a9ce7b8) |
| 59 | Пустая JSON-команда | [f634966](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/f634966fc439e3a9db8a230e68d67f96f445252a) |
| 60 | Числовой аргумент в JSON-команде | [299f43e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/299f43e8831f2539dfd0f89e8b8bbaa48654479b) |
| 61 | Незакрытый JSON-массив | [bc8416e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/bc8416ec6463fcce9768c711f59f7f93a17962ea) |
| 62 | Незавершённый перенос RUN | [dc5f2ea](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/dc5f2ea53f6ce1be1ee8b6abb44d52462a5dcb8b) |
| 63 | Незавершённый heredoc | [e80e9df](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e80e9df4d7e02eb8a70af7e0642dc0cadf860b3f) |
| 64 | Пустая причина исключения правила | [8a91ab4](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/8a91ab4c1e4e0bf15c0854b200ce9bce2999be27) |
| 65 | Номера строк многострочной инструкции | [909397d](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/909397dcc7884c9ac81ee00d012032ca996a2da9) |
| 66 | Комментарий внутри переноса инструкции | [a118332](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a1183327d4e6f8b444fe1d98bfc5aecb2825e1ba) |
| 67 | Директива escape в Windows Dockerfile | [5ca1c29](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/5ca1c29fad7693fcb49817d8cae6d11b9d9f66d7) |
| 68 | Наследование пользователя от родительской стадии | [8aa8006](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/8aa800628ba645de7da857184c9d9204dff4336f) |
| 69 | Платформа перед именем образа | [a765840](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a765840d060605e19ffc332710eb7a74472cdc91) |
| 70 | Текст heredoc-маркера в echo | [e29f305](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e29f3054a78abbd27dbcd0a2696c21d633a44978) |
| 71 | Табуляция в heredoc с дефисом | [3a48183](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/3a48183a52f7a51763b37da8f8f95a83fa6f574e) |
| 72 | Исправление файла без завершающего переноса | [4b41887](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/4b4188724025ab4cf5f2a649dce8806070122d32) |
| 73 | Сохранение отступов при исправлении | [8a57d7a](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/8a57d7ae2ce26b2b36cbf6703c53700ae5a565d3) |
| 74 | Сохранение JSON-аргументов команды | [80cdfaf](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/80cdfaf1285dbc62e0887d8f3fe983a5a89f89f7) |
| 75 | Сохранение комментариев при исправлении | [0301f71](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/0301f7142f2516ca678244fe0f3427bfd06c4609) |
| 76 | Локальное исключение проверки регистра | [ffcab54](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/ffcab543d74f02e05c9f084aea503f517bc6815b) |
| 77 | Область действия исключения правила | [a6e30b0](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/a6e30b0ae07757bd281f26908ed05718d929688c) |
| 78 | Исправленный файл без лишнего backup | [4b792c7](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/4b792c7773d6b735e2fb982f29b828b068f5732e) |
| 79 | Сохранение исходных байтов в backup | [0373d6e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/0373d6efdd33b2c9ab0470d3c8b52d6a85dabe61) |
| 80 | Защита от изменения файла во время проверки | [0373a49](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/0373a49a6bc1b400ab920c14555b45093ffd4a0f) |
| 81 | Защита существующей резервной копии | [2c8f2fa](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/2c8f2faacff657a3dcd12b70bf0a34a64ceef25c) |
| 82 | Сохранение значений ENV при исправлении | [1166c76](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/1166c76636db8cb0bfe1e2a2d8ab5a186771bbbd) |
| 83 | Скрытие heredoc в предпросмотре | [968597e](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/968597e4806a166689281c5d4d33c297f53b3bb2) |
| 84 | Сохранение CRLF в предпросмотре | [7cd2f34](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/7cd2f34035ad84a8d40f822dd7420558e37b6400) |
| 85 | Повторное исправление без изменений | [5ecc42d](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/5ecc42d680b2e5550688a6258344a221494ca00d) |
| 86 | Команды Dockerfile не выполняются при исправлении | [c3454b2](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/c3454b21bf42cff6d9becfeb2ee9a909089f17db) |
| 87 | Пустая сводка JSON-отчёта | [6fcc720](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/6fcc7203cab375f010f4daebc548717b4193e77e) |
| 88 | Сводка ошибок нескольких файлов | [e12c382](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e12c3824c751535108fefeef491e0ba1771b8688) |
| 89 | Подавленные правила в JSON-отчёте | [6b8f837](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/6b8f837a6eee38d65bd737487a89df65deddd69a) |
| 90 | Спецсимволы пути в SARIF | [d024fc1](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/d024fc1bf13ed26b24bd66e268f178006f2a90fa) |
| 91 | Уровень рекомендаций в SARIF | [ce05394](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/ce0539444802367c5fb0078b83d2d795d2af3e5a) |
| 92 | Правила без дубликатов в SARIF | [7590418](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/7590418f47d1a0c795d043d7231879e6e53a771d) |
| 93 | Рекомендации в текстовом отчёте | [c9d7e54](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/c9d7e547134684c00efd4a31baf2b641112bc420) |
| 94 | Порог error при наличии рекомендаций | [2cd6590](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/2cd65908f27214db60450176a1e2ae576df9e6a2) |
| 95 | Порог warning при предупреждениях | [f1f0422](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/f1f042226d6eee21146e30f2ce897dc100a91616) |
| 96 | Отключение порога ошибок через none | [f1f0ef6](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/f1f0ef6a024381a5dfb1d26776f7353db099aa81) |
| 97 | Путь файла в JSON-отчёте CLI | [4ea15aa](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/4ea15aad2975269482e7cbacf00c8a700a2b96fc) |
| 98 | Ошибка синтаксиса при отключённом пороге | [e78ca0f](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/e78ca0f8cee2fcf1b73954764d51791672d208cc) |
| 99 | Порядок замечаний по строкам | [6850822](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/685082250b97e5404d15ea1a7523cd6c473c5852) |
| 100 | Выбор runtime-стадии без учёта регистра | [9a68210](https://github.com/akiooooo/Dockerfile-Security-Checker/commit/9a68210b77704b1336a6f79ad56cc3a75f54ac4f) |
