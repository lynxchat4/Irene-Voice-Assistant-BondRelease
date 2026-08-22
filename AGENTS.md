# AGENTS — инструкция для AI-агентов

> Этот файл — входная точка для любого AI-ассистента (Muse, Codex, Pi, Cursor) работающего с репозиторием LAVA.

## Что делать перед любой задачей

1. Прочти `handbook/README.md` — индекс справочников.
2. Открой нужный справочник из `handbook/` (таблица ниже).
3. Только потом лезь в исходники.

## Справочники

| # | Файл | Когда открывать |
|---|------|-----------------|
| 0 | `handbook/00_overview.md` | Не знаешь где файл / что за проект |
| 1 | `handbook/01_plugin_system.md` | Пишешь/чинишь плагин, операции, `MagicPlugin`, порядок шагов |
| 2 | `handbook/02_brain.md` | Команды, контексты, `VACommandTree`, `VAApi`, таймауты, диалоги |
| 3 | `handbook/03_config_cli.md` | Конфиги, CLI, Docker, переменные `{irene_home}` |
| 4 | `handbook/04_web_protocol.md` | WebSocket, `negotiate`, все `PROTOCOL_*`, REST |
| 5 | `handbook/05_frontend.md` | Vue/XState, `app.ts`, `sm-*.ts`, сборка Vite |
| 6 | `handbook/06_faces_tts_stt.md` | TTS/STT, faces, голоса, ESP32, audio converters |

## Правила

- Не ищи по всему репо `grep` если ответ есть в справочнике — экономь время.
- После изменения архитектуры/протокола/плагина — **обнови соответствующий handbook**.
- Пути проекта: `d:/умный-дом/LAVA/Local-AI-Voice-Assistant-LAVA/` (Windows, с дефисом и кириллицей — экранируй в bash).
- Язык проекта — русский (комментарии/док-строки), код — Python 3.9 + TypeScript 4.7 + Vue 3.

## Быстрые команды

```bash
# запуск
python -m irene --help
cd frontend && npm ci && npm run build

# тесты
pytest irene/brain/tests
mypy irene
```
