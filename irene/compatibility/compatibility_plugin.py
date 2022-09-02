import inspect
import sys
from functools import wraps
from logging import getLogger
from types import ModuleType
from typing import Any, Callable

import irene.compatibility.vacore as vacore_module
from irene import VAContextSource, VAApiExt
from irene.compatibility.vacore import VACore
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, operation, before


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

        try:
            self._core.config = self._manifest['default_options']
            self.config = self._core.config
            self.receive_config = self._receive_config
        except KeyError:
            pass

        # вызов конструктора после присвоения `config` чтобы MagicPlugin смог его (config) заметить
        super().__init__()

    def _receive_config(self, config, *_args, **_kwargs):
        self._manifest['options'] = config

        try:
            start_with_options = self._module.start_with_options
        except AttributeError:
            return

        start_with_options(self._core, self._manifest)

        # Читаем значение (возможно) обновлённое плагином
        self.config = self._core.config

    def _wrap_context_fn(self, fn):
        @wraps(fn)
        def wrapper(va: VAApiExt, text: str):
            self._core.va = va
            fn(self._core, text)

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
            prev = self._wrap_context_fn(prev)
        elif isinstance(prev, tuple):
            first, *rest = prev

            if callable(first) and getattr(first, '__module__', None) == self._module.__name__:
                prev = (self._wrap_context_fn(first), *rest)

        return nxt(prev, *args, **kwargs)

    def define_commands(self, *_args, **_kwargs):
        return self._manifest.get('commands', {})

    def create_tts(self, *_args, **_kwargs):
        # TODO
        ...

    def create_audio_channel(self, *_args, **_kwargs):
        # TODO
        ...


class OriginalCompatibilityPlugin(MagicPlugin):
    """
    Плагин, обеспечивающий совместимость с плагинами для оригинальной Ирины.
    """
    name = 'original_plugin_loader'
    version = '1.0.0'

    config = {
        "mpcIsUse": True,
        "mpcHcPath": "C:\Program Files (x86)\K-Lite Codec Pack\MPC-HC64\mpc-hc64_nvo.exe",
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
