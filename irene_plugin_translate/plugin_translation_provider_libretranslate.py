"""
Добавляет возможность использовать сервис LibreTranslate в компонентах, использующих TranslationProvider.
"""

import json
from logging import getLogger
from typing import Optional, TypedDict
from urllib.request import urlopen, Request

from irene_plugin_translate.translation_provider import TranslationProvider

name = 'translation_provider_libretranslate'
version = '0.1.0'


class _Config(TypedDict):
    api_url: str
    api_key: Optional[str]


config: _Config = {
    'api_url': 'https://translate.terraprint.co/translate',
    'api_key': None,
}

config_comment = """
Настройки перевода текста при помощи сервиса LibreTranslate.

Параметры:
- `api_url`   - URL сервиса.
                Список публичных сервисов LibreTranslate доступен здесь:
                https://github.com/LibreTranslate/LibreTranslate#mirrors
                Так же, можно развернуть self-hosted сервис и указать его URL.
- `api_key`   - ключ для LibreTranslate, нужен только если Вы используете сервис, требующий авторизации.
"""

_logger = getLogger(name)


class _LibretranslateTranslationProvider(TranslationProvider):
    def translate(
            self,
            text: str,
            target_language: str,
            source_language: Optional[str] = None,
            *_args,
            **_kwargs
    ):
        query = {
            'q': text,
            'source': 'auto' if source_language is None else source_language,
            'target': target_language,
            'format': 'text',
        }

        if (api_key := config.get('api_key')) is not None:
            query['api_key'] = api_key

        req = Request(
            config["api_url"],
            json.dumps(query).encode('utf-8'),
            headers={
                "Content-Type": "application/json"
            }
        )

        with urlopen(req) as res:
            data = json.load(res)

        _logger.debug(
            "Перевод с %s на %s: '%s' -> %s",
            source_language if source_language is not None else "нераспознанного языка",
            target_language,
            text,
            data,
        )

        return data.get('translatedText')


def get_translation_provider(nxt, prev, settings, *args, **kwargs):
    if settings.get('type') == 'libretranslate':
        prev = prev or _LibretranslateTranslationProvider()

    return nxt(prev, settings, *args, **kwargs)
