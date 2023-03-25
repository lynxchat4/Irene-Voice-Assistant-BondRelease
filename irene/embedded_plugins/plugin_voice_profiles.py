from logging import getLogger
from typing import Any, Optional, Generic, TypeVar, Iterable

from irene.brain.abc import AudioOutputChannel
from irene.face.abc import FileWritingTTS, TTS, TTSResultFile, ImmediatePlaybackTTS
from irene.face.tts_helpers import FilePlaybackTTS
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import step_name
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.utils.metadata import Metadata, MetaMatcher, MetadataMapping
from irene.utils.predicate import Predicate

name = 'voice_profiles'
version = '0.1.0'

_logger = getLogger(name)

config_comment = """
Настройки голосов, которыми может говорить голосовой ассистент.

Параметры:

- `"voiceProfiles"`       - список голосовых профилей (см. далее)
- `"defaultLocalPlayer"`  - метод воспроизведения голоса, используемый по-умолчанию для воспроизведения речи на
                            локальном устройстве.

Голосовым профилем называется набор настроек для TTS-движка, который затем может использоваться для озвучения речи.
Список голосовых профилей представляет собой объект, ключом в котором служит уникальное имя профиля, а значением - набор
его параметров.
Настройки профиля представляют собой объект, содержащий следующие поля:

- `"tts_settings"`        - объект, содержащий тип TTS-движка (как правило, в поле `"type"`) и дополнительные настройки
                            в других полях. Точный набор полей зависит от выбранного TTS-движка.
- `"enabled"`             - если это поле не равно `true`, то профиль будет проигнорирован. Полезно если нужно временно
                            отключить некоторые профили или добавить примеры/дополнительные варианты настроек в шаблон
                            конфигурации.
- `"priority"`            - приоритет профиля. Чем меньше значение, тем выше приоритет.
- `"metadata"`            - объект, содержащий метаданные профиля. Используется для выбора голоса, при воспроизведении
                            речи.
- `"localPlayer"`         - метод воспроизведения голоса, используемый для воспроизведения голоса, синтезированного этим
                            профилем. Можно использовать это поле, если метод, используемый по-умолчанию не работает
                            корректно с результатами синтеза выбранного TTS-движка.

Изменения настроек существующих профилей (кроме включения/выключения) применяются немедленно.
Для применения других изменений может понадобиться переподключение подключенных устройств (в клиент-серверном режиме)
или перезапуск приложения.

## Выбор профилей с помощью метаданных

Обычно метаданные профиля должны содержать, как минимум, следующую информацию:

- сведения о языках, поддерживаемых, профилем.
  Для каждого поддерживаемого языка добавляется поле следующего вида:
  ```yaml
  "language.<код языка>": true
  ```
- указание пола голоса. Например, для женского голоса должно присутствовать следующее поле:
  ```yaml
  "gender.female": true
  ```

Метаданные профилей могут так же содержать произвольные пользовательские поля.

Например, если вы хотите использовать TTS pyttsx для воспроизведения речи локально и TTS silero_v3 для воспроизведения
ответов на сообщения в Telegram, то можно добавить профили следующего вида:

```yaml
voiceProfiles:
  myPyttsxProfile:
    enabled: true
    tts_settings:
      type: pyttsx
    metadata:
      "gender.female": true
      "language.ru": true
      "usage.local": true
  myTelegramProfile:
    enabled: true
    tts_settings:
      type: silero_v3
      silero_settings:
        speaker: "xenia"
        sample_rate: 24000
        put_accent: true
        put_yo: true
      warmup_iterations: 4
      warmup_phrase: "Привед медвед"
      model_url:
        "https://models.silero.ai/models/tts/ru/v3_1_ru.pt"
    metadata:
      "gender.female": true
      "language.ru": true
      "usage.telegram": true
```

Затем, в настройках локального интерфейса (face_local):

```yaml
...
outputs:
... # Другие способы вывода
- profile_selector:
    "usage.local": true
  type: tts
...
```

и в настройках озвучения сообщений для Telegram (telegram_output_audio):

```yaml
...
voiceProfileSelector:
  "usage.telegram": true
```

указать, какие профили следует использовать.
"""

