import re
from logging import getLogger
from typing import Callable, Awaitable, TypedDict, Optional, Union

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers

name = 'web_authentication'
version = '0.1.0'

_logger = getLogger(name)


class _RuleSettings(TypedDict):
    enabled: bool
    path: Optional[str]
    method: Optional[str]
    action: str
    comment: Optional[str]


class _DefaultRuleSettings(TypedDict):
    action: str


class _Config(TypedDict):
    rules: list[_RuleSettings]
    default: _DefaultRuleSettings


config: _Config = {
    'rules': [
        {
            'enabled': False,
            'path': '/api/config/configs/web_face_frontend',
            'method': None,
            'action': 'allow',
            'comment': "Разрешает доступ к настройкам веб-фронтенда",
        },
        {
            'enabled': False,
            'path': '/api/config/.*',
            'method': None,
            'action': 'deny',
            'comment': "Закрывает доступ ко всем остальным настройкам",
        },
    ],
    'default': {
        'action': 'allow',
    },
}

config_comment = """
Настройки доступа к серверу.

Доступные параметры:
- `rules`     - правила доступа, см. далее
- `default`   - действие, применяемое по-умолчанию

Каждое правило представляет собой объект, содержащий следующие поля:
- `enabled`   - включает/выключает правило
- `path`      - регулярное выражение определяющее, к каким путям применяется правило.
                Если поле отсутствует или None, то правило применяется ко всем путям.
- `method`    - HTTP метод, к которому применяется правило.
                Если поле отсутствует или None, то правило применяется ко всем методам.
- `action`    - действие, осуществляемое с запросами, соответствующими этому правилу.
                По-умолчанию доступны действия allow - разрешить доступ и deny - запретить доступ.
                Однако, можно реализовать собственные действия, например, для реализации собственного механизма
                аутентификации.

Получив запрос, сервер начнёт проходить по всем включённым правилам от первого к последнему, пока не найдёт правило,
подходящее к запросу (по path и method).
Если ни одного подходящего правила не найдено, то сервер применит действие по-умолчанию.
"""

_AuthAction = Callable[[Request, RequestResponseEndpoint], Awaitable[Response]]


def _create_action(pm: PluginManager, settings: Union[_RuleSettings, _DefaultRuleSettings]) -> _AuthAction:
    action = call_all_as_wrappers(
        pm.get_operation_sequence('crete_fastapi_auth_action'),
        None,
        settings['action'],
        settings,
        pm,
    )

    if action is None:
        raise ValueError(f"Не удалось создать действие {settings['action']} ({settings})")

    return action


class _Rule:
    def __init__(self, settings: _RuleSettings, pm: PluginManager):
        _path_setting = settings.get('path', None)
        self._path_pattern = re.compile(_path_setting) if _path_setting is not None else None
        self._method = settings.get('method', None)

        self.action = _create_action(pm, settings)

    def matches(self, req: Request) -> bool:
        if self._method is not None:
            if req.method != self._method:
                return False

        if self._path_pattern is not None:
            if not self._path_pattern.match(req.url.path):
                return False

        return True


class _RuleSet:
    def __init__(self, pm: PluginManager, settings: _Config):
        self._pm = pm
        self._rules: list[_Rule]
        try:
            self._rules, self._default = self._load_rules(settings)
        except Exception:
            _logger.exception(
                "Не удалось создать правила по изначальной конфигурации. Использую безопасный набор правил."
            )
            self._rules = []
            self._default = _action_deny

    def _load_rules(self, settings: _Config) -> tuple[list[_Rule], _AuthAction]:
        default = _create_action(self._pm, settings['default'])
        rules = [
            _Rule(rule_settings, self._pm)
            for rule_settings in settings['rules']
            if rule_settings.get('enabled') == True
        ]

        return rules, default

    def reload(self, settings: _Config):
        try:
            self._rules, self._default = self._load_rules(settings)
        except Exception:
            _logger.exception("Не удалось создать правила для новой конфигурации.")

    async def apply(self, request: Request, call_next: RequestResponseEndpoint):
        for rule in self._rules:
            if rule.matches(request):
                return await rule.action(request, call_next)

        return await self._default(request, call_next)


class _AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _rule_set is not None:
            return await _rule_set.apply(request, call_next)

        return await call_next(request)


async def _action_allow(req: Request, call_next: RequestResponseEndpoint) -> Response:
    _logger.debug("Доступ разрешён для %s %s", req.method, req.url)

    return await call_next(req)


async def _action_deny(req: Request, _call_next: RequestResponseEndpoint) -> Response:
    _logger.debug("Доступ запрещён для %s %s", req.method, req.url)

    return Response(
        status_code=403,
        content="Not allowed",
    )


def crete_fastapi_auth_action(
        nxt, prev: Optional[_AuthAction],
        action: str,
        settings: Union[_RuleSettings, _DefaultRuleSettings],
        *args, **kwargs
):
    if prev is None:
        if action == 'allow':
            prev = _action_allow
        elif action == 'deny':
            prev = _action_deny

    return nxt(prev, action, settings, *args, **kwargs)


_rule_set: Optional[_RuleSet] = None


def register_fastapi_routes(app: FastAPI, pm: PluginManager, *_args, **_kwargs):
    global _rule_set
    if _rule_set is None:
        _rule_set = _RuleSet(pm, config)

    app.add_middleware(_AuthenticationMiddleware)


def receive_config(conf: _Config, *_args, **_kwargs):
    if _rule_set is not None:
        _rule_set.reload(conf)
