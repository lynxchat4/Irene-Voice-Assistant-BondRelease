# Карта файлов проекта LAVA (Irene Voice Assistant)
**Дата:** 2026-08-22 · **Цель:** понять что можно удалить без поломки

Легенда:
- 🔴 **Критично** — без файла не запустится
- 🟠 **Нужно для фичи** — можно удалить только если фича не нужна
- 🟡 **Dev/тесты** — можно удалить в проде, нужно для разработки
- 🟢 **Доки/опционально** — можно удалить, на работу не влияет
- 🔵 **Генерируется** — можно удалить, пересоздастся
- ⚪ **Мусор/артефакт** — смело удалять

---

## Корень проекта

| Файл | Назначение | Можно удалить? | Что будет если удалить |
|------|------------|----------------|------------------------|
| `README.md` | Описание проекта, инструкции запуска, доки по Docker/Telegram | 🟢 Да | Потеряешь справку, на запуск не влияет |
| `LICENSE` | Лицензия MIT | 🟢 Да | Юридически нежелательно, технически не влияет |
| `Dockerfile` | Сборка Docker-образа (3 стадии: frontend node + ssl + python) | 🟢 Да если не используешь Docker | Не соберёшь образ, `docker build` сломается |
| `.dockerignore` | Исключения для Docker build контекста | 🟢 Да | Увеличится контекст сборки, медленнее |
| `.gitignore` | Исключения git (venv, __pycache__, *.pt, dist и т.д.) | 🟢 Да | Мусор попадёт в git |
| `mypy.ini` | Конфиг mypy (`ignore_errors` для snapshots) | 🟡 Да | mypy будет ругаться на snapshots |
| `requirements.txt` | **Полные Python зависимости** (vosk, torch, fastapi, sounddevice и т.д.) | 🔴 Нет | `pip install` не поставит зависимости, не запустится |
| `requirements-docker.txt` | Урезанные зависимости для Docker (без pyttsx3 и т.п.) | 🟠 Нужно для Docker | Docker сборка упадёт |
| `requirements-ci.txt` | Dev зависимости (mypy, pep8, coverage, coveralls) | 🟡 Да | Не запустишь `mypy`/`pep8`/coverage в CI |
| `install.sh` | **Инсталлятор Linux/macOS/WSL** (создаёт venv, pip, npm build) | 🟢 Да после установки | Не поставишь с нуля одной командой, ручная установка останется |
| `install.bat` | **Инсталлятор Windows CMD** (аналог .sh) | 🟢 Да после установки | То же для Windows |
| `AGENTS.md` | Инструкция для AI-агентов (куда смотреть в handbook) | 🟢 Да | AI будет дольше искать |
| `nul` | Артефакт Windows (`> nul`), пустой файл 167б | ⚪ Да — **удалить!** | Ничего, это мусор |

---

## `doc/` — документация

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `doc/client-server-protocol.md` | **Спека WebSocket протокола** (negotiate, все PROTOCOL_*) | 🟢 Да | Потеряешь доку для разработки клиентов |
| `doc/local-face.md` | Как настроить локальный микрофон/динамик + Docker `--device /dev/snd` | 🟢 Да | Не поймёшь как завести звук в Docker |
| `doc/plugin-dev-guide.md` | **Гайд по написанию плагинов** (define_commands, config, lifecycle) | 🟢 Да | Не напишешь плагин без чтения кода |
| `doc/img/web_screens.jpg` | Скриншоты веб-интерфейса для README | 🟢 Да | Картинка в README пропадёт |

Все `doc/` — только доки, на рантайм не влияют.

---

