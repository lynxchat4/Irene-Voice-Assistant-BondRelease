# 03 — Конфигурация, CLI, переменные путей

## Переменные путей (`irene/plugin_loader/file_patterns.py`)

| Переменная | Значение | Где задаётся |
|------------|----------|--------------|
| `{irene_path}` | `dirname(irene/__init__.py)` | `__main__.py: register_variable` |
| `{irene_home}` | `$IRENE_HOME` или `~/irene` | `__main__.py` |
| `{user_home}` | `Path.home()` | `file_patterns.py` |
| `{python_path}` | каждый элемент `sys.path` | `file_patterns.py` (перебирает все) |

Используются в `plugin_paths`, `config_dir`, `default_config_paths`. Функции: `substitute_pattern(pattern)` → `Iterable[str]` (разворачивает `python_path` во все варианты), `match_files(patterns)` → `iglob`, `first_substitution`.

## CLI (`irene/__main__.py` + `ConfigPlugin` + `LoggingPlugin`)

```
python -m irene [-T <template>] [-L] [-c <config-dir>] [-d <default-config>]... [--asyncio-debug] [-w N]
```

| Флаг | Плагин | Описание |
|------|--------|----------|
| `-T/--config-template` | ConfigPlugin | Применить шаблон (заменит конфиги) |
| `-L/--list-config-templates` | ConfigPlugin | Список шаблонов |
| `-c/--config-dir` | ConfigPlugin | Папка конфигов, по-умолчанию `{irene_home}/config` |
| `-d/--default-config` | ConfigPlugin | Доп. папка дефолт-конфигов (можно несколько) |
| `--asyncio-debug` | launcher | `asyncio.run(debug=True)` |
| `-w/--executor-max-workers` | launcher | `ThreadPoolExecutor(max_workers)` |

`--default-config` в Docker: `/home/python/config` (см. Dockerfile ENTRYPOINT).

Порядок парсинга (`launcher.py`):
1. `parse_args(strict=False)` — нестрогий, чтобы собрать все `setup_cli_arguments`
2. `call_all(bootstrap)`
3. `parse_args(strict=True)` — строгий

Любой плагин может добавить аргументы через операцию `setup_cli_arguments(ap: ArgumentParser)` и прочитать через `receive_cli_arguments(args)`.

## ConfigPlugin (`irene/plugin_loader/core_plugins/config.py`)

### Конфиг самого ConfigPlugin

```python
config = {
  'yamlDumpOptions': {'default_flow_style':False,'encoding':'utf-8','allow_unicode':True},
  'fileEncoding': 'utf-8',
  'storeOnRESTUpdate': True,
  'storeOnShutdown': True,
  'watchFileChanges': True,
  'watchMemoryChanges': True,
  'watchIntervalSeconds': 30,
}
```

### Как работает

1. При старте для каждого плагина создаётся `ConfigurationScope(main_file_path, initial_value, plugin, comment)`:
   - `main_file_path` = `{config_dir}/{plugin.name}.yaml` (первый путь из substitute)
   - `initial_value` = копия `plugin.config`
   - `comment` = `plugin.config_comment`

2. `load_main_file` — читает YAML/JSON, мержит в `value`, считает `snapshot_hash`, запоминает `mtime`.

3. Дополнительные папки `default_config_paths` — `load_file` мержит поверх (дефолты < основные).

4. `notify_plugin` — вызывает `receive_config(config_dict)` у плагина (все шаги операции), запоминает хеш.

5. Watch-loop (30s):
   - `was_modified_on_disk` → перечитать файл → `notify_plugin`
   - `was_modified_in_memory` (сравнивает `snapshot_hash`) → `store_main_file` (пишет YAML с комментом)
   - Если изменены оба одновременно → приоритет у памяти.

6. REST API (см. `04_web_protocol.md` через `plugin_web_face`): `GET/PUT /api/config/*`, `storeOnRESTUpdate` триггерит запись.

7. При `terminate` если `storeOnShutdown` → запись всех.

### Шаблоны (`config_templates/`)

Папка `{irene_path}/config_templates/<name>/` содержит готовые YAML. CLI `-T console` копирует `config_templates/console/*` → `config_dir`. В репо есть только `console`.

### Добавление конфига в свой плагин

```python
name='my_plugin'; version='0.1.0'
config={'host':'0.0.0.0','port':1234}
config_comment="host — адрес\nport — порт"

def receive_config(cfg, *_a, **_kw):
    global _host; _host = cfg['host']  # вызывается при старте и каждом изменении

# Изменить на лету (сохранится если watchMemoryChanges=True):
config['port'] = 4321
```

**Правило:** не переназначать `config = {...}`, только `config[key]=val` или мутировать словарь.

### Логирование (`core_plugins/logging.py`)

Настраивает `logging` из `config/logging.yaml` либо дефолт. CLI может добавить флаг `--log-level`.

### Где лежат конфиги

| Запуск | Папка |
|--------|-------|
| Из исходников | `~/irene/config/` |
| `IRENE_HOME=/tmp/my` | `/tmp/my/config/` |
| Docker | `/irene/config` (volume) + `/home/python/config` (дефолты из `docker-config/`) |
| `docker-config/` | `discover_plugins.yaml`, `face_web_server.yaml`, `plugin_tts_silero_v3.yaml`, `vosk_model_loader.yaml` |

Пример `docker-config/face_web_server.yaml` содержит `host`, `port`, `ssl_certfile`, `ssl_keyfile`.

## Docker (`Dockerfile`)

```
Stage1 frontend-builder: node:16-alpine → npm ci → npm run build → /home/frontend/dist
Stage2 ssl-generator: python:3.9-slim → openssl req -x509 → cert.pem/key.pem
Stage3 runtime: python:3.9-slim-bullseye
  - apt: libportaudio2 libatomic1 libsndfile1-dev
  - user python:1001, mkdir /irene chown 1001
  - pip install -r requirements-docker.txt
  - COPY irene irene_plugin_* docker-config irene_plugin_web_face_frontend/frontend-dist resources ssl
  - EXPOSE 8086, VOLUME /irene, ENV IRENE_HOME=/irene
  - ENTRYPOINT python -m irene --default-config /home/python/config
```

Сборка: `docker build -t irene .` ; мультиарх: `docker buildx build --platform linux/amd64,linux/arm64`.

### Запуск

```bash
# стабильная
docker run --rm -it --publish 8086:8086 --user="$(id -u):$(id -g)" -v "$HOME/irene:/irene" alexeybond/irene:latest

# звук в контейнере (Linux)
docker run --device /dev/snd:/dev/snd --group-add audio ...

# зависимости для кастомных плагинов
docker run --entrypoint pip -v "$HOME/irene:/irene" --user="$(id -u):$(id -g)" alexeybond/irene install -t /irene/deps <pkg>
cat requirements.txt | docker run -i --entrypoint pip -v "$HOME/irene:/irene" alexeybond/irene install -t /irene/deps -r /dev/stdin
```

## requirements

- `requirements.txt` — полный (vosk, torch, sounddevice, telebot, fastapi, etc)
- `requirements-docker.txt` — урезаный для Docker (без pyttsx3? см. разницу)
- `requirements-ci.txt` — для CI (mypy, pep8)

Гибкость: можно удалить из `requirements.txt` ненужные (torch если не нужен Silero).
