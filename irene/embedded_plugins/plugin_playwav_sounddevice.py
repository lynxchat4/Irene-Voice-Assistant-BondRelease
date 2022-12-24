# Playwav plugin for sounddevice engine
# author: Vladislav Janvarev

import os

import numpy
import sounddevice as sound_device
import soundfile as sound_file
from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "PlayWav through sounddevice",
        "version": "1.0",
        "require_online": False,

        "playwav": {
            "sounddevice": (init,playwav) # первая функция инициализации, вторая - проиграть wav-файл
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass

def init(core:VACore):
    pass

def playwav(core:VACore, wavfile:str):
    data_set, fsample = sound_file.read(wavfile, dtype='float32')

    # sounddevice иногда пропускает некоторое количество данных в конце записи, так что воспроизведение обрывается и
    # конец "проглатывается".
    # Похоже, причина проблемы кроется где-то в недрах библиотеки PortAudio, используемой sounddevice.
    # С.м. https://github.com/spatialaudio/python-sounddevice/issues/283
    # Добавляем немного пустых сэмплов в конец массива чтобы потерялись они, а не полезные данные.
    data_set = numpy.pad(data_set, [0, 10000], mode='constant')

    sound_device.play(data_set, fsample, blocking=True)
