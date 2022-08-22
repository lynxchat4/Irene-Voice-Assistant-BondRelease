from graphlib import TopologicalSorter, CycleError
from logging import getLogger
from typing import Iterable, Collection

from irene.plugin_loader.plugins_abc import PluginManager, OperationStep, Plugin, DependencyCycleException


class PluginManagerImpl(PluginManager):
    __slots__ = ('_plugins', '_logger')

    def __init__(self, plugins: Collection[Plugin], *, logger=getLogger('PluginManager')):
        self._plugins = plugins
        self._logger = logger

    def get_operation_sequence(self, op_name: str) -> Iterable[OperationStep]:
        ts: TopologicalSorter[str] = TopologicalSorter()
        steps: dict[str, OperationStep] = {}

        for plugin in self._plugins:
            for step in plugin.get_operation_steps(op_name):
                if step.name in steps:
                    self._logger.warning(
                        'Шаг с именем "%s" для операции "%s" добавлен одновременно плагинами %s и %s. '
                        'Шаг, добавленные плагином %s будет проигнорирован.',
                        step.name, op_name, steps[step.name].plugin, plugin, plugin
                    )
                    continue

                steps[step.name] = step

                ts.add(step.name, *step.dependencies)

                for reverse_dep in step.reverse_dependencies:
                    ts.add(reverse_dep, step.name)

        try:
            ts.prepare()
        except CycleError as e:
            raise DependencyCycleException(
                op_name,
                [steps.get(name, name) for name in e.args[1][1:]]
            )

        # Генератор вынесен в отдельную функцию чтобы исключение DependencyCycleException выкидывалось непосредственно
        # при вызове get_operation_sequence
        def iterate():
            while ts.is_active():
                node_group = ts.get_ready()

                for name in node_group:
                    if name in steps:
                        yield steps[name]

                ts.done(*node_group)

        return iterate()
