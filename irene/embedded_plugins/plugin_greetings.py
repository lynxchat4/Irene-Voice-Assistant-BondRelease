from random import choice

from irene import VAApiExt

name = 'greetings'
version = '1.0.0'

config = {
    'phrases': [
        "И тебе привет!",
        "Рада тебя видеть!",
    ]
}


def _greet(va: VAApiExt, _):
    va.say(choice(config['phrases']))


define_commands = {
    "привет|доброе утро": _greet
}
