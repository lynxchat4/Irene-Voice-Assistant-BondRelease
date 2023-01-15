"""
Плагин добавляет поддержку TTS Silero V3.
"""

import os
from functools import cache
from hashlib import md5
from logging import getLogger
from os.path import basename, dirname
from typing import Optional, Any, Mapping
from urllib.parse import urlparse

import torch

from irene.face.abc import FileWritingTTS, TTSResultFile
from irene.face.tts_helpers import create_disposable_tts_result_file
from irene.plugin_loader.file_patterns import pick_random_file, first_substitution
from irene.plugin_loader.utils.snapshot_hash import snapshot_hash
from irene.utils.mapping_match import mapping_match

name = 'plugin_tts_silero_v3'
version = '0.2.0'

config: dict[str, Any] = {
    "voices": [
        {
            "silero_settings": {
                "speaker": "xenia",
                "sample_rate": 24000,
                "put_accent": True,
                "put_yo": True,
            },
            "metadata": {
                "locale": "ru",
                "locale.ru": True,
                "gender": "female",
                "gender.female": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
            "model_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
        },
        {
            "silero_settings": {
                "speaker": "eugene",
                "sample_rate": 24000,
                "put_accent": True,
                "put_yo": True,
            },
            "metadata": {
                "locale": "ru",
                "locale.ru": True,
                "gender": "male",
                "gender.male": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "В недрах тундры выдры в гетрах тырят в вёдра ядра кедров",
            "model_url": "https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
        },
        {
            "silero_settings": {
                "speaker": "en_0",
                "sample_rate": 24000,
            },
            "metadata": {
                "locale": "en",
                "locale.en": True,
                "gender": "female",
                "gender.female": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "Can you can a canned can into an un-canned can like a canner can can a canned can into "
                             "an un-canned can?",
            "model_url": "https://models.silero.ai/models/tts/en/v3_en.pt",
        },
        {
            "silero_settings": {
                "speaker": "en_1",
                "sample_rate": 24000,
            },
            "metadata": {
                "locale": "en",
                "locale.en": True,
                "gender": "male",
                "gender.male": True,
            },
            "warmup_iterations": 4,
            "warmup_phrase": "Can you can a canned can into an un-canned can like a canner can can a canned can into "
                             "an un-canned can?",
            "model_url": "https://models.silero.ai/models/tts/en/v3_en.pt",
        },
    ],
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
- ``voices``                  - список шаблонов голосов.

Параметры шаблона голоса:

- ``model_url``               - URL файла модели.
                                Как правило, URL файла из этого списка: https://models.silero.ai/models/tts/.
- ``silero_settings``         - объект с параметрами, передаваемыми в функцию синтеза речи.
                                Как правило, содержит поля ``speaker`` - имя голоса и ``sample_rate`` - частота
                                дискретизации синтезированного звука.
                                Может содержать дополнительные параметры, в зависимости от модели.
- ``metadata``                - Объект с метаданными голоса.
                                Используется при выборе шаблона голоса и затем при выборе канала вывода.
                                Как правило, содержит язык модели и гендер голоса.
                                Можно добавлять дополнительные метки, на своё усмотрение.
- ``warmup_iterations``       - Количество запросов, отправляемых для разогрева модели.
                                Silero может очень медленно обрабатывать первые несколько запросов, так что чтобы
                                уменьшить задержки при реальной работе с пользователем, несколько запросов отправляются
                                в процессе инициализации модели.
                                Если приложение стартует слишком медленно, то можно уменьшить количество запросов
                                (пожертвовав задержками при работе приложения), если задержки при первых запросах ещё
                                остаются, а время запуска не критично, то можно наоборот увеличить количество запросов.
- ``warmup_phrase``           - Фраза, используемая для разогрева TTS.
                                Нужна фраза, на языке, поддерживаемом моделью.

Использование этого TTS в других плагинах (например в ``plugin_out_tts_serverside`` для вывода речи через веб-интерфейс,
в ``face_local`` для воспроизведения речи локально или в ``telegram_output_audio`` для озвучения голосовых сообщений в
Telegram) настраивается примерно следующим образом:

```yaml
tts:
  # Указываем, что нужно использовать TTS Silero
  type: "silero_v3"
  voice_selector:
    # Выбираем первый русскоязычный шаблон женского голоса
    locale.ru: true
    gender.female: true
  silero_settings:
    # Можно изменить некоторые настройки
    sample_rate: 48000
  metadata:
    # Или добавить дополнительные метаданные
    some_label: true
```

или можно определить новый голос, не используя шаблон:

```yaml
tts:
  type: "silero_v3"
  voice:
    model_url: https://models.silero.ai/models/tts/de/v3_de.pt
    silero_settings:
      sample_rate: 24000
    warmup_iterations: 4
    warmup_phrase: "Fischers Fritze fischt frische Fische, Frische Fische fischt Fischers Fritze."
    metadata:
      locale: de
      locale.de: true
```
"""

_logger = getLogger(name)


def _download_model_file(url: str) -> str:
    parsed_url = urlparse(url)
    file_basename = f'{md5(url.encode("utf-8")).hexdigest()}-{basename(parsed_url.path)}'
    try:
        return pick_random_file(config['model_search_paths'], override_vars=dict(file_name=file_basename))
    except FileNotFoundError:
        _logger.info(f"Файл модели '{file_basename}' не найден. Пытаюсь скачать.")

    target_path = first_substitution(config['model_storage_path'], override_vars=dict(file_name=file_basename))
    os.makedirs(dirname(target_path), exist_ok=True)

    torch.hub.download_url_to_file(url, target_path)

    _logger.info(f"Файл модели скачан в '{target_path}'.")

    return target_path


@cache
def _get_device() -> torch.device:
    dev = torch.device('cpu')
    torch.set_num_threads(config['threads'])

    return dev


@cache
def _load_model(file: str) -> Any:
    model = torch.package \
        .PackageImporter(file) \
        .load_pickle("tts_models", "model")

    model.to(_get_device())

    return model


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


def _pick_voice_settings(instance_config: dict[str, Any]) -> Optional[dict[str, Any]]:
    if (settings := instance_config.get('voice')) is not None:
        return settings

    for voice_config in config['voices']:
        if mapping_match(voice_config.get('metadata', {}), instance_config.get('voice_selector', {})):
            return voice_config

    return None


def _make_tts(instance_config: dict[str, Any]) -> Optional[FileWritingTTS]:
    voice_settings = _pick_voice_settings(instance_config)

    if voice_settings is None:
        return None

    model_url = voice_settings['model_url']

    model = _load_model(_download_model_file(model_url))

    full_settings = {
        **voice_settings['silero_settings'],
        **instance_config.get('silero_settings', {})
    }

    _warmup_model(model, full_settings)

    class SileroV3TTS(FileWritingTTS):
        def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
            file = create_disposable_tts_result_file(file_base_path, '.wav')

            model.save_wav(
                audio_path=file.get_full_path(),
                text=text,
                **full_settings,
            )

            return file

        def get_settings_hash(self) -> str:
            return str(snapshot_hash(full_settings) ^ hash(model_url))

        @property
        def meta(self) -> Mapping[str, Any]:
            return {
                'silero.speaker': full_settings.get('speaker'),
                **voice_settings.get('metadata', {}),
                **instance_config.get('metadata', {})
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
