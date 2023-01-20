from logging import getLogger
from os.path import join, dirname, isdir, isfile
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from irene.plugin_loader.magic_plugin import after

name = 'web_face_frontend'
version = '0.0.1'

# Сам плагин не использует этот конфиг, однако его использует JS, выполняющийся в браузере - запрашивая его через API
# менеджера конфигураций.
config: dict[str, Any] = {
    'audioInputEnabled': True,
    'audioOutputEnabled': True,
    'preferStreamingInput': True,
    'microphoneSampleRate': 44100,
    'autoReload': True,
}

config_comment = """
Настройки браузерного интерфейса

Доступные параметры:

- `audioInputEnabled`     - включает голосовой ввод команд
- `audioOutputEnabled`    - включает вывод аудио (звуков и голосовых ответов ассистента)
- `preferStreamingInput`  - если включено, то клиент будет при возможности использовать потоковую передачу звука с
                            микрофона для распознания команд на сервере, а не распознавать голосовые команды
                            самостоятельно
- `microphoneSampleRate`  - частота дискретизации аудио при прослушивании микрофона
- `autoReload`            - автоматически обновляет страницу при изменении настроек браузерного интерфейса
"""

_DIST_DIRS = [
    join(dirname(__file__), 'frontend-dist'),
    join(dirname(__file__), '../frontend/dist')
]
_logger = getLogger(name)


def _find_frontend_dist_dir() -> str:
    for d in _DIST_DIRS:
        if isdir(d) and isfile(join(d, 'index.html')):
            return d

    raise Exception("Файлы веб-интерфейса не найдены")


@after('register_plugin_api_endpoints')
def register_fastapi_routes(app: FastAPI, *_args, **_kwargs):
    static_files = StaticFiles(
        directory=_find_frontend_dist_dir(),
        html=True,
    )
    app.mount('/', static_files)
