import asyncio
from logging import getLogger
from time import sleep
from typing import TypedDict, Optional

import irene.utils.num_to_text_ru as num_to_text
from irene import VAApiExt
from irene.brain.abc import OutputChannelNotFoundError
from irene.plugin_loader.file_patterns import pick_random_file
from irene.plugin_loader.magic_plugin import MagicPlugin

female_units_min2 = ((u'минуту', u'минуты', u'минут'), 'f')
female_units_min = ((u'минута', u'минуты', u'минут'), 'f')
female_units_sec2 = ((u'секунду', u'секунды', u'секунд'), 'f')
female_units_sec = ((u'секунда', u'секунды', u'секунд'), 'f')


class TimerPlugin(MagicPlugin):
    name = 'plugin_timer'
    version = '7.1.0'

    _logger = getLogger(name)

    class _Config(TypedDict):
        wavRepeatTimes: int
        wavPath: str

    config: _Config = {
        'wavRepeatTimes': 2,
        'wavPath': '{irene_path}/embedded_plugins/media/timer.wav',
    }

    def __init__(self) -> None:
        super().__init__()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def init(self, *_args, **_kwargs):
        self._loop = asyncio.get_running_loop()

    def define_commands(self, *_args, **_kwargs):
        return {
            "поставь таймер|поставь тайгер|таймер|тайгер": self._set_timer
        }

    def _set_timer_real(self, va: VAApiExt, time: int, text: str):
        def done_interaction(va: VAApiExt):
            try:
                for i in range(self.config['wavRepeatTimes']):
                    va.play_audio(pick_random_file(self.config['wavPath']))
                    sleep(0.2)
            except OutputChannelNotFoundError:
                va.say(" ".join(("БИП",) * self.config['wavRepeatTimes']))

            va.say(f"{text} прошло")

        async def timer_task():
            await asyncio.sleep(time)
            try:
                await self._loop.run_in_executor(
                    None,
                    va.submit_active_interaction,
                    done_interaction
                )
            except Exception:
                self._logger.exception("Ошибка при обработке таймера")

        loop = self._loop

        if loop is None:
            raise Exception("Установка таймера до вызова init()")

        loop.call_soon_threadsafe(
            loop.create_task,
            timer_task(),
        )

        va.say(f"поставила таймер на {text}")

    def _set_timer(self, va: VAApiExt, phrase: str):
        if phrase == "":
            # таймер по умолчанию - на 5 минут
            self._set_timer_real(va, 5 * 60, "пять минут")
            return

        phrase += " "

        if phrase.startswith("на "):  # вырезаем "на " (из фразы "на Х минут")
            phrase = phrase[3:]

        # ставим секунды?
        for i in range(100, 1, -1):
            txt = num_to_text.num2text(i, female_units_sec) + " "
            if phrase.startswith(txt):
                self._set_timer_real(va, i, txt)
                return

            txt2 = num_to_text.num2text(i, female_units_sec2) + " "
            if phrase.startswith(txt2):
                self._set_timer_real(va, i, txt)
                return

            txt3 = str(i) + " секунд "
            if phrase.startswith(txt3):
                self._set_timer_real(va, i, txt)
                return

        # ставим минуты?
        for i in range(100, 1, -1):
            txt = num_to_text.num2text(i, female_units_min) + " "
            if phrase.startswith(txt):
                self._set_timer_real(va, i * 60, txt)
                return

            txt2 = num_to_text.num2text(i, female_units_min2) + " "
            if phrase.startswith(txt2):
                self._set_timer_real(va, i * 60, txt)
                return

            txt3 = str(i) + " минут "
            if phrase.startswith(txt3):
                self._set_timer_real(va, i * 60, txt)
                return

        # без указания единиц измерения - ставим минуты
        for i in range(100, 1,
                       -1):  # обратный вариант - иначе "двадцать" находится быстрее чем "двадцать пять", а это неверно
            txt = num_to_text.num2text(i, female_units_min) + " "
            txt2 = num_to_text.num2text(i) + " "
            if phrase.startswith(txt2):
                self._set_timer_real(va, i * 60, txt)
                return

            txt3 = str(i) + " "
            if phrase.startswith(txt3):
                self._set_timer_real(va, i * 60, txt)
                return

        # спецкейс под одну минуту
        if phrase.startswith("один ") or phrase.startswith("одна ") or phrase.startswith("одну "):
            txt = num_to_text.num2text(1, female_units_min)
            self._set_timer_real(va, 1 * 60, txt)
            return

        # непонятно, но сохраняем контекст и переспрашиваем время
        va.say("Что после таймер?")
        va.context_set(self._set_timer)
