import os
import uuid
from os.path import join
from tempfile import gettempdir
from typing import Optional, Callable, Any

from irene.brain.abc import AudioOutputChannel, TextOutputChannel
from irene.face.abc import ImmediatePlaybackTTS, FileWritingTTS, TTSResultFile, MuteGroup
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.utils.metadata import MetadataMapping


class DisposableTTSResultFile(TTSResultFile):
    """
    Файл с результатами работы TTS, который может быть удалён после использования (воспроизведения).
    """

    def __init__(self, full_path: str):
        super().__init__()
        self._full_path = full_path

    def get_full_path(self) -> str:
        return self._full_path

    def release(self):
        os.remove(self._full_path)


def create_disposable_tts_result_file(
        preferred_path: Optional[str],
        extension: Optional[str] = None
) -> DisposableTTSResultFile:
    """
    Создаёт ``DisposableTTSResultFile`` с учётом желаемого имени файла и расширения.

    Если желаемое имя файла не передано, то генерируется временный файл в стандартной папке для временных файлов.

    Args:
        preferred_path:
            желаемое имя файла или ``None`` для создания временного файла
        extension:
            желаемое расширение файла

    Returns:
        готовый экземпляр ``DisposableTTSResultFile``
    """
    if preferred_path is None:
        preferred_path = join(gettempdir(), f'tts_{uuid.uuid4()}')

    if extension is not None:
        if not extension.startswith('.'):
            extension = f'.{extension}'

        if not preferred_path.endswith(extension):
            preferred_path = preferred_path + extension

    return DisposableTTSResultFile(preferred_path)


def file_writing_tts_from_callbacks(
        name: str,
        core: Any,
        init: Callable[[Any], None],
        say_to_file: Callable[[Any, str, str], None],
):
    initialized = False

    class _FileWritingTTSImpl(FileWritingTTS):
        def __init__(self):
            nonlocal initialized

            if not initialized:
                init(core)
                initialized = True

        def get_name(self) -> str:
            return name

        def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
            df = create_disposable_tts_result_file(file_base_path, '.wav')
            say_to_file(core, text, df.get_full_path())  # type: ignore
            return df

    return _FileWritingTTSImpl


def immediate_playback_tts_from_callbacks(
        name: str,
        core: Any,
        init: Callable[[Any], None],
        say: Callable[[Any, str], None],
):
    class _ImmediatePlaybackTTSImpl(ImmediatePlaybackTTS):
        def __init__(self):
            init(core)

        def get_name(self) -> str:
            return name

        def say(self, text: str, **kwargs):
            say(core, text)  # type: ignore

    return _ImmediatePlaybackTTSImpl


class FilePlaybackTTS(ImmediatePlaybackTTS):
    """
    Адаптер, превращающий ``FileWritingTTS`` (TTS-движок, пишущий результат в файл) в ``ImmediatePlaybackTTS`` (TTS
    движок, воспроизводящий речь немедленно) за счёт использования аудио-выхода (``AudioOutputChannel``).
    """

    __slots__ = ('_tts', '_ao', '_tmp')

    def __init__(
            self,
            file_writing: FileWritingTTS,
            playback_channel: AudioOutputChannel,
            temp_file_path: Optional[str] = None,
    ):
        self._tts = file_writing
        self._ao = playback_channel
        self._tmp = temp_file_path

    def get_name(self) -> str:
        return self._tts.get_name()

    def get_settings_hash(self) -> str:
        return self._tts.get_settings_hash()

    def say(self, text: str, **kwargs):
        with self._tts.say_to_file(text, self._tmp, **kwargs) as f:
            self._ao.send_file(f.get_full_path(), alt_text=text)

    @property
    def meta(self) -> MetadataMapping:
        return {**self._tts.meta, **self._ao.meta}


class ImmediatePlaybackTTSOutput(TextOutputChannel):
    """
    Реализация ``SpeechOutputChannel``, делегирующая вывод речи экземпляру TTS-движка (``ImmediatePlaybackTTS``).
    """
    __slots__ = ('_tts', '_mg')

    def __init__(self, tts: ImmediatePlaybackTTS, mute_group: MuteGroup = NULL_MUTE_GROUP):
        self._tts = tts
        self._mg = mute_group

    def send(self, text: str, **kwargs):
        with self._mg.muted():
            self._tts.say(text, **kwargs)

    @property
    def meta(self) -> MetadataMapping:
        return {**self._tts.meta, 'is_speech': True}
