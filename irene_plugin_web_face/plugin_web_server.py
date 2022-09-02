import asyncio
import threading
from logging import getLogger
from typing import Optional

import uvicorn
from fastapi import FastAPI, APIRouter

from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin


class WebServerPlugin(MagicPlugin):
    name = 'face_web_server'
    version = '0.0.1'

    config = {
        'host': '0.0.0.0',
        'port': 8086,
    }

    config_comment = """
    Настройки веб-сервера uvicorn.

    Полный список опций доступен здесь: https://www.uvicorn.org/settings/

    Этот конфиг передаётся в метод uvicorn.run, соответственно следует использовать имена параметров, написанные через
    нижнее подчёркивание (ssl_certfile, ssl_keyfile и т.д. и т.п.).
    """

    _logger = getLogger(name)

    def __init__(self):
        super().__init__()

        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    def _create_app(self, pm: PluginManager):
        app = FastAPI(
            title="Ирина",
            version=self.version,
        )

        api_root_router = APIRouter()

        for step in pm.get_operation_sequence('register_fastapi_endpoints'):
            router = APIRouter()

            step.step(router, pm)

            api_root_router.include_router(router, prefix=f'/{step.plugin.name}')

        app.include_router(api_root_router, prefix='/api')

        return app

    def run(self, pm: PluginManager, *_args, **_kwargs):
        self._thread = threading.current_thread()

        if 'reload' in self.config or 'workers' in self.config:
            self._logger.warning(f"Конфигурация содержит параметры reload и/или workers. Они будут проигнорированы.")

        uvicorn_config = uvicorn.Config(
            self._create_app(pm),
            **self.config
        )

        uvicorn_config.workers = 1
        uvicorn_config.reload = False

        self._server = uvicorn.Server(uvicorn_config)

        asyncio.run(self._server.serve())

    def terminate(self, *_args, **_kwargs):
        if self._server is not None:
            self._server.should_exit = True
            self._thread.join()