config: dict[str, Any] = {
    "defaultLocalPlayer": {
        "type": "sounddevice"
    },
    "voiceProfiles": {
        "silero_v3_ru_f": {
            "enabled": True,
            "priority": -1000,
            "tts_settings": {
                "type": 'silero_v3',
                "silero_settings": {
                    "speaker": "xenia",
                    "sample_rate": 24000,
                    "put_accent": True,
                    "put_yo": True,
                },
                "warmup_iterations": 4,
                "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
                "model_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
            },
            "metadata": {
                "language.ru": True,
                "gender.female": True,
            },
            "localPlayer": {
                "type": "sounddevice"
            },
        },
        "silero_v3_ru_m": {
            "enabled": False,
            "priority": -1000,
            "tts_settings": {
                "type": 'silero_v3',
                "silero_settings": {
                    "speaker": "eugene",
                    "sample_rate": 24000,
                    "put_accent": True,
                    "put_yo": True,
                },
                "warmup_iterations": 4,
                "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
                "model_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
            },
            "metadata": {
                "language.ru": True,
                "gender.male": True,
            },
        },
        "silero_v3_en_f": {
            "enabled": False,
            "tts_settings": {
                "type": 'silero_v3',
                "silero_settings": {
                    "speaker": "en_0",
                    "sample_rate": 24000,
                },
                "warmup_iterations": 4,
                "warmup_phrase": "Can you can a canned can into an un-canned can like a canner can can a canned can into "
                                 "an un-canned can?",
                "model_url": "https://models.silero.ai/models/tts/en/v3_en.pt",
            },
            "metadata": {
                "language.en": True,
                "gender.female": True,
            },
        },
        "silero_v3_en_m": {
            "enabled": False,
            "tts_settings": {
                "type": 'silero_v3',
                "silero_settings": {
                    "speaker": "en_1",
                    "sample_rate": 24000,
                },
                "warmup_iterations": 4,
                "warmup_phrase": "Can you can a canned can into an un-canned can like a canner can can a canned can into "
                                 "an un-canned can?",
                "model_url": "https://models.silero.ai/models/tts/en/v3_en.pt",
            },
            "metadata": {
                "language.en": True,
                "gender.male": True,
            },
        },
        "silero_v3_de_f": {
            "enabled": False,
            "tts_settings": {
                "type": 'silero_v3',
                "silero_settings": {
                    "sample_rate": 24000,
                },
                "warmup_iterations": 4,
                "warmup_phrase": "Fischers Fritze fischt frische Fische, Frische Fische fischt Fischers Fritze.",
                "model_url": "https://models.silero.ai/models/tts/de/v3_de.pt",
            },
            "metadata": {
                "language.de": True,
                "gender.female": True,
            },
        },
    },
}

_TTSBaseClass = TypeVar('_TTSBaseClass', bound=TTS)


class _TTSProxy(TTS, Generic[_TTSBaseClass]):
    def __init__(self, tts: _TTSBaseClass, meta_source: Metadata):
        self._current_impl = tts
        self._meta_source = meta_source

    def get_current_implementation(self) -> _TTSBaseClass:
        return self._current_impl

    def replace_implementation(self, impl: _TTSBaseClass):
        self._current_impl = impl

    def get_name(self) -> str:
        return self._current_impl.get_name()

    def get_settings_hash(self) -> str:
        return self._current_impl.get_settings_hash()

    @property
    def meta(self):
        return {**self._meta_source.meta, **self._current_impl.meta}


class _FileWritingTTSProxy(_TTSProxy[FileWritingTTS], FileWritingTTS):
    def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
        return self.get_current_implementation().say_to_file(text, file_base_path, **kwargs)


class _ImmediateTTSProxy(_TTSProxy[ImmediatePlaybackTTS], ImmediatePlaybackTTS):
    def say(self, text: str, **kwargs):
        return self.get_current_implementation().say(text, **kwargs)


class _TTSCreationFailure(Exception):
    ...


