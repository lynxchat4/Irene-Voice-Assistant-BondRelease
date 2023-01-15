"""
Добавляет команды "как по-<язык> будет <фраза>"/"переведи на <язык> <фраза>".
"""

from logging import getLogger
from typing import Optional

from irene import VAApiExt
from irene.brain.abc import SpeechOutputChannel, OutputChannelNotFoundError, VAContextSource
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.utils.metadata import MetaMatcher
from irene_plugin_translate.translation_provider import TranslationProvider

name = 'skill_translate'
version = '0.1.0'

config = {
    'provider': {
        'type': 'libretranslate',
    }
}

config_comment = """
Настройки команд перевода на другие языки.

Доступные параметры:
- ``provider.type``   - тип сервиса, выполняющего перевод.
                        В зависимости от типа используемого сервиса могут быть доступны и/или требоваться дополнительные
                        параметры.
"""

_logger = getLogger(name)

_provider: Optional[TranslationProvider] = None


def init(pm: PluginManager, *_args, **_kwargs):
    global _provider

    _provider = call_all_as_wrappers(
        pm.get_operation_sequence('get_translation_provider'),
        None,
        config['provider'],
    )

    if _provider is None:
        _logger.warning("Не удалось получить сервис для перевода текста")


def _make_translation_handler(target_locale: str, lang_name: str) -> VAContextSource:
    def _translate(va: VAApiExt, text: str):
        if _provider is None:
            va.say("Я не умею переводить")
            return

        try:
            target_locale_output: SpeechOutputChannel
            target_locale_output, *_ = va.get_message().get_related_outputs().get_channels(
                SpeechOutputChannel,  # type: ignore
                MetaMatcher({f"locale.{target_locale}": True})
            )
        except OutputChannelNotFoundError:
            va.say(f"Я не умею говорить по-{lang_name}")
            return

        try:
            translated = _provider.translate(text, target_locale, 'ru')
        except Exception:
            _logger.exception("Ошибка при переводе на другой язык")
            va.say("Не удалось перевести")
        else:
            target_locale_output.send(translated)

    return _translate


_LANGUAGES = (
    ('en', "английский", "английски"),
)


def define_commands(*_args, **_kwargs):
    return {
        **{
            f"переведи на {lang_name_0}": _make_translation_handler(locale, lang_name)
            for locale, lang_name_0, lang_name, *_ in _LANGUAGES
        },
        **{
            f"как по {lang_name} будет": _make_translation_handler(locale, lang_name)
            for locale, _, lang_name, *_ in _LANGUAGES
        },
    }
