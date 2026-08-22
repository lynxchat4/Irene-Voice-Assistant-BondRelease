# 02 — Brain (мозг ассистента)

## Архитектура

```
Входящее сообщение (InboundMessage)
  → BrainImpl.send_messages(outputs) → _process_message
    → VAContextManager.process_command
      → current_context.handle_command(va, msg) → Optional[VAContext] (следующий контекст)
        → если None → возврат к default_context
        → если VAContext → становится current_context + перезапуск таймаута
  → TimeoutTicker.tick_timeout(delta) → handle_timeout → сброс
  → ActiveInteraction → handle_interrupt/handle_restore
```

## Ключевые классы

### Brain (`irene/brain/abc.py` + `brain.py`)

```python
class Brain(VAApiBase):
    def send_messages(outputs: OutputChannelPool) -> ContextManager[Callable[[InboundMessage],None]]:
        # with brain.send_messages(pool) as send: send(msg)

class VAApi:
    def get_outputs() -> OutputChannelPool
    def say(text, **kw)          # → TextOutputChannel.send (блокирует)
    def play_audio(path, **kw)   # → AudioOutputChannel.send_file

class VAApiExt(VAApi):
    def context_set(ctx: VAContextSource, timeout: float|None)
    def get_message() -> InboundMessage
    def get_outputs_preferring_relevant(...)  # сначала related_outputs сообщения
    def say_speech(text)  # только каналы is_speech=True

class InboundMessage(Metadata):
    def get_text() -> str  # канонический (convert_to_canonical)
    def get_related_outputs() -> OutputChannelPool
    def get_original() -> InboundMessage
    @property meta: {'is_direct':bool, 'language':str}
```

`BrainImpl` (`brain/brain.py`):
- `CompositeOutputPool` — стек пулов (insert(0)/remove)
- `_VAApiProvider` — замыкает outputs + context_constructor, лениво связывается с `VAContextManager`
- `TimeoutTicker` отдельный daemon-thread если `timeoutsDisabled==False`

### VAContextManager (`context_manager.py`)

```python
cm = VAContextManager(va, default_context, default_timeout=10.0)
cm.process_command(msg)               # Lock → _set_ctx(current.handle_command(...))
cm.process_active_interaction(ai)     # handle_interrupt → ai.act → handle_restore или InterruptContext
cm.tick_timeout(1.0)                  # вычитает timeout, при <=0 → handle_timeout
cm.default_timeout  # можно менять на лету
```

State-machine: один `current_context` + `_timeout`. Все методы под `Lock`.

### VACommandTree (`command_tree.py`)

Структура для маппинга текста → контексты. Поддерживает:
- Вложенные словари: `{"включи": {"свет": handler}}` → команда "включи свет"
- Варианты через `|`: `"подбрось|брось": {"монетку|монету": fn}` → 4 комбинации
- Нечёткий поиск с `tolerance=2` — пропускает до 2 лишних слов, вес `weight`, `AmbiguousCommandException` если веса близки (<0.1)
- Конфликт → `ConflictingCommandsException`

```python
tree = VACommandTree()
tree.add_commands({"привет": ctx}, context_constructor)
ctx, rest = tree.get_context("привет мир")  # rest="мир"
```

### Контексты (`contexts.py`)

| Класс | Назначение |
|-------|------------|
| `FunctionContext(fn)` | вызывает `fn(va, text)` один раз |
| `FunctionContextWithArgs(fn, arg)` | то же + доп. аргумент |
| `GeneratorContext(gen)` | `yield "фраза"` — говорит и ждёт ответ; `return "фраза"` — финал; `ContextTimeoutException` при молчании |
| `CommandTreeContext(tree, unknown, ambiguous)` | ищет команду в дереве, делегирует остаток текста |
| `TriggerPhraseContext(phrases, inner)` | требует наличие триггер-фразы ("ирина") в тексте, иначе игнор |
| `InterruptContext(interrupted, interrupting)` | сохраняет прерванный контекст, восстанавливает после |
| `TimeoutOverrideContext(inner, timeout)` | переопределяет `get_timeout` |
| `CommandErrorInterceptionContext(inner, replies)` | ловит исключения, говорит `rootCommandErrorReply` |

