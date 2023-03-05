from logging import getLogger
from typing import Any, Mapping, Optional, Generic, TypeVar, Iterable

from irene.brain.abc import AudioOutputChannel
from irene.face.abc import FileWritingTTS, TTS, TTSResultFile, ImmediatePlaybackTTS
from irene.face.tts_helpers import FilePlaybackTTS
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import step_name
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.utils.metadata import Metadata, MetaMatcher
from irene.utils.predicate import Predicate

name = 'voice_profiles'
version = '0.1.0'

_logger = getLogger(name)

config_comment = """
"""

config: dict[str, Any] = {
    "defaultLocalPlayer": {
        "type": "sounddevice"
    },
    "voiceProfiles": {
        "silero_v3_ru_f": {
            "enabled": True,
            "type": 'silero_v3',
            "silero_settings": {
                "speaker": "xenia",
                "sample_rate": 24000,
                "put_accent": True,
                "put_yo": True,
            },
            "metadata": {
                "locale": "ru",
                "locale.ru": True,
                "gender": "female",
                "gender.female": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
            "model_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
            "localPlayer": {
                "type": "sounddevice"
            },
        },
        "silero_v3_ru_m": {
            "enabled": False,
            "type": "silero_v3",
            "silero_settings": {
                "speaker": "eugene",
                "sample_rate": 24000,
                "put_accent": True,
                "put_yo": True,
            },
            "metadata": {
                "locale": "ru",
                "locale.ru": True,
                "gender": "male",
                "gender.male": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
            "model_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
        },
        "silero_v3_en_f": {
            "enabled": False,
            "type": "silero_v3",
            "silero_settings": {
                "speaker": "en_0",
                "sample_rate": 24000,
            },
            "metadata": {
                "locale": "en",
                "locale.en": True,
                "gender": "female",
                "gender.female": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "Can you can a canned can into an un-canned can like a canner can can a canned can into "
                             "an un-canned can?",
            "model_url": "https://models.silero.ai/models/tts/en/v3_en.pt",
        },
        "silero_v3_en_m": {
            "enabled": False,
            "type": "silero_v3",
            "silero_settings": {
                "speaker": "en_1",
                "sample_rate": 24000,
            },
            "metadata": {
                "locale": "en",
                "locale.en": True,
                "gender": "male",
                "gender.male": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "Can you can a canned can into an un-canned can like a canner can can a canned can into "
                             "an un-canned can?",
            "model_url": "https://models.silero.ai/models/tts/en/v3_en.pt",
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
        return {**self._meta_source, **self._current_impl.meta}


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
    def meta(self) -> Mapping[str, Any]:
        return self._settings.get('metadata', {})

    def _create_file_writing_tts(self) -> FileWritingTTS:
        assert self._pm is not None

        tts: Optional[FileWritingTTS] = call_all_as_wrappers(
            self._pm.get_operation_sequence('create_file_tts'),
            None,
            self._settings,
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
            self._settings,
            self._pm,
        )

        if tts is None:
            file_tts = self.get_file_writing_tts(self._pm)

            player_settings: dict[str, Any] = self._settings.get('localPlayer', config['defaultLocalPlayer'])

            player = call_all_as_wrappers(
                self._pm.get_operation_sequence('create_local_output'),
                None,
                self._pm,
                player_settings,
            )

            if not isinstance(player, AudioOutputChannel):
                raise _TTSCreationFailure(f"Не удалось создать канал вывода звука для профиля {self._id}")

            tts = FilePlaybackTTS(file_tts, player)

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
        selector: Optional[dict[str, Any]],
) -> Iterable[_VoiceProfile]:
    profile_matcher: Predicate[_VoiceProfile] = Predicate.true()

    if selector is not None:
        profile_matcher = profile_matcher | MetaMatcher(selector)

    return (profile for profile in _profiles.values() if profile_matcher(profile))


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
