# Справочники проекта LAVA (Irene Voice Assistant)

> Папка создана чтобы **не искать каждый раз** как что работает. Читай этот индекс первым, потом нужный файл.

## Карта справочников

| Файл | Что внутри | Когда открывать |
|------|------------|-----------------|
| [00_overview.md](./00_overview.md) | Карта репозитория, техстек, точки входа, где что лежит | Первый раз / ищешь файл |
| [01_plugin_system.md](./01_plugin_system.md) | `plugin_loader`, `MagicPlugin`, операции/шаги, `TopologicalSorter`, `file_patterns` | Пишешь/дебажишь плагин |
| [02_brain.md](./02_brain.md) | `Brain`, `VAContextManager`, `VACommandTree`, контексты, `VAApi`, сообщения | Работа с командами/диалогами |
| [03_config_cli.md](./03_config_cli.md) | `ConfigPlugin`, YAML/JSON, CLI `-c -d -T -L`, переменные `{irene_home}` | Настройки, запуск, Docker |
| [04_web_protocol.md](./04_web_protocol.md) | WebSocket `/api/face_web/ws`, `negotiate/*`, все `PROTOCOL_*`, `Connection` | Клиент-сервер, WebSocket, ESP32 |
| [05_frontend.md](./05_frontend.md) | Vue3 + XState + Vite, `app.ts`, все `sm-*.ts`, `audioStreamWsService` | Фронт, сборка, state machines |
| [06_faces_tts_stt.md](./06_faces_tts_stt.md) | Faces (web/telegram/local/console), TTS/STT, `voice_profiles`, `MuteGroup` | Аудио ввод/вывод,TTS,STT |

## Быстрые ответы

- **Запуск из исходников:** `pip install -r requirements.txt` → `cd frontend && npm ci && npm run build` → `python -m irene` (см. `03_config_cli.md`)
- **Запуск Docker:** `docker run --publish 8086:8086 -v $HOME/irene:/irene alexeybond/irene` (см. `03_config_cli.md`)
- **Добавить команду:** `define_commands = {"привет": handler}` в `plugin_*.py` (см. `01_plugin_system.md` + `02_brain.md`)
- **Добавить WebSocket-протокол:** операция `init_client_protocol` (см. `04_web_protocol.md`)
- **Фронт не собирается:** `frontend/vite.config.ts` proxy `/api -> localhost:8086` (см. `05_frontend.md`)
- **TTS не говорит:** проверь `voice_profiles` + `plugin_tts_silero_v3` (см. `06_faces_tts_stt.md`)

## Соглашения для AI-агента

1. Перед правкой — прочти соответствующий файл справочника.
2. После изменения архитектуры — обнови справочник.
3. Пути в Windows: `d:/умный-дом/LAVA/Local-AI-Voice-Assistant-LAVA/...` — экранируй при `bash`.

> Все файлы в `handbook/` — синтетические знания, не генерируются автоматически. Источник — чтение исходников на 2026-08-21.
