# 01 — Система плагинов

## Ядро: `irene/plugin_loader/`

### Базовые типы (`abc.py`)

```python
class Plugin(ABC):
    name: str; version: str
    def get_operation_steps(op_name: str) -> Iterable[OperationStep]

class OperationStep(NamedTuple):
    step: Any; name: str; plugin: Plugin
    dependencies: Collection[str] = ()
    reverse_dependencies: Collection[str] = ()

class PluginManager(ABC):
    def get_operation_sequence(op_name: str) -> Iterable[OperationStep]  # топологически отсортировано
```

### MagicPlugin (`magic_plugin.py`)

Удобный базовый класс. **Любой публичный метод/атрибут** становится шагом операции:

```python
from irene.plugin_loader.magic_plugin import MagicPlugin, operation, after, before, step_name

class MyPlugin(MagicPlugin):
    name='my_plugin'; version='1.0.0'
    config = {'key':'val'}              # объявит конфиг (см. 03)
    config_comment="..."                # комментарий к YAML

    def init(self, pm): ...             # → операция "init", шаг "my_plugin.init"
    @operation('terminate')
    @after('kill_brain')                # выполнится после kill_brain
    def terminate(self): ...

    @operation('define_commands')
    def define_commands(self): return {"привет": handler}

    @before('construct_default')
    def my_wrapper(self, nxt, prev, pm, **kw): ...  # обёртка (call_all_as_wrappers)
```

Декораторы:
- `@operation('op')` — явно указать операцию (иначе имя метода = имя операции)
- `@after('a','b')` — зависимость (выполнится **после** a,b)
- `@before('x')` — обратная зависимость (x выполнится после текущего)
- `@step_name('my.step')` — кастомное имя шага (по-умолчанию `plugin.method`)

**Важно:** поля `name`/`version`/`__doc__` игнорируются при сканировании шагов (`_SPECIAL_ATTRS_RE`).

Два вида плагинов:
- `MagicPlugin` — класс
- `MagicModulePlugin` — обёртка над обычным `plugin_*.py` модулем (module.name/version/__doc__ читаются из переменных модуля)

### PluginManagerImpl (`plugin_manager.py`)

```python
pm = PluginManagerImpl(plugins)
seq = pm.get_operation_sequence('init')  # TopologicalSorter + CycleError -> DependencyCycleException
```

Дубли имени шага → warning, берётся первый. Цикл → исключение.

### Запуск (`launcher.py`)

```
launch_application(core_plugins, canonical_launch_command='python -m irene')
  ├─ parse_args(False) → setup_cli_arguments → receive_cli_arguments (нестрогий)
  ├─ call_all(bootstrap) — даёт плагинам шанс зарегистрировать клиенты
  ├─ parse_args(True) — строгий парсинг
  ├─ init (параллельно async, ThreadPoolExecutor) — await _run_with_interrupts
  ├─ run (параллельно, shield) — ждёт SIGINT/SIGTERM
  └─ terminate (параллельно) — отмена run-задач, ожидание
```

`_wait_for_interrupt` ставит handler на SIGINT/SIGTERM, на Windows — fallback через `signal.signal`. Периодически переустанавливает handler (каждые 1s, экспоненциально).

`call_all` / `call_all_as_wrappers` / `call_all_parallel_async` — из `run_operation.py`.

### Поиск плагинов (`core_plugins/plugin_discovery.py` + `file_patterns.py`)

По-умолчанию `discover_plugins.yaml`:
```yaml
plugin_paths:
  - "{irene_home}/plugins/plugin_*.py"
  - "{irene_home}/plugins/*/plugin_*.py"
  - "{python_path}/irene_plugin_*/plugin_*.py"
  - "{irene_path}/embedded_plugins/plugin_*.py"  # встроенные
```

Переменные в шаблонах (`file_patterns.py`):
- `{irene_path}` = `dirname(irene/__init__.py)`
- `{irene_home}` = `$IRENE_HOME` или `~/irene`
- `{user_home}` = `Path.home()`
- `{python_path}` = `sys.path` (перебирает все)

Функции: `match_files`, `pick_random_file`, `substitute_pattern`, `first_substitution`.

### Все операции (что можно реализовать в плагине)

| Операция | Сигнатура | Где используется |
|----------|-----------|------------------|
| `setup_cli_arguments` | `(ap: ArgumentParser)` | `launcher` + `config`, `logging` |
| `receive_cli_arguments` | `(args: Namespace)` | читает `config_dir`, `default_config_paths` |
| `bootstrap` | `(pm: PluginManager)` | ранняя инициализация |
| `init` | `(pm)` async/sync | создание ресурсов (Brain, WebServer, Vosk) |
| `run` | `(pm)` async/sync | долгоживущие задачи (uvicorn.serve) |
| `terminate` | `(pm)` | очистка |
| `receive_config` | `(config: dict)` | вызывается при изменении конфига |
| `define_commands` | `() -> dict` | `BrainPlugin.create_root_context` собирает дерево |
| `create_root_context` | `(nxt, prev:VAContext, pm)` wrapper | оборачивание корневого контекста |
| `construct_context` | `(nxt, prev:VAContextSource, pm)` wrapper | создание любого контекста |
| `get_brain` | `(nxt, prev:Brain\|None)` wrapper | переопределить Brain |
| `register_fastapi_routes` | `(app: FastAPI, pm)` | `plugin_web_server` |
| `register_fastapi_endpoints` | `(router: APIRouter, pm)` | добавить `/api/<plugin>/...` |
| `init_client_protocol` | `(prev:None, variant:str, conn:Connection, pm, mute_group)` wrapper | согласование WebSocket-протокола |
| `get_mute_group` | `(nxt, prev:MuteGroup\|None, pm, conn)` wrapper | группа заглушаемых входов |
| `get_config_template_paths` | — | доп. шаблоны конфигов |

### Пример минимального плагина (файл)

```python
"""Мой плагин — здоровается."""
name='my_greeter'
version='0.1.0'
config={'reply':'Привет!'}
config_comment="reply — текст ответа"

def define_commands():
    def _hi(va, text): va.say(config['reply'])
    return {"привет": _hi}
```

Файл положить в `~/irene/plugins/plugin_my_greeter.py` или пакет `irene_plugin_my/plugin_my.py` + `requirements.txt`.

### Подводные камни

- `config` мутирует in-place — не переназначай `config = new_dict`, меняй ключи.
- `define_commands` вызывается **один раз** при старте Brain — динамически менять команды нельзя без пересоздания Brain.
- Порядок шагов критичен — используй `@after`/`@before` а не надежду на порядок файлов.
- `run` в отдельном потоке если синхронная, в event loop если `async def run` — `terminate` должна уметь отменить.
