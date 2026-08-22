# 06 — Faces, TTS/STT, аудио

## Абстракции (`irene/face/abc.py`)

```python
class TTS(Metadata): get_name(); get_settings_hash()
class ImmediatePlaybackTTS(TTS): say(text,**kw)  # блокирует, играет сам
class FileWritingTTS(TTS): say_to_file(text,file_base_path?,**kw)->TTSResultFile
class TTSResultFile: get_full_path(); release()  # контекстный менеджер
class LocalInput: run()->ContextManager[(Iterable[str], Callable stop)]  # генератор строк
class Muteable: mute(); unmute()
class MuteGroup(Muteable): add_item(Muteable)->Callable remove; muted()->ContextManager
```

`MuteGroupImpl` — счётчик `mute_count`, при `>0` все `Muteable` заглушены. Используется чтобы не распознать собственный TTS.

## Встроенные плагины (`irene/embedded_plugins/`)

| Плагин | Что делает | Операции |
|--------|------------|----------|
| `plugin_greetings.py` | "привет" | `define_commands` |
| `plugin_time.py` | "сколько времени" | `define_commands`, использует `pronounce_time_ru` |
| `plugin_date.py` | "какая дата" | `define_commands`, `all_num_to_text` |
| `plugin_gamemoreless.py` | "игра больше меньше" (генератор) | `define_commands` |
| `plugin_random.py` | "брось монету/кость" | `define_commands` с вариантами `подбрось\|брось` |
| `plugin_timer.py` | "поставь таймер на N секунд" | `define_commands`, `active_interaction`, `play_audio(media/timer.wav)` |
| `plugin_command_aliases.py` | алиасы команд | `construct_context` wrapper, читает `aliases` из конфига |
| `plugin_face_console.py` | консольный ввод/вывод | `init`/`run`/`terminate`, `LocalInput` через `aioconsole` |
| `plugin_global_mute_group.py` | глобальный `MuteGroup` | `get_mute_group` |
| `plugin_notification_api.py` | REST `/api/notification` для внешних пушей | `register_fastapi_endpoints` |
| `plugin_voice_profiles.py` | профили голосов (язык/гендер) | `config`, выбор TTS по `MetaMatcher` |
| `plugin_voiceover.py` | озвучка текста через TTS | `get_tts` wrapper, `output` |
| `plugin_tts_cache.py` | кэш `say_to_file` по хешу текста+настроек | `get_tts` wrapper |
| `plugin_tts_pyttsx.py` | движок pyttsx3 (не в Docker) | `get_tts` |
| `plugin_tts_silero_v3.py` | Silero V3 (torch) | `get_tts`, конфиг `model_path`, `speaker`, `sample_rate` |
| `plugin_tts_bark.py` | Bark (малоиспользуемый) | `get_tts` |
| `plugin_audio_converter_ffmpeg.py` / `soundfile` | конвертация аудио | `get_audio_converter` |
| `plugin_vosk_model_loader.py` | загрузка Vosk модели | `init`, `get_vosk_model` |

## Web Face (`irene_plugin_web_face/`)

| Плагин | Роль |
|--------|------|
| `plugin_web_face.py` | `Connection`, `negotiate_protocols`, `Brain.send_messages` |
| `plugin_web_server.py` | Uvicorn + FastAPI, `config:{host,port,ssl_*}` |
| `plugin_web_face_auth.py` | аутентификация WS/REST |
| `plugin_text_io.py` | `in.text-direct/indirect` + `out.text-plain` (каналы `TextOutputChannel`) |
| `plugin_in_stt_clientside.py` | `in.stt.clientside` → `PlainTextMessage(meta=is_direct?)` |
| `plugin_in_stt_serverside.py` | доп WS `/api/plugin_in_stt_serverside/{uuid}`, PCM приём → Vosk → `recognized/processed` |
| `plugin_audio_out_link.py` | `out.audio.link` — сохраняет `TTSResultFile` во временную папку, отдаёт по URL + ждёт progress/done |
| `plugin_out_tts_serverside.py` | `out.tts.serverside` — `FileWritingTTS.say_to_file` → `plugin_audio_out_link` |
| `plugin_mute_protocol.py` | `in.mute` — шлёт mute/unmute при `MuteGroup` |
| `plugin_expose_vosk_model.py` | `GET /api/plugin_expose_vosk_model/*` — отдаёт модель для `vosk-browser` |

## Local Speech Face (`irene_plugin_local_speech_face/`)

