"""
Загружает модель для движка распознания речи Vosk.

В настройках указывается публичный URL, по которому расположен архив с моделью.
Если файл не был загружен ранее, то он будет загружен при запуске приложения или при изменении конфигурации плагина.
"""

import os
import tempfile
import zipfile
from functools import cache, lru_cache
from hashlib import md5
from logging import getLogger
from os.path import basename, dirname, isdir, join
from shutil import rmtree, move
from typing import Optional, Callable, Any
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
    "model_cache_size": 1,
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


_model_path: Optional[str] = None


def receive_config(*_args, **_kwargs):
    global _model_path
    _model_path = _download_model()


def get_vosk_model_local_path(*_args, **_kwargs) -> Optional[str]:
    return _model_path


def _get_extraction_path_for_archive(archive_path: str) -> str:
    return archive_path + '.extracted'


def _find_model(zip_info: list[zipfile.ZipInfo]) -> Optional[zipfile.ZipInfo]:
    for entry in zip_info:
        def has_sub_path(p: str) -> bool:
            return any(it.filename == (entry.filename + p) for it in zip_info)

        if entry.is_dir() and \
                has_sub_path('am/final.mdl') and \
                has_sub_path('graph/phones/word_boundary.int') and \
                has_sub_path('conf/model.conf'):
            return entry

    return None


def get_extracted_vosk_model_path(*args, **kwargs) -> Optional[str]:
    archive_path = get_vosk_model_local_path(*args, **kwargs)

    if archive_path is None:
        return None

    extracted_path = _get_extraction_path_for_archive(archive_path)

    if isdir(extracted_path):
        if os.stat(extracted_path).st_mtime >= os.stat(archive_path).st_mtime:
            _logger.debug("Похоже, архив %s уже извлечён в %s", archive_path, extracted_path)
            return extracted_path
        else:
            rmtree(extracted_path)

    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            model_entry = _find_model(zip_file.filelist)

            if model_entry is None:
                _logger.error("Не удалось найти модель в архиве %s", archive_path)
                return None

            with tempfile.TemporaryDirectory() as temp_dir:
                for entry in zip_file.filelist:
                    if entry.filename.startswith(model_entry.filename):
                        zip_file.extract(entry, temp_dir)

                move(join(temp_dir, model_entry.filename), extracted_path)

        return extracted_path
    except Exception:
        rmtree(extracted_path)
        raise


@cache
def _get_model_loader() -> Callable[[str], Optional[Any]]:
    cache_size: Optional[int] = config['model_cache_size']

    @lru_cache(maxsize=cache_size)
    def _load_vosk_model(path: str):
        try:
            from vosk import Model
        except ImportError:
            _logger.error(
                "Пакет vosk не установлен"
            )
            return None

        try:
            model = Model(path)
        except Exception as e:
            _logger.exception("Ошибка при загрузке модели из %s", path)
            return None

        return model

    return _load_vosk_model


def get_vosk_model(nxt, prev, *args, **kwargs):
    if prev is None and (model_path := get_extracted_vosk_model_path(*args, **kwargs)) is not None:
        prev = _get_model_loader()(model_path)

    return nxt(
        prev,
        *args, **kwargs,
    )
