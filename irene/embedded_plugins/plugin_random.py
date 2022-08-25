from random import choice

from irene import VAApiExt

name = 'random'
version = '2.0'

_COIN_VARIANTS = ["Выпал орел", "Выпала решка"]
_DICE_VARIANTS = ["Выпала единица", "Выпало два", "Выпало три", "Выпало четыре", "Выпало пять", "Выпало шесть"]


def _play_coin(va: VAApiExt, _text: str):
    va.say(choice(_COIN_VARIANTS))


def _play_dice(va: VAApiExt, _text: str):
    va.say(choice(_DICE_VARIANTS))


define_commands = {
    "подбрось|брось": {
        "монету|монетку": _play_coin,
        "кубик|кость": _play_dice,
    }
}
