# 00 — Обзор проекта

## Что это
Форк [Irene Voice Assistant](https://github.com/janvarev/Irene-Voice-Assistant) — локальный голосовой ассистент. Работает офлайн (Vosk + Silero), имеет веб-интерфейс, Telegram-бота, локальный микрофон/динамики, ESP32-клиент.

## Техстек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.9+, FastAPI, Uvicorn, WebSockets, asyncio + ThreadPoolExecutor |
| Распознавание | vosk 0.3.7, vosk-browser (фронт) |
| Синтез | Silero V3 (torch 1.12.1), pyttsx3, rhvoice, bark |
| Фронт | Vue 3.2, TypeScript 4.7, Vite 3, XState 4.33, vue-router 4, axios, zod, unplugin-icons |
| Инфра | Docker (python:3.9-slim-bullseye + node:16 builder), openssl самоподписанный cert |
| Тесты | pytest, time_machine, snapshottest, mypy, pep8 |

## Структура репозитория

```
irene/                          # ядро (ядро-плагины + brain + face + utils)
  __main__.py                   # точка входа: регистрирует переменные irene_path/irene_home → launch_application
  brain/                        # логика диалога (см. 02_brain.md)
  plugin_loader/                # система плагинов (см. 01_plugin_system.md)
  face/                         # абстракции TTS / LocalInput / MuteGroup
  embedded_plugins/             # встроенные плагины (14 шт)
  constants/                    # gender, languages, numerals_ru, time_units_ru, word_forms
  compatibility/                # загрузчик плагинов оригинальной Ирины
  config_templates/             # шаблоны конфигов (console)
  utils/                        # num_to_text_ru, pronounce_*, all_num_to_text, audio_converter, predicate
irene_plugin_web_face/          # WebSocket face + все протоколы in.* / out.*
irene_plugin_web_face_frontend/ # раздача собранного frontend/dist через FastAPI
irene_plugin_local_speech_face/ # локальный микрофон/динамик (sounddevice)
irene_plugin_telegram_face/     # Telegram bot face
irene_plugin_llm/               # LLM (ollama, openai) + скиллы
irene_plugin_translate/         # переводчик (libretranslate)
frontend/                       # Vue-приложение
  src/app.ts                    # initApplication, getProtocolRequirements, provide всех машин
  src/components/dialog/        # 7 state machines (sm-*.ts) + DialogPage.vue
  src/audio-input-streaming/    # серверный STT поток (streamingService)
  src/local-recognizer/         # клиентский STT (voskService + recognizerWorklet.js)
  vite.config.ts                # alias @, proxy /api -> 8086, manualChunks config-page
docker-config/                  # 4 yaml по-умолчанию (discover, face_web_server, silero, vosk)
resources/                      # silero модель *.pt, vosk-модели (пусто по-умолчанию)
esp32-client/                   # Arduino клиент (WebSocket + audio_capture/playback)
_orig/                          # архив оригинальной Ирины (mic_client, vacore.py, plugins/*)
doc/                            # client-server-protocol.md, local-face.md, plugin-dev-guide.md
frontend/dist → копируется в irene_plugin_web_face_frontend/frontend-dist/ при Docker build
```

## Точки входа

| Команда | Что делает |
|---------|------------|
| `python -m irene` | Обычный запуск (web + telegram + local если настроены) |
| `python -m irene -T console` | Консольный режим (перепишет часть конфигов) |
| `python -m irene --help` | Покажет все CLI аргументы от плагинов |
| `python -m irene --asyncio-debug -w 4` | Дебаг asyncio + 4 воркера |
| Docker `ENTRYPOINT ["python","-m","irene","--default-config","/home/python/config"]` | В контейнере |

## Важные файлы быстро

- `irene/__main__.py:10-20` — 5 core-плагинов: `ConfigPlugin, PluginDiscoveryPlugin, LoggingPlugin, BrainPlugin, OriginalCompatibilityPlugin`
- `frontend/src/app.ts` — `FrontendConfig` (zod), `getProtocolRequirements()` — какие протоколы запросить
- `irene/brain/brain_plugin.py` — `triggerPhrases` по-умолчанию `["ирина","ирины","ирину"]`
- `irene_plugin_web_face/protocol.py` — константы всех типов сообщений
- `irene/plugin_loader/file_patterns.py` — переменные `{irene_home}`, `{irene_path}`, `{user_home}`, `{python_path}`
- `requirements.txt` vs `requirements-docker.txt` — второй для Docker (без pyttsx3? см. Dockerfile)
- `Dockerfile` — 3 stages: frontend-builder (node) → ssl-generator → python:3.9-slim (копирует frontend/dist, resources, ssl)

## Где искать что

| Хочу ... | Иди в ... |
|----------|-----------|
| Добавить голосовую команду | `irene/embedded_plugins/plugin_*.py` пример `plugin_time.py` |
| Добавить TTS движок | `irene/face/abc.py` + `plugin_tts_*.py` |
| Поменять логику триггер-фразы | `irene/brain/brain_plugin.py:add_trigger_phrase` |
| Поменять приоритет команд | `irene/brain/command_tree.py:VACommandTree` |
| Добавить REST endpoint | операция `register_fastapi_endpoints` (см. `plugin_web_server.py`) |
| Поменять порт/SSL | `config/face_web_server.yaml` или `irene_plugin_web_face/plugin_web_server.py:config` |
| Починить микрофон в Docker | `--device /dev/snd --group-add audio` (doc/local-face.md) |
| Понять почему фронт не коннектится | `frontend/src/components/dialog/sm-connection.ts` → путь `/api/face_web/ws` |
