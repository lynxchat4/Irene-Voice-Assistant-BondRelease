import unittest
from typing import Optional, Any, Iterable, Callable
from unittest.mock import Mock

from irene.brain.abc import AudioOutputChannel, OutputChannel
from irene.face.abc import FileWritingTTS, ImmediatePlaybackTTS, TTSResultFile
from irene.plugin_loader.abc import Plugin, PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.test_utuls import PluginTestCase
from irene.utils.mapping_match import mapping_match
from irene.utils.metadata import MetadataMapping


class ResultFileStub(TTSResultFile):
    def __init__(self, tts: FileWritingTTS):
        self.tts = tts

    def get_full_path(self) -> str:
        return f'/stub/{self.tts.get_name()}/file.wav'

    def release(self):
        pass


class FileTTSStub(FileWritingTTS):
    def __init__(self, name: str):
        self._name = name

    def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
        return ResultFileStub(self)

    def get_name(self) -> str:
        return self._name

    def get_settings_hash(self) -> str:
        return f'{self._name}:settings'

    @property
    def meta(self) -> MetadataMapping:
        return {f'name.{self._name}': True}


def _make_immediate_tts_mock() -> ImmediatePlaybackTTS:
    return Mock(spec=ImmediatePlaybackTTS)


def _make_playback_channel_mock() -> AudioOutputChannel:
    return Mock(spec=AudioOutputChannel)


class TTSPluginFixture(MagicPlugin):
    name = 'tts_fixture'
    version = '1.0.0'

    def __init__(self):
        super().__init__()

        self.file_mock1 = FileTTSStub('mock1')
        self.file_mock2 = FileTTSStub('mock2')

        self.immediate_mock2 = _make_immediate_tts_mock()
        self.immediate_mock3 = _make_immediate_tts_mock()

        self.player_mock = _make_playback_channel_mock()

    def create_file_tts(self, nxt, prev: Optional[FileWritingTTS], config: dict[str, Any], *args, **kwargs):
        if config.get('type') == 'mock1':
            prev = self.file_mock1
        elif config.get('type') == 'mock2':
            prev = self.file_mock2

        return nxt(prev, config, *args, **kwargs)

    def create_immediate_tts(self, nxt, prev: Optional[ImmediatePlaybackTTS], config: dict[str, Any], *args, **kwargs):
        if config.get('type') == 'mock2':
            prev = self.immediate_mock2
        elif config.get('type') == 'mock3':
            prev = self.immediate_mock3

        return nxt(prev, config, *args, **kwargs)

    def create_local_outputs(
            self,
            nxt: Callable,
            prev: list[OutputChannel],
            pm: PluginManager,
            settings: dict[str, Any],
            *args,
            **kwargs
    ):
        if settings.get('type') == 'mock':
            prev.append(self.player_mock)

        return nxt(prev, pm, settings, *args, **kwargs)


