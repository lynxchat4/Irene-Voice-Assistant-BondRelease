"""
Добавляет команды "как по-<язык> будет <фраза>"/"переведи на <язык> <фраза>".
"""

from logging import getLogger
from typing import Optional

from irene import VAApiExt
from irene.brain.abc import SpeechOutputChannel, OutputChannelNotFoundError, VAContextSource, TextOutputChannel
from irene.brain.canonical_text import convert_to_canonical
from irene.constants.languages import ALL_LANGUAGES, RUSSIAN, LanguageDefinition
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


def _get_output_for_language(va: VAApiExt, language: LanguageDefinition) -> TextOutputChannel:
    related_outputs = va.get_message().get_related_outputs()
    output: TextOutputChannel

    for label in language.labels:
        try:
            output, *_ = related_outputs.get_channels(
                SpeechOutputChannel,  # type: ignore
                MetaMatcher({label: True})
            )
            return output
        except OutputChannelNotFoundError:
            continue

    for label in language.labels:
        try:
            output, *_ = related_outputs.get_channels(
                TextOutputChannel,  # type: ignore
                MetaMatcher({label: True})
            )

            va.say(f"Я не умею говорить {language.adverb_ru}, но могу написать")

            return output
        except OutputChannelNotFoundError:
            continue

    raise OutputChannelNotFoundError()


def _make_translation_handler(language_definition: LanguageDefinition) -> VAContextSource:
    def _translate(va: VAApiExt, text: str):
        if _provider is None:
            va.say("Я не умею переводить")
            return

        try:
            output = _get_output_for_language(va, language_definition)
        except OutputChannelNotFoundError:
            va.say(f"Я не умею говорить {language_definition.adverb_ru}")
            return

        try:
            translated = _provider.translate(text, language_definition.code, 'ru')
        except Exception:
            _logger.exception(f"Ошибка при переводе на {language_definition.known_ru.nominative} язык")
            va.say("Не удалось перевести")
        else:
            output.send(translated)

    return _translate


_LANGUAGES = tuple(filter(lambda lng: lng.code != RUSSIAN.code, ALL_LANGUAGES))


def define_commands(*_args, **_kwargs):
    commands = {}

    for lng in _LANGUAGES:
        handler = _make_translation_handler(lng)
        commands[f"переведи на {lng.known_ru.nominative}"] = handler
        commands[f"как {convert_to_canonical(lng.adverb_ru)} будет"] = handler

    return commands