## `docker-config/` — дефолтные конфиги для Docker

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `docker-config/discover_plugins.yaml` | Пути поиска плагинов (`{irene_home}/plugins`, `{python_path}/irene_plugin_*/...`) | 🔴 Нет для Docker | В контейнере не найдёт плагины |
| `docker-config/face_web_server.yaml` | Хост/порт/SSL для `face_web_server` (8086, cert/key) | 🟠 Нужно для Docker | Веб не стартанёт с дефолтом |
| `docker-config/plugin_tts_silero_v3.yaml` | Пути к Silero модели | 🟠 Нужно если Silero | TTS Silero не найдёт модель в Docker |
| `docker-config/vosk_model_loader.yaml` | URL и пути Vosk модели (`alphacephei.com/...small-ru-0.22.zip`) | 🟠 Нужно если Vosk | STT не скачает модель |

Вне Docker эти файлы не используются — можно удалить если запускаешь без Docker. Внутри контейнера копируются в `/home/python/config` (см. Dockerfile).

---

## `resources/` — предзагруженные модели

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `resources/README.md` | Описание откуда брать модели | 🟢 Да |
| `resources/silero-models/c9e311e...-v3_1_ru.pt` (60М) | **Русская Silero TTS модель v3.1** | 🟠 Нужно если хочешь офлайн TTS | Без неё Silero будет качать или упадёт, можно заменить на другую |
| `resources/vosk-models/c611af...-vosk-model-small-ru-0.22.zip` (45М) | **Русская Vosk STT модель small 0.22** | 🟠 Нужно если хочешь офлайн STT | Без неё скачает при первом запуске (требует инет) |

Оба файла — большие бинарники, исключены в `.gitignore` (`*.pt`), но в репо лежат для Docker. Можно удалить если экономишь место и готов качать.

---

## `scripts/`

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `scripts/collect_and_show_coverage.sh` | Запуск `coverage run -m unittest discover` + `coverage html` | 🟡 Да | Не посмотришь покрытие |

---

## `esp32-client/` — прошивка для ESP32

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `esp32-client/README.md` | Описание ESP32 клиента | 🟢 Да если нет ESP32 |
| `esp32-client/img/schematics-dumb.svg` | Схема подключения | 🟢 Да |
| `esp32-client/irene-esp32-arduino-client/README.md` | Инструкция по прошивке | 🟢 Да |
| `*.ino` (`irene-esp32-arduino-client.ino`) | **Главный скетч Arduino** | 🟢 Да если нет ESP32 |
| `audio_capture.cpp/.h` | Захват I2S микрофона | 🟢 |
| `audio_playback.cpp/.h` | Проигрывание I2S динамика | 🟢 |
| `config.h` | WiFi/сервер настройки | 🟢 |
| `websocket_connection.cpp/.h` | WebSocket к `/api/face_web/ws` | 🟢 |
| `protocol_negotiation.cpp/.h` | Согласование `negotiate/request` | 🟢 |
| `state.cpp/.h`, `wifi_connection.*`, `interval.h`, `logging.h`, `debug.*`, `esp32.svd` | Состояния, WiFi, логи | 🟢 |

**Целиком `esp32-client/` — опционально.** Можно удалить если не используешь ESP32 железо. На сервер не влияет никак.

---

## `frontend/` — веб-интерфейс (Vue 3 + XState + Vite)

### Корень frontend

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `frontend/package.json` | **Зависимости фронта** (vue, xstate, axios, zod, vite) | 🔴 Нет | `npm ci` не поставит пакеты |
| `frontend/package-lock.json` | Лок версий (286К) | 🔴 Нет для `npm ci` | `npm ci` упадёт, `npm install` пересоздаст |
| `frontend/vite.config.ts` | **Конфиг Vite** (alias `@`, proxy `/api → 8086`, manualChunks) | 🔴 Нет | `npm run build`/`dev` сломается |
| `frontend/index.html` | HTML шаблон | 🔴 Нет | Vite не соберёт |
| `frontend/tsconfig.json` / `tsconfig.config.json` | Конфиг TypeScript | 🟡 Да | `vue-tsc --noEmit` сломается, сборка может пройти |
| `frontend/.eslintrc.cjs` | Конфиг ESLint | 🟡 Да | Линт сломается |
| `frontend/.gitignore` | Игнор `node_modules`, `dist` | 🟢 Да | Мусор в git |
| `frontend/.env.development` | Переменные Vite dev | 🟢 Да | Dev режим без них |
| `frontend/env.d.ts` | Типы для `*.vue` | 🟡 Да | TS будет ругаться |
| `frontend/README.md` | Дока фронта (Vite) | 🟢 Да |
| `frontend/public/favicon.ico` | Иконка | 🟢 Да | Без иконки |
| `frontend/.vscode/extensions.json` | Рекомендуемые расширения VS Code | 🟢 Да |

