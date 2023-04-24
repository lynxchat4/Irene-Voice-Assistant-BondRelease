"""
Добавляет поддержку TTS bark (https://github.com/suno-ai/bark).

Для работы нужно установить сам bark:

pip install git+https://github.com/suno-ai/bark.git

Этот TTS практически бесполезен, очень низкопроизводителен, но иногда забавно галлюцинирует.

Пример профиля (для voice_profiles):

voiceProfiles:
  bark_1:
    enabled: true
    metadata:
      language.ru: true
      language.en: true
      language.de: true
    tts_settings:
      type: bark
      # prompt: ru_speaker_1
      # prefix_prompt: "[clears throat] ♪"
"""

from typing import Optional, Any

from irene.face.abc import FileWritingTTS, TTSResultFile
from irene.face.tts_helpers import create_disposable_tts_result_file
from irene.plugin_loader.utils.snapshot_hash import snapshot_hash

try:
    import bark  # type: ignore
    from scipy.io.wavfile import write as write_wav  # type: ignore
except ImportError:
    pass
else:
    name = 'tts_bark'
    version = '0.1.0-alpha0'

    config = {
        'model_options': {
            'text_use_gpu': True,
            'text_use_small': True,
            'coarse_use_gpu': True,
            'coarse_use_small': True,
            'fine_use_gpu': True,
            'fine_use_small': True,
            'codec_use_gpu': True,
            'force_reload': False,
        },
    }

    _preloaded_models_options = None

    class _BarkTTS(FileWritingTTS):
        def __init__(self, settings: dict[str, Any]):
            self._prompt = settings.get('prompt', None)
            self._prefix_prompt = settings.get('prefix_prompt', '')

        def get_name(self) -> str:
            return 'bark'

        def get_settings_hash(self) -> str:
            return str(snapshot_hash(_preloaded_models_options) ^ snapshot_hash((self._prompt, self._prefix_prompt)))

        def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
            file = create_disposable_tts_result_file(file_base_path)

            audio = bark.generate_audio(
                ' '.join((self._prefix_prompt, text)).strip(),
                history_prompt=self._prompt
            )

            write_wav(file.get_full_path(), bark.SAMPLE_RATE, audio)

            return file

    def init(*_args, **_kwargs):
        global _preloaded_models_options
        _preloaded_models_options = {**config['model_options']}

        bark.preload_models(**_preloaded_models_options)

    def create_file_tts(nxt, prev: Optional[FileWritingTTS], config: dict[str, Any], *args, **kwargs):
        if config.get('type') == 'bark':
            prev = prev or _BarkTTS(config)

        return nxt(
            prev,
            config,
            *args,
            **kwargs,
        )
