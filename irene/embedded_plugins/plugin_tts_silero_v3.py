"""
Плагин добавляет поддержку TTS Silero V3.
"""

import os
from functools import cache
from hashlib import md5
from logging import getLogger
from os.path import basename, dirname
from typing import Optional, Any, TypedDict, Iterable
from urllib.parse import urlparse

import torch

import irene.utils.all_num_to_text as all_num_to_text
from irene.face.abc import FileWritingTTS, TTSResultFile
from irene.face.tts_helpers import create_disposable_tts_result_file
from irene.plugin_loader.file_patterns import first_substitution, match_files
from irene.plugin_loader.utils.snapshot_hash import snapshot_hash
from irene.utils.metadata import MetadataMapping

name = 'plugin_tts_silero_v3'
version = '0.3.1'


class _Config(TypedDict):
    threads: int
    model_storage_path: str
    model_search_paths: list[str]


config: _Config = {
    "threads": 4,
    "model_storage_path": "{irene_home}/silero_v3/models/{file_name}",
    "model_search_paths": ["{irene_home}/silero_v3/models/{file_name}"],
}

config_comment = """
Настройки адаптера TTS Silero V3.

Доступные параметры:

- ``model_storage_path``      - шаблон пути, по которому плагин будет сохранять скаченные файлы моделей.
- ``model_search_paths``      - шаблоны путей, по которым плагин будет искать файлы моделей для Silero.
                                Как правило, должен содержать шаблон, указанный в параметре ``model_storage_path`` и
                                по-умолчанию содержит только его.
                                Дополнительные пути могут быть добавлены если сборка приложения (например, Docker-образ)
                                содержит неизменяемые предварительно загруженные файлы моделей.
- ``threads``                 - количество потоков, используемых для синтеза речи.
"""

_logger = getLogger(name)


def _get_model_files(url: str) -> Iterable[str]:
    """
    Возвращает пути к файлам, в которых следует искать модель, скачанную по переданному url'у.
    """
    parsed_url = urlparse(url)
    file_basename = f'{md5(url.encode("utf-8")).hexdigest()}-{basename(parsed_url.path)}'

    # Сначала перебираем все подходящие по названию существующие файлы.
    # Ранее могли быть скачаны битые файлы, модель из которых загрузить не получится, обнаружив такой файл, вызывающая
    # сторона попросит у _get_model_files следующий вариант.
    yield from match_files(config['model_search_paths'], override_vars=dict(file_name=file_basename))

    # Потом пытаемся скачать файл
    target_path = first_substitution(
        config['model_storage_path'], override_vars=dict(file_name=file_basename))
    os.makedirs(dirname(target_path), exist_ok=True)

    torch.hub.download_url_to_file(url, target_path)

    _logger.info(f"Файл модели скачан в '{target_path}'.")

    yield target_path


@cache
def _get_device() -> torch.device:
    dev = torch.device('cpu')
    torch.set_num_threads(config['threads'])

    return dev


@cache
def _load_model_from_file(file_path: str) -> Any:
    model = torch.package \
        .PackageImporter(file_path) \
        .load_pickle("tts_models", "model")

    _logger.debug("Загружена модель из %s", file_path)

    model.to(_get_device())

    return model


def _load_model(model_url: str) -> Any:
    for file_path in _get_model_files(model_url):
        try:
            return _load_model_from_file(file_path)
        except Exception:
            _logger.exception("Не удалось загрузить модель из %s", file_path)

    raise Exception(f"Не удалось загрузить модель из {model_url}")


def _warmup_model(model, voice_settings: dict[str, Any]):
    if (warmup_iterations := int(voice_settings.get('warmup_iterations', 0))) > 0:
        # Первые несколько запросов к модели происходят очень медленно т.к. чему-то внутри неё нужно скомпилироваться.
        # Чтобы не ждать слишком долго обработки первых реальных команд от пользователя, шлём несколько запросов в
        # процессе загрузки модели.
        # 4 раз достаточно в случае машины, на которой был написан этот плагин, на других машинах может понадобиться
        # больше.
        # Если у пользователей будут возникать дополнительные проблемы, связанные с медленным запуском Silero то можно
        # попробовать применить предложения из этого комментария: https://habr.com/ru/post/660565/#comment_24652282
        warmup_phrase = voice_settings.get('warmup_phrase', None)

        if warmup_phrase is None:
            _logger.warning(
                "Для модели включен разогрев (warmup_iterations=%i), но не выбрана фраза для разогрева",
                warmup_iterations,
            )
            return

        _logger.info("Разогреваюсь.")
        for _ in range(warmup_iterations):
            warmup_file = model.save_wav(
                audio_path='./warmup.wav',
                text=warmup_phrase,
                **(voice_settings['silero_settings'] or {}),
            )
            os.remove(warmup_file)

        _logger.info("Разогрев закончен.")


def _make_tts(instance_config: dict[str, Any]) -> Optional[FileWritingTTS]:
    model_url = instance_config['model_url']

    model = _load_model(model_url)

    full_settings = instance_config.get('silero_settings', {})

    _warmup_model(model, full_settings)

    all_num_to_text.load_language('ru-RU')

    class SileroV3TTS(FileWritingTTS):
        def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
            file = create_disposable_tts_result_file(file_base_path, '.wav')

            # TODO: Это не будет работать с другими языками кроме русского. Нужно более универсальное решение.
            text = all_num_to_text.all_num_to_text(text)

            model.save_wav(
                audio_path=file.get_full_path(),
                text=text,
                **full_settings,
            )

            return file

        def get_settings_hash(self) -> str:
            return str(snapshot_hash(full_settings) ^ snapshot_hash(model_url))

        @property
        def meta(self) -> MetadataMapping:
            return {
                'silero.speaker': full_settings.get('speaker'),
                **instance_config.get('metadata', {}),
            }

    return SileroV3TTS()


def create_file_tts(nxt, prev: Optional[FileWritingTTS], config: dict[str, Any], *args, **kwargs):
    if config.get('type') == 'silero_v3':
        prev = prev or _make_tts(config)

    return nxt(
        prev,
        config,
        *args,
        **kwargs,
    )
