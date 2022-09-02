import re
from abc import ABC
from types import ModuleType
from typing import Iterable, Collection, Callable, TypeVar

from irene.plugin_loader.abc import Plugin, OperationStep

_SIMPLE_PLUGIN_OP_NAME = '__sp_op_name'
_SIMPLE_PLUGIN_DEPENDENCIES = '__sp_dependencies'
_SIMPLE_PLUGIN_REVERSE_DEPENDENCIES = '__sp_reverse_dependencies'
_SIMPLE_PLUGIN_STEP_NAME = '__sp_step_name'

T = TypeVar('T')


def operation(op_name: str) -> Callable[[T], T]:
    """
    Помечает аттрибут магического плагина как шаг, для заданной операции.

    Args:
        op_name:
            имя операции
    """

    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_OP_NAME, op_name)
        return f

    return decorator


def after(*dependencies) -> Callable[[T], T]:
    """
    Помечает аттрибут магического плагина как шаг, зависящий от других шагов.

    Args:
        *dependencies:
            имена шагов, от которых зависит этот шаг
    """

    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_DEPENDENCIES,
                (*dependencies, *getattr(f, _SIMPLE_PLUGIN_DEPENDENCIES, ())))
        return f

    return decorator


def before(*reverse_dependencies) -> Callable[[T], T]:
    """
    Помечает аттрибут магического плагина как шаг, имеющий обратную зависимость от других шагов.

    Обратная зависимость шага ``A`` от шага ``B`` эквивалентна прямой зависимости шага ``B`` от шага ``A``.

    Если зависимости между шагами определяют порядок выполнения шагов, то прямая зависимость ``A`` от ``B`` означает,
    что ``A`` зависит от результата выполнения ``B`` и будет выполнен после ``B``.
    Обратная зависимость ``A`` от ``B``, в свою очередь означает, что ``A`` должен быть выполнен до ``B``, например,
    чтобы произвести какие-либо дополнительные модификации данных, используемых шагом ``B``.

    Args:
        *reverse_dependencies:
            имена шагов, зависящих от этого шага
    """

    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_REVERSE_DEPENDENCIES,
                (*reverse_dependencies, *getattr(f, _SIMPLE_PLUGIN_REVERSE_DEPENDENCIES, ())))
        return f

    return decorator


def step_name(name: str) -> Callable[[T], T]:
    """
    Явно устанавливает имя шага, созданного из аттрибута магического плагина.

    Args:
        name:
            имя шага
    """

    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_STEP_NAME, name)
        return f

    return decorator


_SPECIAL_ATTRS_RE = re.compile(
    f'^(?:{"|".join((*Plugin.__dict__.keys(), *Plugin.__annotations__.keys()))})$|^_'
)


def extract_operations_from(
        obj: object,
        plugin: Plugin,
) -> dict[str, Collection[OperationStep]]:
    steps: dict[str, Collection[OperationStep]] = {}

    for attr in dir(obj):
        if _SPECIAL_ATTRS_RE.match(attr):
            continue

        value = getattr(obj, attr)

        op_name: str = getattr(value, _SIMPLE_PLUGIN_OP_NAME, attr)
        name: str = getattr(value, _SIMPLE_PLUGIN_STEP_NAME, None) or f'{plugin.name}.{attr}'
        dependencies: Collection[str] = getattr(value, _SIMPLE_PLUGIN_DEPENDENCIES, ())
        reverse_dependencies: Collection[str] = getattr(value, _SIMPLE_PLUGIN_REVERSE_DEPENDENCIES, ())

        steps[op_name] = (
            OperationStep(
                step=value,
                name=name,
                plugin=plugin,
                dependencies=dependencies,
                reverse_dependencies=reverse_dependencies,
            ),
            *steps.get(op_name, ())
        )

    return steps


class MagicPlugin(Plugin, ABC):
    """
    Базовый класс для плагинов, предоставляющий дополнительные функции, упрощающие разработку плагинов.

    Все публичные (имя которых не начинается с ``_``) методы и аттрибуты плагинов, наследующихся от этого класса
    рассматриваются как шаги операций.

    >>> class MyPlugin(MagicPlugin):
    >>>     def init(self, *args, **kwargs):
    >>>         # Метод становится шагом операции "init", без каких-либо зависимостей и с уникальным именем, зависящим
    >>>         # от имени плагина
    >>>         ...
    >>>     @operation('init')
    >>>     def init2(self, *args, **kwargs):
    >>>         # Метод становится ещё одним шагом операции "init"
    >>>         ...
    >>>     @operation('terminate')
    >>>     @after('kill_brain')
    >>>     def terminate(self, *_, **__):
    >>>         # Метод становится шагом операции "terminate", зависящим от (выполняющимся после) шага "kill_brain"
    >>>         ...
    """

    def __init__(self):
        super().__init__()
        self.__steps = extract_operations_from(self, self)

    def get_operation_steps(self, op_name: str) -> Iterable[OperationStep]:
        return self.__steps.get(op_name, ())


class MagicModulePlugin(Plugin):
    __slots__ = ('name', 'version', '_module', '_steps', '__doc__')

    def __init__(self, module: ModuleType):
        self.name = getattr(module, 'name', module.__name__)
        self.version = getattr(module, 'version', '0.0.0')
        self.__doc__ = getattr(module, '__doc__', None)
        self._steps = extract_operations_from(module, self)
        self._module = module

    def get_operation_steps(self, op_name: str) -> Iterable[OperationStep]:
        return self._steps.get(op_name, ())

    def __setattr__(self, key, value):
        if key in self.__slots__:
            return super().__setattr__(key, value)

        return setattr(self._module, key, value)

    def __getattr__(self, item):
        return getattr(self._module, item)