- `plugin_local_speech_face.py` — оркестратор, собирает `input: LocalInput` + `outputs: List[Output]` из конфига `face_local`
- `plugin_local_input_sounddevice_vosk.py` — `type: vosk+sounddevice`, слушает микрофон через `sounddevice` (portaudio), распознаёт vosk
- `plugin_local_output_sounddevice.py` — `type: sounddevice`, играет через `sounddevice`
- `plugin_local_output_tts.py` — `type: tts`, выбирает голос через `profile_selector` (см. voice_profiles)

Конфиг `face_local.yaml`:
```yaml
input: {type: vosk+sounddevice}
outputs:
  - {type: sounddevice}
  - {type: tts, profile_selector: {"gender.female": true}}
```

Docker звук: `--device /dev/snd --group-add audio`.

## Telegram Face (`irene_plugin_telegram_face/`)

- `plugin_telegram_face.py` — основной, `pyTelegramBotAPI`
- `plugin_telegram_auth.py` — `allowed_users` из конфига
- `plugin_telegram_plaintext_io.py` — текст `in.text-direct`
- `plugin_telegram_audio_input.py` — голосовые → скачивает ogg → конвертит → vosk → текст
- `plugin_telegram_audio_output.py` — TTS → mp3/ogg → отправка
- `inbound_messages.py` / `outputs.py` — адаптеры `InboundMessage`/`OutputChannelPool` для Telegram

## LLM (`irene_plugin_llm/`)

- `plugin_llm_ollama.py` / `plugin_llm_openai.py` — `LLM` интерфейс, конфиг `api_url`, `model`, `api_key`
- `plugin_llm_fallback_context.py` — если команда не распознана → спрашивает LLM
- `plugin_ai_skill_datetime.py` / `timer.py` — скиллы для LLM function calling

## Translate (`irene_plugin_translate/`)

- `plugin_translate.py` — команда "как по-английски будет ...", "переведи на ..."
- `plugin_translation_provider_libretranslate.py` — `libretranslate` API
- `translation_provider.py` — абстракция

## Utils (`irene/utils/`)

| Модуль | Назначение |
|--------|------------|
| `num_to_text_ru.py` | `num2text(42)` → "сорок два" (склонения, тысячи/миллионы) |
| `all_num_to_text.py` | чисела в тексте → слова |
| `pronounce_numbers_ru.py` / `pronounce_time_ru.py` | "13:05" → "тринадцать ноль пять" |
| `audio_converter.py` | `AudioConverter` (ffmpeg/soundfile), `get_audio_converter` op |
| `predicate.py` | `Predicate.true() & MetaMatcher` для `pool.get_channels` |
| `mapping_match.py` / `executable_files.py` | вспомогательное |
| `metadata.py` | `Metadata` + `MetaMatcher({'is_speech':True})` |

## Constants (`irene/constants/`)

- `gender.py` — `MALE/FEMALE`
- `languages.py` — `RU/EN/...` (ограниченный список для voice_profiles)
- `numerals_ru.py`, `time_units_ru.py`, `word_forms.py` — склонения
- `labels.py`

## Голосовые профили (`plugin_voice_profiles.py`)

```yaml
# voice_profiles.yaml
profiles:
  silero_female:
    tts: silero_v3
    language: ru
    gender: female
    config: {speaker: xenia, sample_rate: 48000}
  silero_male: {tts: silero_v3, language: ru, gender: male, config: {speaker: aidar}}
```

`profile_selector` в `face_local`/`local_output_tts` фильтрует по `MetaMatcher`.

## Добавление TTS движка

```python
from irene.face.abc import FileWritingTTS

class MyTTS(FileWritingTTS):
    def say_to_file(self, text, file_base_path=None, **kw):
        path = file_base_path or tempfile.mktemp(suffix='.wav')
        # синтез → path
        return FileResult(path)  # реализуй get_full_path + release (удаляет файл)

# В плагине:
def get_tts(self, nxt, prev, *a, **kw):
    # вернуть MyTTS() или nxt(prev) если не подходит
    return MyTTS()
```

Цепочка `get_tts` — wrapper, `voiceover` → `tts_cache` → `voice_profiles` → конкретный движок.

## ESP32 (`esp32-client/irene-esp32-arduino-client/`)

- Arduino, `audio_capture.cpp` (I2S микрофон), `audio_playback.cpp` (I2S динамик), `websocket_connection.cpp`, `state.cpp` (конечный автомат), `protocol_negotiation.*` (negotiate), `wifi_connection.*`
- Протокол тот же что web_face, запрашивает `in.stt.serverside` + `out.audio.link` + `out.tts.serverside`