class VoiceProfilesTest(PluginTestCase):
    plugin = '../plugin_voice_profiles.py'

    configs = {
        'voice_profiles': {
            'voiceProfiles': {
                'mock1_prof': {
                    'enabled': True,
                    'tts_settings': {
                        'type': 'mock1'
                    },
                    'metadata': {
                        'profile_label': 'mock1',
                    },
                    'localPlayer': {
                        'type': 'mock'
                    },
                },
                'mock2_prof': {
                    'enabled': True,
                    'priority': -1,
                    'tts_settings': {
                        'type': 'mock2'
                    },
                    'metadata': {
                        'profile_label': 'mock2',
                    },
                },
                'mock3_prof': {
                    'enabled': True,
                    'tts_settings': {
                        'type': 'mock3'
                    },
                    'metadata': {
                        'profile_label': 'mock3',
                    },
                },
            }
        }
    }

    fixture_plugin = TTSPluginFixture()

    def get_additional_plugins(self) -> Iterable[Plugin]:
        return [self.fixture_plugin]

    def assert_result_from(self, result: TTSResultFile, tts: FileWritingTTS):
        self.assertIsInstance(result, ResultFileStub)
        self.assertIs(result.tts, tts)  # type: ignore

    def test_get_all_file_profiles(self):
        ttss = call_all_as_wrappers(
            self.pm.get_operation_sequence('get_file_writing_tts_engines'),
            [],
            self.pm,
            random_named_argument=True,
        )

        self.assertEqual(len(ttss), 2)

    def test_file_profiles_order(self):
        ttss: list[FileWritingTTS] = call_all_as_wrappers(
            self.pm.get_operation_sequence('get_file_writing_tts_engines'),
            [],
            self.pm,
        )

        # Приоритет у mock2 выше, так что он идёт первым.
        # Сравнивать экземпляры ttss[x] с self.fixture_plugin.file_mockX напрямую нельзя - voice_profiles возвращает
        # прокси
        self.assertEqual(ttss[0].get_name(),
                         self.fixture_plugin.file_mock2.get_name())
        self.assertEqual(ttss[0].get_settings_hash(
        ), self.fixture_plugin.file_mock2.get_settings_hash())
        self.assert_result_from(ttss[0].say_to_file(
            'test'), self.fixture_plugin.file_mock2)

        self.assertEqual(ttss[1].get_name(),
                         self.fixture_plugin.file_mock1.get_name())
        self.assertEqual(ttss[1].get_settings_hash(
        ), self.fixture_plugin.file_mock1.get_settings_hash())
        self.assert_result_from(ttss[1].say_to_file(
            'test'), self.fixture_plugin.file_mock1)

    def test_file_profile_get_one_by_meta(self):
        ttss: list[FileWritingTTS] = call_all_as_wrappers(
            self.pm.get_operation_sequence('get_file_writing_tts_engines'),
            [],
            self.pm,
            selector={'profile_label': 'mock1'},
        )

        self.assertEqual(len(ttss), 1)
        self.assertTrue(mapping_match(
            ttss[0].meta, {'profile_label': 'mock1', 'name.mock1': True}))

    def test_immediate_profile(self):
        ttss = call_all_as_wrappers(
            self.pm.get_operation_sequence(
                'get_immediate_playback_tts_engines'),
            [],
            self.pm,
            random_named_argument=True,
        )

        self.assertEqual(3, len(ttss))

    def test_one_direct_immediate_profile(self):
        ttss: list[ImmediatePlaybackTTS] = call_all_as_wrappers(
            self.pm.get_operation_sequence(
                'get_immediate_playback_tts_engines'),
            [],
            self.pm,
            selector={'profile_label': 'mock2'}
        )

        self.assertEqual(len(ttss), 1)
        ttss[0].say('Hi', additional_arg='foo')

        self.fixture_plugin.immediate_mock2.say.assert_called_once_with(
            'Hi', additional_arg='foo')

    def test_one_composite_immediate_profile(self):
        """
        Чтобы получить ImmediatePlaybackTTS для профиля с TTS-движком, поддерживающим только запись в файлы, mock1_prof,
        voice_profiles создаёт канал воспроизведения файлов (AudioOutputChannel) и создаёт адаптер, генерирующий файл
        при помощи TTS и сразу воспроизводящий его через этот канал.
        """
        ttss: list[ImmediatePlaybackTTS] = call_all_as_wrappers(
            self.pm.get_operation_sequence(
                'get_immediate_playback_tts_engines'),
            [],
            self.pm,
            selector={'profile_label': 'mock1'}
        )

        self.assertEqual(len(ttss), 1)
        ttss[0].say('Hi', additional_arg='foo')

        self.fixture_plugin.player_mock.send_file.assert_called_once_with(
            self.fixture_plugin.file_mock1.say_to_file('').get_full_path(),
            alt_text='Hi'
        )


if __name__ == '__main__':
    unittest.main()
