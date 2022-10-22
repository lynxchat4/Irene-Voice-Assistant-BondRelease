"""
Загружает модель для движка распознания речи Vosk.

В настройках указывается публичный URL, по которому расположен архив с моделью.
Если файл не был загружен ранее, то он будет загружен при запуске приложения или при изменении конфигурации плагина.
"""

import os
from hashlib import md5
from logging import getLogger
from os.path import basename, dirname
from urllib.parse import urlparse
from urllib.request import urlretrieve

from irene.plugin_loader.file_patterns import pick_random_file, first_substitution

name = 'vosk_model_loader'
version = '1.0.0'

_logger = getLogger(name)

config = {
    "model_origin_url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
    "model_search_paths": ["{irene_home}/vosk/models/{file_name}"],
    "model_storage_path": "{irene_home}/vosk/models/{file_name}",
}


def _download_model() -> str:
    raw_url: str = config['model_origin_url']
    parsed_url = urlparse(raw_url)
    file_basename = f'{md5(raw_url.encode("utf-8")).hexdigest()}-{basename(parsed_url.path)}'
    try:
        return pick_random_file(config['model_search_paths'], override_vars=dict(file_name=file_basename))
    except FileNotFoundError:
        _logger.info(f"Файл модели '{file_basename}' не найден. Пытаюсь скачать.")

    target_path = first_substitution(config['model_storage_path'], override_vars=dict(file_name=file_basename))
    os.makedirs(dirname(target_path), exist_ok=True)

    urlretrieve(raw_url, target_path)

    _logger.info(f"Файл модели загружен в {target_path}")

    return target_path


_model_path = None


def receive_config(*_args, **_kwargs):
    global _model_path
    _model_path = _download_model()


def get_vosk_model_local_path(*_args, **_kwargs):
    return _model_path
