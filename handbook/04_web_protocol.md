# 04 — Клиент-серверный протокол

Док-основа: `doc/client-server-protocol.md`, константы `irene_plugin_web_face/protocol.py`, реализация `irene_plugin_web_face/plugin_web_face.py`.

## Транспорт

- **URL:** `ws(s)://host:8086/api/face_web/ws` (WebSocket, текстовые JSON)
- Все сообщения: `{"type":"<protocol>/<action>", ...}`
- Доп. WebSocket для `in.stt.serverside` — путь выдаёт сервер в `in.stt.serverside/ready`

## Согласование протоколов

```
Клиент → {"type":"negotiate/request","protocols":[["a","b"],["c","d"]]}
  # каждая вложенная группа = "нужен хотя бы один из"
Сервер → {"type":"negotiate/agree","protocols":["a","d"]}
  # выбирает первый поддерживаемый из каждой группы, сохраняет порядок
```

Пример фронтенда (`frontend/src/app.ts:getProtocolRequirements`):
```js
requirements = [
  ['in.text-direct','in.text-indirect'],
  ['out.audio.link'],
  ['out.tts.serverside','out.text-plain'],
  ['in.stt.serverside','in.stt.clientside','in.text-indirect'], // в зависимости от preferStreamingInput
  ['in.mute']
]
```

Реализация сервера (`plugin_web_face.py:_ConnectionImpl.negotiate_protocols`):
- ищет `init_client_protocol` среди плагинов через `call_all_as_wrappers`
- если `ProtocolHandler` найден → `negotiated.append(variant)` + `handler.start()`
- иначе пробует следующий вариант, если все не поддержаны → `_UnsupportedProtocolsException`
- `get_mute_group` резолвит `MuteGroup` для соединения

## Все протоколы

| Протокол | Направление | Типы сообщений | Файл плагина |
|----------|-------------|----------------|--------------|
| `in.text-direct` | C→S | `in.text-direct/text {text}` | `plugin_text_io.py` |
| `in.text-indirect` | C→S | `in.text-indirect/text {text}` | `plugin_text_io.py` |
| `in.stt.clientside` | C→S / S→C | `in.stt.clientside/recognized {text}` → `in.stt.clientside/processed {text}` | `plugin_in_stt_clientside.py` |
| `in.stt.serverside` | C↔S (+доп WS) | `in.stt.serverside/ready {path}` (S→C), аудио поток (C→S доп WS `?sample_rate=44100`), `recognized`/`processed {text}` (S→C) | `plugin_in_stt_serverside.py` |
| `in.mute` | S→C | `in.mute/mute {}` / `in.mute/unmute {}` | `plugin_mute_protocol.py` |
| `out.text-plain` | S→C | `out.text-plain/text {text}` | `plugin_text_io.py` |
| `out.audio.link` | S→C + C→S | S→C `out.audio.link/playback-request {url, playbackId, altText?}` ; C→S `playback-progress {playbackId}` (каждую 1s) + `playback-done {playbackId}` | `plugin_audio_out_link.py` |
| `out.tts.serverside` | S→C (мета) | разрешает серверу использовать `out.audio.link` для TTS, **должен идти после `out.audio.link` в negotiate** | `plugin_out_tts_serverside.py` |

Детали:

- ** `in.text-indirect` vs `direct`**: indirect требует триггер-фразы ("ирина ..."), direct — любое сообщение считается командой.
- ** `clientside` processed**: сервер отвечает только если часть текста распознана как команда (отфильтрован триггер). Пример: `recognized:"бла бла ирина включи свет"` → `processed:"включи свет"`.
- ** `serverside` streaming**: 
  ```
  S→C {"type":"in.stt.serverside/ready","path":"/api/plugin_in_stt_serverside/44aec96f-..."}
  C→S connect ws://host:8086/api/plugin_in_stt_serverside/44aec96f-...?sample_rate=44100 (или 16000)
  C→S binary: 16-bit signed LE PCM (порядок байтов хоста)
  S→C {"type":"in.stt.serverside/recognized","text":"..."}
  S→C {"type":"in.stt.serverside/processed","text":"включи свет"} // если команда
  ```
- ** `out.audio.link`**: файл временно доступен по `url` (обычно `/api/plugin_audio_out_link/<id>.wav`), клиент создаёт `new Audio(url)`, шлёт `progress` каждую секунду + `done` в конце. Сервер ждёт `done` чтобы освободить.
- ** `in.mute`**: когда сервер/клиент воспроизводит ответ, сервер шлёт `mute`, после окончания — `unmute`. Клиент должен выключить микрофон чтобы не распознать свой же голос.

## Архитектура WebSocket на сервере

```
plugin_web_face.py: WebFacePlugin
  FastAPI route /api/face_web/ws (WebSocket)
    on connect → _ConnectionImpl(ws)
      1) ждёт negotiate/request (первое сообщение)
      2) negotiate_protocols(pm, msg) → выбирает ProtocolHandler'ы
      3) создаёт Brain.send_messages(outputs) context → set_message_processor
      4) каждый ProtocolHandler.start() регистрирует:
           - connection.register_message_type(type, handler)
           - connection.register_output(channel)
      5) on_message_received → dispatch по type
      6) on disconnect → connection.terminate() (чистит outputs + proto handlers)
```

```python
class Connection(ABC):
    def register_message_type(mt, handler): ...
    def register_output(ch: OutputChannel): ...
    def get_associated_outputs() -> OutputChannelPool: ...
    def receive_inbound_message(im: InboundMessage): ...  # → run_in_executor(mp(im))
    def send_message(mt, payload): ...  # call_soon_threadsafe(ws.send_json)
    def negotiate_protocols(pm, msg): ...
    def set_message_processor(fn): ...
    def terminate(): ...
```

`ProtocolHandler` (abc.py): `start()`, `terminate()`.

## Добавление своего протокола

```python
# plugin_my_proto.py
from irene_plugin_web_face.abc import ProtocolHandler
from irene.plugin_loader.magic_plugin import MagicPlugin

class MyProto(ProtocolHandler):
    def __init__(self, conn): self.conn=conn
    def start(self):
        self.conn.register_message_type("my.proto/msg", self.on_msg)
        self.conn.register_output(MyOutputChannel(self.conn))
    def terminate(self): ...
    def on_msg(self, msg): ...

class MyPlugin(MagicPlugin):
    name='my_proto'
    def init_client_protocol(self, nxt, prev, variant, connection, pm, mute_group=None):
        if variant != "my.proto": return nxt(prev, variant, connection, pm, mute_group=mute_group)
        return MyProto(connection)
```

Клиент должен запросить `"my.proto"` в `negotiate/request`.

## REST (помимо WS)

- `GET /api/config` — список конфигов
- `GET /api/config/{plugin}` — конфиг + коммент
- `PUT /api/config/{plugin}` — обновить (если `storeOnRESTUpdate`)
- `GET /api/plugin_audio_out_link/{id}` — временный аудиофайл
- `GET /` — фронт (из `irene_plugin_web_face_frontend`)
- Auth: `plugin_web_face_auth.py` — базовая/токен защита, настраивается через `web_face_frontend` + `web_authentication` (см. README фронтенда)
