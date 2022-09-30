from logging import getLogger
from os.path import join, dirname, isdir, isfile

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from irene.plugin_loader.magic_plugin import after

name = 'web_face_frontend'
version = '0.0.1'

_DIST_DIRS = [
    join(dirname(__file__), 'frontend-dist'),
    join(dirname(__file__), '../frontend/dist')
]
_logger = getLogger('web_face_frontend')


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