`ApiExtProvider` — мост между `FunctionContext` и `VAApiExt`:
- `context_set` сохраняет `next_context` + `timeout`
- `get_next_context_from_returned_value` обрабатывает возврат: `None`→default, `str`→say+stay, `generator`→GeneratorContext, `VAContext`→он же

### Сообщения (`inbound_messages.py`)

```python
PlainTextMessage(text, outputs, meta)  # get_text() = canonical(text)
PartialTextMessage(original, text_slice, meta_overrides)  # остаток после съеденного префикса
convert_to_canonical(text)  # lower + без пунктуации + один пробел между словами (см. canonical_text.py)
```

### OutputPool (`output_pool.py`)

```python
CompositeOutputPool(pools)  # объединяет несколько
OutputPoolImpl(channels)
pool.query_channels(predicate)  # Predicate.true() & MetaMatcher
pool.get_channels(TextOutputChannel, MetaMatcher({'is_speech':True}))
```

Каналы — `OutputChannel` с `meta` (словарь). `TextOutputChannel.send(text)`, `AudioOutputChannel.send_file(path)`.

### BrainPlugin (`brain/brain_plugin.py`)

Конфиг по-умолчанию:
```python
config = {
  'triggerPhrases': ["ирина","ирины","ирину"],
  'unknownRootCommandReply': "Извини, я не поняла",
  'ambiguousRootCommandReply': "Извини, я не совсем поняла",
  'rootCommandErrorReply': "Упс, что-то пошло не так.",
  'unknownCommandReply': "Не поняла...",
  'ambiguousCommandReply': "Не совсем поняла...",
  'defaultTimeout': 10.0, 'timeoutsDisabled': False, 'timeoutCheckInterval': 1.0,
}
```

Операции BrainPlugin:
- `construct_context` (степ `construct_default`) — `construct_context(src, **kw)` из `irene/__init__.py`
- `add_default_unknown_command_handlers` (`before construct_default`) — подставляет `unknownCommandReply/ambiguousCommandReply` если нет в словаре
- `create_root_context:load_commands` — собирает `VACommandTree` из всех `define_commands`, вынимает `UNKNOWN_COMMAND_SPECIAL_KEY`/`AMBIGUOUS_COMMAND_SPECIAL_KEY`
- `add_trigger_phrase` (`after load_commands`) — оборачивает в `TriggerPhraseContext`
- `intercept_errors` (`after add_trigger_phrase`) — оборачивает в `CommandErrorInterceptionContext`
- `create_brain` / `kill_brain` / `get_brain` — жизненный цикл `BrainImpl`

### Как добавить команду (шпаргалка)

```python
# Простой хендлер
def _hi(va: VAApiExt, text: str): va.say("Привет!")

# Генератор-диалог
def _game(va: VAApiExt, text: str):
    name = yield "Как тебя зовут?"   # говорит и ждёт
    va.say(f"Привет, {name}")
    va.context_set(_game2)          # альтернатива yield

# Вложенный словарь + варианты
define_commands = {
    "привет|здравствуй": _hi,
    "игра": {"больше меньше": _game, "числа": _game},
    UNKNOWN_COMMAND_SPECIAL_KEY: lambda va, txt: va.say("Не знаю такого"),
}
```

`text` — остаток после съеденного префикса команды (уже canonical).

### Таймауты

- `defaultTimeout` из конфига Brain → `VAContextManager.default_timeout` → `VAContext.get_timeout(default)`
- `TimeoutTicker` тикает каждые `timeoutCheckInterval` (1s), вызывает `tick_timeout`
- Генератор ловит `ContextTimeoutException` при `yield` если пользователь молчит
- `va.context_set(ctx, timeout=5.0)` — одноразовый переопредел.

