"""
Позволяет клиентам загружать модель для Vosk STT.

Как правило, возвращается модель, заданная в настройках плагина vosk_model_loader.
"""

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_until_first_result

name = 'expose_vosk_model'
version = '1.0.0'


def register_fastapi_endpoints(router: APIRouter, pm: PluginManager, *_args, **_kwargs):
    @router.get(
        '/model.zip',
        response_class=FileResponse,
        name="Актуальная модель Vosk STT",
        responses={
            503: {
                "description": "Возвращается если модель не удалось загрузить",
            },
        },
    )
    def get_model_file():
        """
        Возвращает актуальный файл модели для Vosk.
        """
        local_path = call_until_first_result(pm.get_operation_sequence('get_vosk_model_local_path'))

        if not local_path:
            raise HTTPException(503)

        return FileResponse(
            local_path,
        )
