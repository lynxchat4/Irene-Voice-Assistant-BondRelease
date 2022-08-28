from typing import Any, Optional

from irene import VAApiExt

__all__ = ('VACore',)


class VACore:
    def __init__(self, modname, core_config):
        self._modname = modname
        self.config = {}
        self.mpcIsUse = core_config.get('mpcIsUse', False)
        self.mpcHcPath = core_config.get('mpcHcPath', '')
        self.mpcIsUseHttpRemote = core_config.get('mpcIsUseHttpRemote', False)
        self.isOnline = core_config.get('isOnline', False)

        self.va: Optional[VAApiExt] = None

    def save_plugin_options(self, _modname, options):
        self.config = options

    def plugin_options(self, modname: str) -> dict[str, Any]:
        if modname == self._modname:
            return self.config

        raise NotImplementedError("Доступ к конфигурации других плагинов не поддерживается.")

    def say(self, text: str):
        self.va.say(text)

    def say2(self, text: str):
        self.va.say_speech(text)

    def context_set(self, ctx, timeout=None):
        self.va.context_set(ctx, timeout)

    def play_voice_assistant_speech(self, text: str):
        return self.say(text)

    mpcHcPath: str
    mpcIsUse: bool
    mpcIsUseHttpRemote: bool

    isOnline: bool
