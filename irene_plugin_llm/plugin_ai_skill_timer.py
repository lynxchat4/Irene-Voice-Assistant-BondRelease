import asyncio
from asyncio import AbstractEventLoop, get_running_loop
from logging import getLogger
from time import sleep
from typing import Optional, Annotated, TypedDict

from annotated_types import Ge
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from irene import VAApiExt
from irene.brain.abc import OutputChannelNotFoundError
from irene.constants.time_units_ru import HOUR, MINUTE, SECOND
from irene.constants.word_forms import WordCaseRU
from irene.plugin_loader.file_patterns import pick_random_file
from irene.plugin_loader.magic_plugin import operation
from irene.utils.pronounce_numbers_ru import pronounce_integer

name = 'ai_skill_timer'
version = '0.1.0'

_logger = getLogger(name)


class _Config(TypedDict):
    wavRepeatTimes: int
    wavPath: str


config: _Config = {
    'wavRepeatTimes': 2,
    'wavPath': '{irene_path}/embedded_plugins/media/timer.wav',
}

config_comment = """
Настройки таймера.

Параметры:
- `wavPath`           - путь к аудио файлу, проигрываемому перед сообщением о срабатывании таймера.
- `wavRepeatTimes`    - количество проигрываний аудио файла.
"""

_loop: Optional[AbstractEventLoop] = None


async def init(*_args, **_kwargs):
    global _loop
    _loop = get_running_loop()


@operation('lc_tools')
@tool(parse_docstring=True)
def set_timer(
        hours: Annotated[int, Ge(ge=0)],
        minutes: Annotated[int, Ge(ge=0)],
        seconds: Annotated[int, Ge(ge=0)],
        run_config: RunnableConfig,
        message: Optional[str] = None,
) -> str:
    """
    Set timer for specific time.
    You must specify hours, minutes and seconds for it. All must be integers.
    If no specifications, set timer for 5 minutes, 0 hours, 0 seconds.
    Если указывается, например, на "полминуты", сконвертируй их в integer величины.
    Например, полминуты будет 30 секунд, полчаса - 30 минут.

    Args:
        hours: количество часов, на которое ставится таймер
        minutes: количество минут, на которое ставится таймер
        seconds: количество секунд, на которое ставится таймер
        message: сообщение, которое нужно озвучить по истечение отсчёта
        run_config:
    """
    va: VAApiExt = run_config['configurable']['irene_va_api']
    assert isinstance(va, VAApiExt)

    if seconds == 0 and minutes == 0 and hours == 0:
        return "Нельзя поставить таймер на 0"

    minutes += seconds // 60
    seconds %= 60
    hours += minutes // 60
    minutes %= 60

    texts: list[str] = []

    if hours > 0:
        texts.extend(pronounce_integer(hours, HOUR, WordCaseRU.NOMINATIVE))
    if minutes > 0:
        texts.extend(pronounce_integer(minutes, MINUTE, WordCaseRU.NOMINATIVE))
    if seconds > 0:
        texts.extend(pronounce_integer(seconds, SECOND, WordCaseRU.NOMINATIVE))

    text = ' '.join(texts)

    if message is None or len(message) == 0 or message.isspace():
        message = f"{text} прошло"

    def done_interaction(va: VAApiExt):
        try:
            for i in range(config['wavRepeatTimes']):
                va.play_audio(pick_random_file(config['wavPath']))
                sleep(0.2)
        except OutputChannelNotFoundError:
            va.say(" ".join(("БИП",) * config['wavRepeatTimes']))

        assert isinstance(message, str)
        va.say(message)

    async def timer_task():
        await asyncio.sleep(seconds + 60 * (minutes + 60 * hours))
        try:
            await _loop.run_in_executor(
                None,
                va.submit_active_interaction,
                done_interaction
            )
        except Exception:
            _logger.exception("Ошибка при обработке таймера")

    loop = _loop

    if loop is None:
        raise Exception("Установка таймера до вызова init()")

    loop.call_soon_threadsafe(
        loop.create_task,
        timer_task(),
    )

    _logger.info("Установлен таймер на %s с сообщением: %s", text, message)

    return f"Установлен таймер на {text}"
