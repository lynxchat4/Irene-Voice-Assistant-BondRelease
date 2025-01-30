"""
Добавляет API для отправки/озвучивания простых уведомлений.
"""

from typing import Optional

from irene.brain.abc import Brain, VAApiExt

name = "notification_api"
version = "0.1.0"

_brain: Optional[Brain] = None


def get_brain(nxt, *args, **kwargs):
    global _brain

    b = nxt(*args, **kwargs)
    if _brain is None:
        _brain = b
    return b


def register_fastapi_endpoints(router, *_args, **_kwargs) -> None:
    from fastapi import APIRouter, Body, HTTPException
    from pydantic import BaseModel, Field

    r: APIRouter = router

    class NotificationModel(BaseModel):
        text: str = Field(
            title="Текст уведомления"
        )

    @r.post('/notify', name="Отправка уведомления")
    def notify(notification: NotificationModel = Body()):
        if _brain is None:
            raise HTTPException(503, "Мозг не найден")

        def interaction(va: VAApiExt):
            va.say(notification.text)

        _brain.submit_active_interaction(interaction)
