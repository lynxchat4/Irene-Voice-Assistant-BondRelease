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
    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_OP_NAME, op_name)
        return f

    return decorator


def after(*dependencies) -> Callable[[T], T]:
    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_DEPENDENCIES,
                (*dependencies, *getattr(f, _SIMPLE_PLUGIN_DEPENDENCIES, ())))
        return f

    return decorator


def before(*reverse_dependencies) -> Callable[[T], T]:
    def decorator(f):
        setattr(f, _SIMPLE_PLUGIN_REVERSE_DEPENDENCIES,
                (*reverse_dependencies, *getattr(f, _SIMPLE_PLUGIN_REVERSE_DEPENDENCIES, ())))
        return f

    return decorator


def step_name(name: str) -> Callable[[T], T]:
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
    def __init__(self):
        super().__init__()
        self.__steps = extract_operations_from(self, self)

    def get_operation_steps(self, op_name: str) -> Iterable[OperationStep]:
        return self.__steps.get(op_name, ())


class MagicModulePlugin(Plugin):
    __slots__ = ('name', 'version', '_module', '_steps')

    def __init__(self, module: ModuleType):
        self.name = getattr(module, 'name', module.__name__)
        self.version = getattr(module, 'version', '0.0.0')
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
