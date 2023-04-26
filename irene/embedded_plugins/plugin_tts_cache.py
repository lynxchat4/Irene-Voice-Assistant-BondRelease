"""
Добавляет кеширование результатов работы TTS.

Кеш реализован в виде папки с файлами, где имя файла является хешем от типа TTS, его настроек и озвученной фразы.

Плагин так же осуществляет периодическую очистку папки кеша. В зависимости от настроек, файлы могут удаляться если:
- они не использовались дольше заданного времени
- кеш занимает больше места, чем разрешено
- файлов накопилось больше заданного количества
"""

import os
from datetime import datetime
from hashlib import sha256
from logging import getLogger
from pathlib import Path
from shutil import copy
from threading import Event
from typing import TypedDict, Optional, Any

from irene.face.abc import FileWritingTTS, TTSResultFile
from irene.face.tts_helpers import PersistentTTSResultFile, create_disposable_tts_result_file
from irene.plugin_loader.file_patterns import first_substitution
from irene.utils.metadata import MetadataMapping

name = 'tts_cache'
version = '0.1.0'

_logger = getLogger(name)


class _Config(TypedDict):
    cache_path: str
    max_files: Optional[int]
    max_size: Optional[float]
    max_age: Optional[float]
    cleanup_interval: float


config: _Config = {
    'cache_path': '{irene_home}/cache/tts',
    'max_files': -1,
    'max_size': -1,
    'max_age': -1,
    'cleanup_interval': 1.0,
}

config_comment = """
Настройки кеширования файлов TTS.

Доступные параметры:
- `cache_path`        - путь к папке, где хранятся файлы кеша
- `max_files`         - максимальное количество хранимых файлов кеша.
                        0, `null` или значение меньше 0 означают, что количество файлов не ограничено.
- `max_size`          - максимальный суммарный размер (в мибибайтах), всех файлов кеша.
                        0, `null` или значение меньше 0 означают, что размер файлов не ограничен.
- `max_age`           - максимальное время хранения (в сутках с последнего использования) файлов в кеше.
                        0, `null` или значение меньше 0 означают, что файлы кеша могут храниться сколь угодно долго.
- `cleanup_interval`  - интервал (в часах) с которым происходит очистка кеша.
"""

_terminated = Event()


def _ensure_cache_dir() -> Path:
    """
    Убеждается, что папка кеша существует и возвращает путь к ней.
    """
    cache_dir_path = Path(first_substitution(config['cache_path'])).absolute()

    cache_dir_path.mkdir(parents=True, exist_ok=True)

    return cache_dir_path


def _find_existing_file(base_name: str) -> Path:
    """
    Ищет файл с заданным базовым именем в кеше.

    Args:
        base_name:
    Returns:
        путь к найденному файлу
    Raises:
        FileNotFoundError - если подходящего файла не найдено
    """
    # В кеше может лежать несколько версий файла - оригинальный файл, созданный TTS и его варианты, преобразованные в
    # другие форматы AudioConverter'ом.
    matching = list(_ensure_cache_dir().glob(f'{base_name}.*'))

    if len(matching) == 0:
        raise FileNotFoundError()

    time = datetime.now().timestamp()

    for file_path in matching:
        # Нельзя использовать file_path.touch() так как он создаст файл если он был только что удалён потоком очистки
        os.utime(file_path, (time, time))

    # Имена преобразованных файлов будут длиннее, чем у оригинала. Поэтому, возвращаем к файлу с самым коротким именем.
    return min(matching, key=lambda it: len(it.name))


def _cache_file_sort(path: Path) -> Any:
    """
    Возвращает ключ сортировки, используемый при очистке кеша.

    Файлы сортируются от новых к старым (по mtime), среди файлов с одинаковым mtime первыми идут файлы с более коротким
    именем. Таким образом, оригинальный файл будет ближе к началу списка (и удалится с меньшей вероятностью), чем
    варианты, преобразованные в другие форматы - AudioConverter гарантирует, что mtime новых преобразованных файлов
    совпадает с mtime оригинала.
    """
    return -path.stat().st_mtime, len(path.name)


