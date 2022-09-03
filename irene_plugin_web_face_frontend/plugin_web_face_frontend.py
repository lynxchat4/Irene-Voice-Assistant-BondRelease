from logging import getLogger
from os.path import join, dirname, isdir, isfile

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from irene.plugin_loader.magic_plugin import after

name = 'web_face_frontend'
version = '0.0.1'

_DIST_DIR = join(dirname(__file__), 'frontend-dist')
_logger = getLogger('web_face_frontend')


@after('register_plugin_api_endpoints')
def register_fastapi_routes(app: FastAPI, *_args, **_kwargs):
    if isdir(_DIST_DIR) and isfile(join(_DIST_DIR, 'index.html')):
        static_files = StaticFiles(
            directory=_DIST_DIR,
            html=True,
        )
        app.mount('/', static_files)
    else:
        _logger.error(f"Файлы веб-интерфейса в папке {_DIST_DIR} не найдены.")