### `frontend/src/`

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `src/main.ts` | Точка входа Vite → вызывает `initApplication()` | 🔴 Нет |
| `src/main.css` | Глобальные стили | 🟠 Нет | Без стилей UI поедет |
| `src/App.vue` | Корневой компонент + роутер | 🔴 Нет |
| `src/app.ts` | **Инициализация приложения** (zod FrontendConfig, getProtocolRequirements, 7 xstate машин, router /#/config/#/about) | 🔴 Нет | Фронт не стартанёт |
| `src/audio-input-streaming/audioStreamWsService.ts` | WebSocket для PCM стрима (`?sample_rate=44100`) | 🟠 Нужно если `in.stt.serverside` | Серверный STT не заработает |
| `src/audio-input-streaming/sm.ts` | XState машина стриминга (ждёт `in.stt.serverside/ready`) | 🟠 |
| `src/audio-input-streaming/streamingService.ts` | Проверка `streamingSupported` (MediaStream + AudioWorklet) | 🟠 |
| `src/components/eventBus.ts` | **Шина событий между машинами** (`busConnector`) | 🔴 Нет | Все машины ослепнут |
| `src/components/wakeLock.ts` | Запрет гашения экрана | 🟢 Да | Экран будет гаснуть |
| `src/components/about/AboutPage.vue` | Страница «О программе» | 🟢 Да | Пропадёт /about |
| `src/components/config/ConfigEditPanel.vue` | Редактор YAML/JSON (vue3-json-editor) | 🟠 Нужно если хочешь настройки в браузере | Не отредактируешь конфиги через UI |
| `src/components/config/ConfigsPage.vue` | Страница /config | 🟠 |
| `src/components/config/service.ts` | `fetchConfig()` REST `/api/config` | 🟠 |
| `src/components/config/sm.ts` | XState для конфигов | 🟠 |
| `src/components/dialog/DialogPage.vue` | **Главная страница диалога** | 🔴 Нет |
| `src/components/dialog/Message.vue` | Рендер сообщения (markdown) | 🔴 Нет |
| `src/components/dialog/messages.ts` | Типы + zod схемы сообщений | 🔴 Нет |
| `src/components/dialog/sm-connection.ts` | **XState WebSocket** (`/api/face_web/ws`, negotiate, reconnect 1s) | 🔴 Нет | Не подключится к серверу |
| `src/components/dialog/sm-helpers.ts` | `eventNameForMessageType/type` | 🔴 Нет |
| `src/components/dialog/sm-input-text.ts` | Отправка `in.text-direct/indirect/text` | 🔴 Нет | Не отправишь текст |
| `src/components/dialog/sm-message-history.ts` | История `HISTORY_ADD_MESSAGE` | 🔴 Нет | Не увидишь историю |
| `src/components/dialog/sm-output-audio.ts` | `out.audio.link` → `new Audio(url)` + `playback-progress/done` | 🟠 Нужно если аудио вывод | Не услышишь ответы |
| `src/components/dialog/sm-output-plaintext.ts` | `out.text-plain/text` → история | 🔴 Нет | Не увидишь текст |
| `src/components/shared/ConnectionStatus.vue` | Индикатор соединения | 🟢 Да |
| `src/components/shared/Header.vue` | Шапка | 🟢 Да |
| `src/components/shared/MicrophoneStatus.vue` | Индикатор микрофона | 🟢 Да |
| `src/components/ui/Container.vue`, `Header.vue`, `HeaderTitle.vue` | UI примитивы | 🟢 Да | UI поедет но работать будет |
| `src/local-recognizer/recognizerWorklet.js` | **AudioWorklet** ресемплер для Vosk | 🟠 Нужно если `in.stt.clientside` | Клиентский STT сломается |
| `src/local-recognizer/sm.ts` | XState клиентского Vosk (`WS_READY(in.stt.clientside)`) | 🟠 |
| `src/local-recognizer/voskService.ts` | Загрузка `vosk-browser` модели | 🟠 |
| `src/stub/vue3-markdown-it.d.ts` | Заглушка типов для markdown | 🟡 Да | TS ругнётся |

**Итого по frontend:** `src/app.ts` + `sm-connection.ts` + `eventBus.ts` критичны. Остальные — по фичам (отключаются через `audioInputEnabled/audioOutputEnabled` в `app.ts`).

`frontend/dist/` (генерируется `npm run build`) — 🔵 можно удалить, пересоздастся. Игнорится в git.

---

## `handbook/` — справочники для AI/людей (созданы в этой сессии)

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `handbook/README.md` | Индекс справочников | 🟢 Да |
| `handbook/00_overview.md` | Карта репо, техстек, точки входа | 🟢 Да |
| `handbook/01_plugin_system.md` | Система плагинов, MagicPlugin, операции | 🟢 Да |
| `handbook/02_brain.md` | Brain, контексты, VACommandTree | 🟢 Да |
| `handbook/03_config_cli.md` | Конфиги, CLI, Docker | 🟢 Да |
| `handbook/04_web_protocol.md` | WebSocket протокол | 🟢 Да |
| `handbook/05_frontend.md` | Фронт архитектура | 🟢 Да |
| `handbook/06_faces_tts_stt.md` | Faces, TTS/STT | 🟢 Да |

Все `handbook/` — **только доки**, на рантайм не влияют, можно удалить после чтения.

---

## `irene/` — ядро бэкенда

### Корень `irene/`

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `irene/__init__.py` | Экспорт `construct_context`, констант, проверка версии | 🔴 Нет |
| `irene/__main__.py` | **Точка входа** (`register_variable irene_path/irene_home → launch_application` с 5 core плагинами) | 🔴 Нет | `python -m irene` не запустится |
| `irene/py.typed` | Маркер PEP 561 для mypy | 🟡 Да | mypy не увидит типы |

### `irene/brain/` — логика диалога

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `brain/__init__.py` | Реэкспорт | 🔴 Нет |
| `brain/abc.py` | **Базовые типы** (Brain, VAApi, VAApiExt, InboundMessage, OutputChannelPool) | 🔴 Нет | Всё сломается |
| `brain/brain.py` | `BrainImpl` + `CompositeOutputPool`, `_VAApiProvider` | 🔴 Нет |
| `brain/brain_plugin.py` | **BrainPlugin** (triggerPhrases `ирина`, defaultTimeout 10с, сборка дерева команд) | 🔴 Нет | Мозг не создастся |
| `brain/canonical_text.py` | `convert_to_canonical` (lower, без пунктуации) | 🔴 Нет | Команды не матчились |
| `brain/command_tree.py` | `VACommandTree` (варианты `\|`, fuzzy tolerance 2) | 🔴 Нет |
| `brain/context_manager.py` | `VAContextManager` + `TimeoutTicker` (Lock, tick 1с) | 🔴 Нет |
| `brain/contexts.py` | **Все контексты** (FunctionContext, GeneratorContext, TriggerPhrase, Interrupt) | 🔴 Нет |
| `brain/inbound_messages.py` | `PlainTextMessage`, `PartialTextMessage` | 🔴 Нет |
| `brain/output_pool.py` | `CompositeOutputPool`, `OutputPoolImpl`, `query_channels` | 🔴 Нет |
| `brain/active_interaction.py` | `construct_active_interaction` (для `submit_active_interaction`) | 🔴 Нет |
| `brain/tests/*` (9 файлов) | Тесты мозга | 🟡 Да | Не запустишь `unittest discover` для мозга |

### `irene/plugin_loader/` — система плагинов

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_loader/__init__.py` | — | 🔴 Нет |
| `plugin_loader/abc.py` | `Plugin`, `OperationStep`, `PluginManager`, `DependencyCycleException` | 🔴 Нет |
| `plugin_loader/magic_plugin.py` | **MagicPlugin** + декораторы `@operation/@after/@before/@step_name` | 🔴 Нет |
| `plugin_loader/plugin_manager.py` | `PluginManagerImpl` (TopologicalSorter) | 🔴 Нет |
| `plugin_loader/launcher.py` | **Запускатор** (argparse, bootstrap→init→run→terminate, SIGINT) | 🔴 Нет |
| `plugin_loader/file_patterns.py` | Переменные `{irene_home}` etc, `match_files`, `substitute_pattern` | 🔴 Нет |
| `plugin_loader/run_operation.py` | `call_all`, `call_all_as_wrappers`, `call_all_parallel_async` | 🔴 Нет |
| `plugin_loader/errors.py` | Исключения | 🔴 Нет |
| `plugin_loader/core_plugins/config.py` | **ConfigPlugin** (YAML/JSON, watch 30с, snapshot_hash) | 🔴 Нет | Конфиги не загрузятся |
| `plugin_loader/core_plugins/logging.py` | LoggingPlugin | 🟠 Нужно | Без логов ослепнешь, но запустится |
| `plugin_loader/core_plugins/plugin_discovery.py` | Поиск `plugin_*.py` по шаблонам | 🔴 Нет | Не найдёт плагины |
| `plugin_loader/utils/snapshot_hash.py` | Хеш снапшотов конфигов | 🔴 Нет |
| `plugin_loader/tests/*` | Тесты загрузчика | 🟡 Да |
| `plugin_loader/utils/tests/*` | Тесты хеша | 🟡 Да |
| `plugin_loader/core_plugins/__init__.py`, `irene/plugin_loader/__init__.py` | — | 🔴 Нет |

### `irene/constants/` — константы языка

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `constants/gender.py` | `MALE/FEMALE` | 🟠 Нужно для voice_profiles |
| `constants/languages.py` | Коды языков (RU/EN...) | 🟠 Нужно для переводчика/TTS |
| `constants/numerals_ru.py`, `time_units_ru.py`, `word_forms.py`, `labels.py` | Склонения, единицы времени | 🟠 Нужно для `pronounce_*` | Без них время/числа криво склоняются |

Можно удалить если не используешь русскую озвучку.

### `irene/face/` — абстракции ввода/вывода

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `face/__init__.py` | — | 🔴 Нет |
| `face/abc.py` | `TTS`, `FileWritingTTS`, `ImmediatePlaybackTTS`, `LocalInput`, `MuteGroup` | 🔴 Нет |
| `face/mute_group.py` | `MuteGroupImpl` (счётчик mute) | 🔴 Нет | Микрофон не заглушится при TTS |
| `face/tts_helpers.py` | Хелперы выбора TTS | 🔴 Нет |
| `face/tests/test_mute_group.py` | Тест | 🟡 Да |

### `irene/compatibility/` — поддержка старых плагинов

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `compatibility/compatibility_plugin.py` | Загрузчик плагинов оригинальной Ирины | 🟢 Да если не используешь старые плагины формата `start(vacore)` |
| `compatibility/vacore.py` | Совместимость с `vacore.py` | 🟢 Да |
| `compatibility/__init__.py` | — | 🟢 Да |

Можно удалить целиком если не нужны старые плагины.

### `irene/config_templates/`

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `config_templates/console/README.txt` | Описание шаблона console | 🟢 Да |
| `config_templates/console/discover_plugins.yaml` | Пути для `python -m irene -T console` | 🟠 Нужно если используешь `-T console` |
| `config_templates/console/face_console.yaml` | Конфиг консоли | 🟠 |

### `irene/embedded_plugins/` — встроенные команды

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_greetings.py` | Команда «привет» | 🟢 Да | Потеряешь привет |
| `plugin_time.py` | «сколько времени» (`pronounce_time_ru`) | 🟢 Да |
| `plugin_date.py` | «какая дата» | 🟢 Да |
| `plugin_random.py` | «брось монету/кость» | 🟢 Да |
| `plugin_gamemoreless.py` | Игра «больше меньше» (генератор) | 🟢 Да |
| `plugin_timer.py` | Таймер (`timer.wav` + active_interaction) | 🟢 Да |
| `plugin_tts_silero_v3.py` | **Движок Silero V3** (torch) | 🟠 Нужно если хочешь Silero | Без него только pyttsx/bark |
| `plugin_tts_pyttsx.py` | Движок pyttsx3 (не в Docker) | 🟢 Да |
| `plugin_tts_bark.py` | Движок Bark | 🟢 Да |
| `plugin_tts_cache.py` | Кэш `say_to_file` по хешу | 🟢 Да | Медленнее синтез |
| `plugin_voice_profiles.py` | Профили голосов (язык/гендер) | 🟠 Нужно для мультиязычности | Без него TTS без выбора голоса |
| `plugin_voiceover.py` | Выбор TTS через `get_tts` | 🔴 Нет если используешь TTS | Без него TTS не выберется |
| `plugin_vosk_model_loader.py` | Загрузка/распаковка Vosk zip | 🔴 Нет если используешь Vosk | STT не загрузит модель |
| `plugin_audio_converter_ffmpeg.py` / `plugin_audio_converter_soundfile.py` | Конвертация аудио (ogg→wav) | 🟠 Нужно для Telegram/аудио | Без них не сконвертит голосовые |
| `plugin_command_aliases.py` | Алиасы команд | 🟢 Да |
| `plugin_face_console.py` | Консольный face (aioconsole) | 🟢 Да если не используешь `-T console` |
| `plugin_global_mute_group.py` | Глобальный MuteGroup | 🔴 Нет | `in.mute` сломается |
| `plugin_notification_api.py` | REST `/api/notification` для внешних пушей | 🟢 Да |
| `media/timer.wav` | Звук таймера (ПИИИК) | 🟢 Да если удалил таймер |
| `tests/*` (5 файлов) | Тесты алиасов/времени и т.д. | 🟡 Да |

Каждый `plugin_*.py` можно удалять отдельно — теряешь только его фичу, остальное работает.

### `irene/utils/` — утилиты

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `utils/num_to_text_ru.py` | `num2text(42)` → «сорок два» (склонения) | 🟠 Нужно для времени/даты |
| `utils/all_num_to_text.py` | Числа в тексте → слова | 🟠 |
| `utils/pronounce_numbers_ru.py` / `pronounce_time_ru.py` | Озвучка чисел/времени | 🟠 |
| `utils/audio_converter.py` | Абстракция `AudioConverter` | 🟠 |
| `utils/predicate.py` / `metadata.py` / `mapping_match.py` | `Predicate`, `MetaMatcher`, фильтры каналов | 🔴 Нет | `get_channels` сломается |
| `utils/executable_files.py` | Поиск исполняемых файлов | 🟢 Да |
| `utils/probabilistic_flag.py` | Флаг с вероятностью | 🟢 Да |
| `utils/tests/*` + `snapshots/*` | Тесты + снапшоты | 🟡 Да |

### `irene/test_utuls/` (опечатка в названии — `utuls`)

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `test_utuls/context_mock.py`, `dialogtestcase.py`, `plugin_test_case.py`, `stub_text_message.py` | Хелперы для тестов плагинов | 🟡 Да | Тесты плагинов не запустятся |

---

## `irene_plugin_*` — внешние плагины (каждый — отдельный пакет)

### `irene_plugin_web_face/` — **критично для веб-режима**

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_web_face.py` | **WebSocket `/api/face_web/ws` + negotiate** (`_ConnectionImpl`) | 🔴 Нет для веб-режима | Веб не подключится |
| `plugin_web_server.py` | **Uvicorn сервер** (`face_web_server.yaml` host/port/ssl) | 🔴 Нет | Сервер не стартанёт |
| `plugin_text_io.py` | `in.text-direct/indirect` + `out.text-plain` | 🔴 Нет | Текст не уйдёт |
| `plugin_in_stt_clientside.py` | `in.stt.clientside` (Vosk в браузере) | 🟠 Нужно если клиентский STT | Без него браузерный Vosk не работает |
| `plugin_in_stt_serverside.py` | `in.stt.serverside` (PCM → Vosk на сервере, доп WS `?sample_rate`) | 🟠 Нужно если серверный STT | Потоковый ввод сломается |
| `plugin_audio_out_link.py` | `out.audio.link` (временные URL `/api/plugin_audio_out_link/*.wav`) | 🔴 Нет если нужен звук | Аудио не проиграется |
| `plugin_out_tts_serverside.py` | `out.tts.serverside` (TTS → file → audio_link) | 🔴 Нет если TTS в браузере | Озвучка в браузере пропадёт |
| `plugin_mute_protocol.py` | `in.mute` (mute/unmute) | 🟠 Нужно для микрофона | Эхо от TTS |
| `plugin_expose_vosk_model.py` | Отдаёт модель для `vosk-browser` (`/api/plugin_expose_vosk_model/*`) | 🟠 Нужно для клиентского Vosk | Браузер не скачает модель |
| `plugin_web_face_auth.py` | Аутентификация WS/REST | 🟢 Да если без авторизации |
| `protocol.py` | **Константы всех типов сообщений** (`MT_*`, `PROTOCOL_*`) | 🔴 Нет | Импорты упадут |
| `abc.py` | `Connection`, `ProtocolHandler` | 🔴 Нет |

Без `irene_plugin_web_face` веб-интерфейс полностью не работает. Можно удалить только если используешь только Telegram/консоль.

### `irene_plugin_web_face_frontend/`

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_web_face_frontend.py` | **Раздача `frontend/dist` + `custom-styles.css`** (`StaticFiles`, fallback `index.html`) | 🔴 Нет для веб-режима | Откроешь `/` — 404 |

Ищет `frontend/dist` или `frontend-dist`. Без сборки фронта — 404.

### `irene_plugin_local_speech_face/` — локальный микрофон/динамик

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_local_speech_face.py` | Оркестратор `face_local` (`input` + `outputs` из yaml) | 🟠 Нужно если локальный звук |
| `plugin_local_input_sounddevice_vosk.py` | `vosk+sounddevice` (микрофон → Vosk) | 🟠 |
| `plugin_local_output_sounddevice.py` | `sounddevice` вывод | 🟠 |
| `plugin_local_output_tts.py` | `tts` вывод через `voice_profiles` | 🟠 |

Целиком можно удалить если используешь только веб/Telegram. Требует `sounddevice` + `vosk`.

### `irene_plugin_telegram_face/` — Telegram бот

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_telegram_face.py` | Основа, `pyTelegramBotAPI` | 🟠 Нужно если Telegram |
| `plugin_telegram_auth.py` | `allowed_users` | 🟢 Да | Бот будет для всех |
| `plugin_telegram_plaintext_io.py` | Текст `in.text-direct` | 🟠 |
| `plugin_telegram_audio_input.py` | Голосовые ogg → vosk | 🟢 Да | Только текст |
| `plugin_telegram_audio_output.py` | TTS → ogg → отправка | 🟢 Да |
| `inbound_messages.py` / `outputs.py` / `utils.py` | Адаптеры | 🟠 |

Целиком можно удалить если не нужен Telegram. Требует `pyTelegramBotAPI`.

### `irene_plugin_llm/` — LLM (опционально)

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_llm_ollama.py` / `plugin_llm_openai.py` | LLM бэкенды | 🟢 Да если без LLM |
| `plugin_llm_fallback_context.py` | Fallback когда команда не распознана → LLM | 🟢 |
| `plugin_ai_skill_datetime.py` / `plugin_ai_skill_timer.py` | Скиллы для function calling | 🟢 |
| `requirements.txt` | Зависимости LLM (openai, ollama) | 🟢 |
| `README.md` | Дока LLM | 🟢 |

Целиком можно удалить если не используешь LLM. Не входит в Docker по умолчанию.

### `irene_plugin_translate/`

| Файл | Назначение | Удалить? |
|------|------------|----------|
| `plugin_translate.py` | Команда «как по-английски будет...» | 🟢 Да |
| `plugin_translation_provider_libretranslate.py` | LibreTranslate провайдер | 🟢 |
| `translation_provider.py` | Абстракция | 🟢 |

Можно удалить если не нужен перевод.

---

## Системные/служебные (не удалять)

| Файл/папка | Назначение | Удалить? |
|------------|------------|----------|
| `.git/` | История git | ⚪ Не трогать | Потеряешь историю, сломаешь `git` |
| `.github/workflows/*` (5 yml: tests, mypy, pep8, docker-image, docker-image-release) | CI GitHub Actions | 🟡 Да | CI не запустится, локально не влияет |
| `irene/__pycache__/*` (`*.cpython-312.pyc` 4+4 файлов) | Кэш байткода | 🔵 Да | Пересоздастся при следующем `python -m irene` |
| `nul` | Артефакт `> nul` | ⚪ Да — удалить | Мусор |

---

## Итоговая шпаргалка: что можно смело удалить

**Безопасно (освободишь место, ничего не сломается если фича не нужна):**
- `nul` — мусор, удалить сразу
- `handbook/` — только доки для AI (7 файлов), ~30КБ
- `esp32-client/` — целиком если нет ESP32
- `irene_plugin_llm/` — если без LLM
- `irene_plugin_translate/` — если без перевода
- `irene_plugin_telegram_face/` — если без Telegram
- `irene_plugin_local_speech_face/` — если без локального микрофона
- `irene/compatibility/` — если не нужны старые плагины
- `irene/brain/tests/`, `irene/plugin_loader/tests/`, `irene/utils/tests/`, `irene/face/tests/`, `irene/embedded_plugins/tests/` — тесты (жёлтые)
- `irene/test_utuls/` — хелперы тестов
- `scripts/` — coverage
- `doc/img/web_screens.jpg` — картинка
- `.github/` — CI
- `__pycache__` / `*.pyc` — кэш

**Опасно (сломается):**
- `irene/__main__.py`, `irene/brain/`, `irene/plugin_loader/`, `irene/face/`, `irene/constants/` (часть критична)
- `irene_plugin_web_face/` + `irene_plugin_web_face_frontend/` — без них нет веба
- `frontend/src/app.ts`, `frontend/src/components/dialog/sm-connection.ts`, `frontend/src/components/eventBus.ts` — без них фронт мёртв
- `frontend/package.json`, `vite.config.ts`, `index.html` — не соберёшь фронт
- `requirements.txt` / `requirements-docker.txt` — не поставишь deps
- `Dockerfile` — не соберёшь образ
- `resources/silero-models/*.pt` / `vosk-models/*.zip` — если нужен офлайн

**Подсчёт:** из ~210 файлов (без .git/__pycache__) — ~120 критичны, ~40 опциональны по фичам, ~30 тесты/доки, ~20 — генерируются.

> **Рекомендация для «чистой» установки:** оставь `irene/`, `irene_plugin_web_face*`, `frontend/`, `docker-config/`, `resources/`, `install.*`, `requirements*.txt`, `README.md`, `LICENSE`. Всё остальное — по желанию. Для прод Docker достаточно `Dockerfile` + `resources` + `docker-config`.
