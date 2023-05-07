import asyncio
from logging import getLogger
from os.path import join, dirname, isdir, isfile
from typing import Any

from fastapi import FastAPI, APIRouter
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from irene.plugin_loader.file_patterns import match_files
from irene.plugin_loader.magic_plugin import after

name = 'web_face_frontend'
version = '0.1.0'

# Большую часть полей использует не сам плагин, а JS, выполняющийся в браузере - запрашивая его через API менеджера
# конфигураций.
config: dict[str, Any] = {
    'audioInputEnabled': True,
    'audioOutputEnabled': True,
    'preferStreamingInput': True,
    'microphoneSampleRate': 44100,
    'autoReload': True,
    'hideConfiguration': False,
    'customCssPaths': ['{irene_home}/frontend/*.css'],
    'customCss': '\n\n',
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
- `hideConfiguration`     - скрывает страницу настроек в веб-интерфейсе.
                            Важно: включение этой опции не влияет на возможность изменения настроек через REST API, а
                            только скрывает графический интерфейс на веб-странице.
- `customCssPaths`        - шаблоны путей к файлам, содержащим пользовательские CSS-стили.
- `customCss`             - пользовательские CSS-стили.
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


def _load_custom_css():
    css_chunks = [config['customCss']]

    for file_path in sorted(match_files(config['customCssPaths'])):
        with open(file_path, 'r') as file:
            css_chunks.append(file.read())

    return '\n'.join(css_chunks)


def register_fastapi_endpoints(router: APIRouter, *_args, **_kwargs):
    @router.get('/custom-styles.css')
    async def get_custom_styles():
        return Response(
            await asyncio.get_running_loop().run_in_executor(None, _load_custom_css),
            media_type='text/css',
        )
