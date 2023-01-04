"""
Плагин добавляет поддержку TTS Silero V3.
"""

import os
from functools import cache
from hashlib import md5
from logging import getLogger
from os.path import basename, dirname
from typing import Optional, Any
from urllib.parse import urlparse

import torch

from irene.face.abc import FileWritingTTS, TTSResultFile
from irene.face.tts_helpers import create_disposable_tts_result_file
from irene.plugin_loader.file_patterns import pick_random_file, first_substitution

name = 'plugin_tts_silero_v3'
version = '0.1.0'

config = {
    "threads": 4,
    "silero_settings": {
        "speaker": "xenia",
        "sample_rate": 24000,
        "put_accent": True,
        "put_yo": True,
    },
    "warmup_iterations": 4,
    "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
    "model_origin_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
    "model_storage_path": "{irene_home}/silero_v3/models/{file_name}",
    "model_search_paths": ["{irene_home}/silero_v3/models/{file_name}"],
}

config_comment = """
Настройки TTS Silero V3.

Для использования другой модели измените параметр `model_origin_url` на URL файла нужной модели.
Список моделей доступен здесь: https://models.silero.ai/models/tts/

Если при использовании этого TTS первые несколько команд обрабатываются слишком медленно, попробуйте увеличить значение
параметра `warmup_iterations`.
"""

_logger = getLogger(name)


def _download_model_file() -> str:
    raw_url = config['model_origin_url']
    parsed_url = urlparse(raw_url)
    file_basename = f'{md5(raw_url.encode("utf-8")).hexdigest()}-{basename(parsed_url.path)}'
    try:
        return pick_random_file(config['model_search_paths'], override_vars=dict(file_name=file_basename))
    except FileNotFoundError:
        _logger.info(f"Файл модели '{file_basename}' не найден. Пытаюсь скачать.")

    target_path = first_substitution(config['model_storage_path'], override_vars=dict(file_name=file_basename))
    os.makedirs(dirname(target_path), exist_ok=True)

    torch.hub.download_url_to_file(raw_url, target_path)

    _logger.info(f"Файл модели скачан в '{target_path}'.")

    return target_path


@cache
def _load_model(file: str) -> Any:
    device = torch.device('cpu')
    torch.set_num_threads(config['threads'])

    model = torch.package \
        .PackageImporter(file) \
        .load_pickle("tts_models", "model")

    model.to(device)

    if (warmup_iterations := int(config['warmup_iterations'])) > 0:
        # Первые несколько запросов к модели происходят очень медленно т.к. чему-то внутри неё нужно скомпилироваться.
        # Чтобы не ждать слишком долго обработки первых реальных команд от пользователя, шлём несколько запросов в
        # процессе загрузки модели.
        # 4 раз достаточно в случае машины, на которой был написан этот плагин, на других машинах может понадобиться
        # больше.
        # Если у пользователей будут возникать дополнительные проблемы, связанные с медленным запуском Silero то можно
        # попробовать применить предложения из этого комментария: https://habr.com/ru/post/660565/#comment_24652282
        warmup_phrase = config['warmup_phrase']

        _logger.info("Разогреваюсь.")
        for _ in range(warmup_iterations):
            warmup_file = model.save_wav(
                audio_path='./warmup.wav',
                text=warmup_phrase,
                **(config['silero_settings'] or {}),
            )
            os.remove(warmup_file)

        _logger.info("Разогрев закончен.")

    return model


def _make_tts() -> FileWritingTTS:
    model = _load_model(_download_model_file())

    class SileroV3TTS(FileWritingTTS):
        def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
            file = create_disposable_tts_result_file(file_base_path, '.wav')

            model.save_wav(
                audio_path=file.get_full_path(),
                text=text,
                **(config['silero_settings'] or {}),
            )

            return file

    return SileroV3TTS()


def create_file_tts(nxt, prev: Optional[FileWritingTTS], config: dict[str, Any], *args, **kwargs):
    if config.get('type') == 'silero_v3':
        prev = prev or _make_tts()

    return nxt(
        prev,
        config,
        *args,
        **kwargs,
    )
