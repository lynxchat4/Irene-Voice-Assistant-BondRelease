import inspect
import sys
from functools import wraps
from logging import getLogger
from types import ModuleType
from typing import Any, Callable, Type, Optional

import irene.compatibility.vacore as vacore_module
from irene import VAContextSource, VAApiExt
from irene.brain.abc import AudioOutputChannel
from irene.compatibility.vacore import VACore
from irene.face.abc import FileWritingTTS, ImmediatePlaybackTTS, MuteGroup
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.face.tts_helpers import file_writing_tts_from_callbacks, immediate_playback_tts_from_callbacks
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, operation, before

_WavPlayerConstructor = Callable[[MuteGroup], AudioOutputChannel]


def _make_playwav_channel_type(vacore, init, play) -> _WavPlayerConstructor:
    initialized = False

    class _LocalPlaywavChannel(AudioOutputChannel):
        __slots__ = '_mg'

        def __init__(self, mute_group: MuteGroup):
            nonlocal initialized

            self._mg = mute_group

            if not initialized:
                init(vacore)
                initialized = True

        def send_file(self, file_path: str, **kwargs):
            with self._mg.muted():
                play(vacore, file_path)

    return _LocalPlaywavChannel


class _OriginalPlugin(MagicPlugin):
    """
    Обёртка для модуля плагина оригинальной Ирины.
    """

    def __init__(self, module: ModuleType, core_config: dict[str, Any]):
        self.name = getattr(module, 'modname', module.__name__)
        self.__doc__ = getattr(module, '__doc__', None)

        self._core = VACore(self.name, core_config)

        self._module = module
        self._manifest = module.start(self._core)

        self.version = self._manifest.get('version', 'unknown')

        self._file_tts_types: dict[str, Type[FileWritingTTS]] = {}
        self._immediate_tts_types: dict[str, Type[ImmediatePlaybackTTS]] = {}
        self._audio_output_types: dict[str, _WavPlayerConstructor] = {}

        try:
            self._core.config = self._manifest['default_options']
            self.config = self._core.config
            self.receive_config = self._receive_config
        except KeyError:
            pass

        try:
            ttss: dict[str, tuple] = self._manifest['tts']
        except KeyError:
            pass
        else:
            for (name, callbacks) in ttss.items():
                if callbacks[1] is not None:
                    self._immediate_tts_types[name] = immediate_playback_tts_from_callbacks(
                        name,
                        self._core,
                        callbacks[0],
                        callbacks[1],
                    )

                if len(callbacks) >= 3 and callbacks[2] is not None:
                    self._file_tts_types[name] = file_writing_tts_from_callbacks(
                        name,
                        self._core,
                        callbacks[0],
                        callbacks[2],
                    )

        try:
            playvaws: dict[str, tuple] = self._manifest['playwav']
        except KeyError:
            pass
        else:
            for (name, callbacks) in playvaws.items():
                self._audio_output_types[name] = _make_playwav_channel_type(
                    self._core, *callbacks)

        # вызов конструктора после присвоения `config` чтобы MagicPlugin смог его (config) заметить
        super().__init__()

    def _receive_config(self, config, *_args, **_kwargs):
        self._manifest['options'] = config
        self._core.config = config

        try:
            start_with_options = self._module.start_with_options
        except AttributeError:
            return

        start_with_options(self._core, self._manifest)

        # Читаем значение (возможно) обновлённое плагином
        self.config = self._core.config

    def _wrap_context_fn_no_args(self, fn: Callable[[VACore, str], None]) -> Callable[[VAApiExt, str], None]:
        @wraps(fn)
        def wrapper(va: VAApiExt, text: str):
            self._core.va = va
            fn(self._core, text)

        return wrapper

    def _wrap_context_fn_with_args(self, fn: Callable[[VACore, str, Any], None]) \
            -> Callable[[VAApiExt, str, Any], None]:
        @wraps(fn)
        def wrapper(va: VAApiExt, text: str, *args):
            self._core.va = va
            fn(self._core, text, *args)

        return wrapper

    @operation('construct_context')
    @before('construct_default')
    def wrap_with_vacore_provider(
            self,
            nxt: Callable,
            prev: VAContextSource,
            *args, **kwargs
    ):
        if callable(prev) and getattr(prev, '__module__', None) == self._module.__name__:
            prev_cast: Callable[[VACore, str], None] = prev  # type: ignore
            prev = self._wrap_context_fn_no_args(prev_cast)
        elif isinstance(prev, tuple):
            first, *rest = prev

            if callable(first) and getattr(first, '__module__', None) == self._module.__name__:
                first_cast: Callable[[VACore, str, Any],
                                     None] = first  # type: ignore
                prev = (self._wrap_context_fn_with_args(first_cast), rest[0])

        return nxt(prev, *args, **kwargs)

    def define_commands(self, *_args, **_kwargs):
        return self._manifest.get('commands', {})

    def create_file_tts(self, nxt, prev: Optional[FileWritingTTS], config: dict[str, Any], *args, **kwargs):
        if (tts_type := self._file_tts_types.get(config.get('type', None), None)) is not None:
            prev = prev or tts_type()

        return nxt(prev, config, *args, **kwargs)

    def create_immediate_tts(self, nxt, prev: Optional[ImmediatePlaybackTTS], config: dict[str, Any], *args, **kwargs):
        if (tts_type := self._immediate_tts_types.get(config.get('type', None), None)) is not None:
            prev = prev or tts_type()

        return nxt(prev, config, *args, **kwargs)

    def create_local_outputs(self, nxt, prev: list[AudioOutputChannel], pm: PluginManager, settings: dict[str, Any],
                             *args, **kwargs):
        requested_type = settings.get('type')

        if requested_type in self._audio_output_types:
            prev.append(self._audio_output_types[requested_type](
                kwargs.get('mute_group', NULL_MUTE_GROUP)))

        return nxt(prev, pm, settings, *args, **kwargs)


class OriginalCompatibilityPlugin(MagicPlugin):
    """
    Плагин, обеспечивающий совместимость с плагинами для оригинальной Ирины.
    """
    name = 'original_plugin_loader'
    version = '1.1.0'

    config = {
        "mpcIsUse": True,
        "mpcHcPath": "C:\\Program Files (x86)\\K-Lite Codec Pack\\MPC-HC64\\mpc-hc64_nvo.exe",
        "mpcIsUseHttpRemote": False,

        # TODO: Нужен способ передавать этот флаг (и вообще учитывать оффлайн/онлайн) для новых плагинов тоже
        "isOnline": False,
    }

    _logger = getLogger('compatibilityLoader')

    @before('discover_plugins/bootstrap')
    def bootstrap(self, *_args, **_kwargs):
        # Модули оригинальной Ирины были расположены прямо в корне репозитория, который добавлялся в PYTHONPATH.
        # Эмитируем наличие модуля ядра добавляя его в sys.modules вручную.
        sys.modules['vacore'] = vacore_module

    @operation('discover_plugins_in_module')
    @before('discover_magic_plugin_module')
    def discover_original_irene_plugins(self, _pm: PluginManager, module: ModuleType, *_args, **_kwargs):
        try:
            start = module.start
        except AttributeError:
            return None

        if not callable(start):
            return None

        start_sig = inspect.signature(start)

        if len(start_sig.parameters) != 1:
            return None

        self._logger.debug(
            "Плагин %s выглядит как плагин для оригинальной Ирины.",
            inspect.getfile(module)
        )

        return _OriginalPlugin(module, self.config),