def _do_cleanup():
    _logger.info("Ищу файлы кеша, которые пора удалить")

    cache_files: list[Path] = list(_ensure_cache_dir().iterdir())
    cache_files.sort(key=_cache_file_sort)
    n_files_to_delete = 0

    if (files_limit := (config['max_files'] or 0)) > 0:
        if len(cache_files) > files_limit:
            n_files_to_delete = max(n_files_to_delete, len(cache_files) - files_limit)

            _logger.debug(
                "В кеше %d файлов, %d из них будут удалены, чтобы оставить не более %d файлов",
                len(cache_files), n_files_to_delete, files_limit,
            )

    if (size_limit := (config['max_size'] or 0)) > 0:
        size_accumulator = 0  # MiB

        for i, file in enumerate(cache_files):
            size_accumulator += file.stat().st_size / 1024 / 1024  # Bytes -> MiBytes

            if size_accumulator > size_limit:
                n_files_to_delete = max(n_files_to_delete, len(cache_files) - i)

                _logger.debug(
                    "%d из %d самых новых файлов занимают %f Мибибайт, один из них и ещё %d файл(ов) будут удалены",
                    i + 1, len(cache_files), size_accumulator, len(cache_files) - (i + 1),
                )

                break

    if (age_limit := (config['max_age'] or 0)) > 0:
        max_mtime = datetime.now().timestamp() - age_limit * 60 * 60 * 24

        for i, file in enumerate(cache_files):
            if file.stat().st_mtime < max_mtime:
                n_files_to_delete = max(n_files_to_delete, len(cache_files) - i)

                _logger.debug(
                    "Все файлы кеша начиная с %dго из %d старше %f часов и будут удалены",
                    i + 1, len(cache_files), age_limit,
                )

    if n_files_to_delete == 0:
        _logger.debug("Нет файлов, требующих удаления")
        return

    _logger.info("Собираюсь удалить %d файл(ов) кеша", n_files_to_delete)

    if n_files_to_delete == len(cache_files):
        _logger.warning(
            "Собираюсь удалить все файлы кеша (%d). Возможно, стратегия очистки кеша настроена не верно.",
            n_files_to_delete,
        )

    for file in cache_files[-n_files_to_delete:]:
        _logger.debug("Удаляю файл %s", str(file))

        file.unlink(missing_ok=True)

    _logger.debug("Удаление файлов закончено")


def _respond_with_cached_file(file_path: Path, file_base_path: Optional[str]) -> TTSResultFile:
    """
    Создаёт объект TTSResultFile для файла, хранящегося в кеше.

    Args:
        file_path: путь к файлу в кеше
        file_base_path: базовый путь файла, запрошенный клиентом
    """
    if file_base_path is not None:
        # Если клиент требует файл, лежащий в определённом месте, то копируем файл из кеша туда и возвращаем
        # DisposableTTSResultFile, чтобы клиент удалил его после использования.
        result_file = create_disposable_tts_result_file(file_base_path)
        copy(file_path, result_file.get_full_path())
        return result_file

    # Если клиенту не важно, где лежит файл - то возвращаем PersistentTTSResultFile, напрямую указывающий на файл в кеше
    return PersistentTTSResultFile(str(file_path))


class _CachingFileTTS(FileWritingTTS):
    def __init__(self, wrapped: FileWritingTTS):
        self._wrapped = wrapped

    def _get_cache_file_base_name(self, text: str) -> str:
        args_hash = sha256(self._wrapped.get_name().encode('utf-8'))
        args_hash.update(self._wrapped.get_settings_hash().encode('utf-8'))
        args_hash.update(text.encode('utf-8'))

        return args_hash.hexdigest()

    def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
        if kwargs.get('no_cache', False):
            return self._wrapped.say_to_file(text, file_base_path, **kwargs)

        cached_file_base_name = self._get_cache_file_base_name(text)

        try:
            cached_file_path = _find_existing_file(cached_file_base_name)
        except FileNotFoundError:
            cached_file_path = Path(
                self._wrapped.say_to_file(
                    text,
                    file_base_path=str(_ensure_cache_dir().joinpath(cached_file_base_name)),
                    **kwargs
                ).get_full_path()
            )

        return _respond_with_cached_file(cached_file_path, file_base_path)

    @property
    def meta(self) -> MetadataMapping:
        return self._wrapped.meta

    def get_name(self) -> str:
        return self._wrapped.get_name()

    def get_settings_hash(self) -> str:
        return self._wrapped.get_settings_hash()


def create_file_tts(nxt, prev: Optional[FileWritingTTS], config: dict[str, Any], *args, **kwargs):
    if (tts := nxt(prev, config, *args, **kwargs)) is None:
        return None

    if config.get('no_cache', False):
        return tts

    return _CachingFileTTS(tts)


def init(*_args, **_kwargs):
    _do_cleanup()


def run(*_args, **_kwargs):
    while not _terminated.wait(config['cleanup_interval'] * 360):
        try:
            _do_cleanup()
        except Exception:
            _logger.exception("Ошибка в процессе очистки кеша")

    _logger.info("Останавливаю поток очистки кеша")


def terminate(*_args, **_kwargs):
    _terminated.set()
