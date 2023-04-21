"""
Преобразует аудио-файлы в различные форматы с использованием библиотеки soundfile (использующей libsndfile под капотом).

В отличие от плагина plugin_audio_converter_ffmpeg, в большинстве случаев не требует дополнительных зависимостей -
soundfile уже используется при локальном воспроизведении звука через sounddevice. Однако, может поддерживать меньше
форматов файлов.
"""

import soundfile  # type: ignore

from irene.plugin_loader.magic_plugin import after
from irene.utils.audio_converter import AudioConverter

name = 'audio_converter_soundfile'
version = '0.1.0'


class _SoundfileAudioConverter(AudioConverter):
    def convert_to(self, file: str, dst_file: str, to_format: str):
        with soundfile.SoundFile(file, 'r') as isf:
            with soundfile.SoundFile(
                    dst_file, 'w',
                    samplerate=isf.samplerate,
                    channels=isf.channels,
            ) as osf:
                for blk in isf.blocks(blocksize=1024, dtype='float32'):
                    osf.write(blk)


@after('ffmpeg')
def get_audio_converter(nxt, prev, *args, **kwargs):
    prev = prev or _SoundfileAudioConverter()
    return nxt(prev, *args, **kwargs)