class _VoiceProfile(Metadata):
    def __init__(
            self,
            profile_id: str,
            settings: dict,
    ):
        self._id = profile_id
        self._settings = settings
        self._pm: Optional[PluginManager] = None

        self._file_writing_tts_proxy: Optional[_FileWritingTTSProxy] = None
        self._immediate_tts_proxy: Optional[_ImmediateTTSProxy] = None

    def update_settings(self, new_settings: dict[str, Any]):
        if self._settings == new_settings:
            _logger.debug(f"Настройки для профиля {self._id} не изменились")
            return

        self._settings = new_settings

        if self._file_writing_tts_proxy is not None:
            try:
                self._file_writing_tts_proxy.replace_implementation(self._create_file_writing_tts())
            except _TTSCreationFailure:
                _logger.exception(
                    f"Не удалось пересоздать файловый TTS для профиля {self._id} после изменения настроек")

        if self._immediate_tts_proxy is not None:
            try:
                self._immediate_tts_proxy.replace_implementation(self._create_immediate_tts())
            except _TTSCreationFailure:
                _logger.exception(f"Не удалось пересоздать TTS для профиля {self._id} после изменения настроек")

    @property
    def meta(self) -> MetadataMapping:
        return self._settings.get('metadata', {})

    @property
    def priority(self):
        return self._settings.get('priority', 0)

    def _create_file_writing_tts(self) -> FileWritingTTS:
        assert self._pm is not None

        tts: Optional[FileWritingTTS] = call_all_as_wrappers(
            self._pm.get_operation_sequence('create_file_tts'),
            None,
            self._settings.get('tts_settings', {}),
            self._pm,
        )

        if tts is None:
            raise _TTSCreationFailure(f"Не удалось создать файловый TTS для профиля {self._id}")

        return tts

    def _create_immediate_tts(self) -> ImmediatePlaybackTTS:
        assert self._pm is not None

        tts: Optional[ImmediatePlaybackTTS] = call_all_as_wrappers(
            self._pm.get_operation_sequence('create_immediate_tts'),
            None,
            self._settings.get('tts_settings', {}),
            self._pm,
        )

        if tts is None:
            file_tts = self.get_file_writing_tts(self._pm)

            player_settings: dict[str, Any] = self._settings.get('localPlayer', config['defaultLocalPlayer'])

            players = call_all_as_wrappers(
                self._pm.get_operation_sequence('create_local_outputs'),
                [],
                self._pm,
                player_settings,
            )

            filtered_players = list(filter(AudioOutputChannel.__instancecheck__, players))

            if len(filtered_players) == 0:
                raise _TTSCreationFailure(f"Не удалось создать канал вывода звука для профиля {self._id}")

            tts = FilePlaybackTTS(file_tts, filtered_players[0])

        return tts

    def get_file_writing_tts(self, pm: PluginManager) -> FileWritingTTS:
        self._pm = pm

        if self._file_writing_tts_proxy is None:
            self._file_writing_tts_proxy = _FileWritingTTSProxy(
                self._create_file_writing_tts(),
                self
            )

        return self._file_writing_tts_proxy

    def get_immediate_tts(self, pm: PluginManager) -> ImmediatePlaybackTTS:
        self._pm = pm

        if self._immediate_tts_proxy is None:
            self._immediate_tts_proxy = _ImmediateTTSProxy(
                self._create_immediate_tts(),
                self
            )

        return self._immediate_tts_proxy


_profiles: dict[str, _VoiceProfile] = {}


def receive_config(config: dict[str, Any], *_args, **_kwargs):
    new_profiles: dict[str, dict[str, Any]] = config['voiceProfiles']

    for profile_id, profile_settings in new_profiles.items():
        if profile_settings.get('enabled', False):
            if profile_id in _profiles:
                _profiles[profile_id].update_settings(profile_settings)
            else:
                _profiles[profile_id] = _VoiceProfile(profile_id, profile_settings)

    for profile_id in _profiles.keys():
        if not new_profiles.get(profile_id, {}).get('enabled', False):
            del _profiles[profile_id]


def _get_matching_profiles(
        selector: Optional[dict[str, Any]] = None,
        **_kwargs,
) -> Iterable[_VoiceProfile]:
    profile_matcher: Predicate[_VoiceProfile] = Predicate.true()

    if selector is not None:
        profile_matcher = profile_matcher & MetaMatcher(selector)

    return sorted(
        (profile for profile in _profiles.values() if profile_matcher(profile)),
        key=lambda it: it.priority
    )


@step_name('get_from_profiles')
def get_file_writing_tts_engines(
        nxt, prev: list[FileWritingTTS],
        pm: PluginManager,
        *args, **kwargs
):
    for profile in _get_matching_profiles(*args, **kwargs):
        try:
            prev.append(profile.get_file_writing_tts(pm))
        except _TTSCreationFailure:
            _logger.exception("")

    return nxt(prev, pm, *args, **kwargs)


@step_name('get_from_profiles')
def get_immediate_playback_tts_engines(
        nxt, prev: list[ImmediatePlaybackTTS],
        pm: PluginManager,
        *args, **kwargs
):
    for profile in _get_matching_profiles(*args, **kwargs):
        try:
            prev.append(profile.get_immediate_tts(pm))
        except _TTSCreationFailure:
            _logger.exception("")

    return nxt(prev, pm, *args, **kwargs)
