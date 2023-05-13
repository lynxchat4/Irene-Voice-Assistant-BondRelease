from os.path import isfile, join, dirname
from typing import Any, Optional

from irene import VAApiExt
from irene.utils.all_num_to_text import all_num_to_text

__all__ = ('VACore',)


class _UnsupportedConfigAccessError(NotImplementedError):
    def __init__(self):
        super().__init__("Доступ к конфигурации других плагинов не поддерживается.")


class VACore:
    def __init__(self, modname, core_config) -> None:
        self._modname = modname
        self.config: dict[str, Any] = {}
        self.mpcIsUse = core_config.get('mpcIsUse', False)
        self.mpcHcPath = core_config.get('mpcHcPath', '')
        self.mpcIsUseHttpRemote = core_config.get('mpcIsUseHttpRemote', False)
        self.isOnline = core_config.get('isOnline', False)

        self.va: Optional[VAApiExt] = None

        self.all_num_to_text = all_num_to_text

    def _assert_va_ready(self) -> VAApiExt:
        if (va := self.va) is None:
            raise RuntimeError()

        return va

    def save_plugin_options(self, modname, options):
        if modname == self._modname:
            self.config = options
            return

        raise _UnsupportedConfigAccessError()

    def plugin_options(self, modname: str) -> dict[str, Any]:
        if modname == self._modname:
            return self.config

        raise _UnsupportedConfigAccessError()

    def say(self, text: str):
        self._assert_va_ready().say(text)

    def say2(self, text: str):
        self._assert_va_ready().say_speech(text)

    def context_set(self, ctx, timeout=None):
        self._assert_va_ready().context_set(ctx, timeout)

    def play_voice_assistant_speech(self, text: str):
        return self.say(text)

    def play_wav(self, wavfile: str):
        if not isfile(wavfile):
            p = join(dirname(__file__), '../embedded_plugins', wavfile)

            if isfile(p):
                wavfile = p

        self._assert_va_ready().play_audio(wavfile)

    mpcHcPath: str
    mpcIsUse: bool
    mpcIsUseHttpRemote: bool

    isOnline: bool
