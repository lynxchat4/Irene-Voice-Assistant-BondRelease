from logging import getLogger
from typing import Callable, TypedDict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from openai import BaseModel

from irene import VAContext, VAApiExt, construct_context
from irene.plugin_loader.abc import PluginManager, OperationStep
from irene.plugin_loader.magic_plugin import MagicPlugin, operation, before, step_name
from irene.plugin_loader.run_operation import call_all_as_wrappers

_DEFAULT_SYSTEM_PROMPT = """
Ты - умный голосовой помощник Ирина.

Используй инструменты чтобы выполнить запрос пользователя.

Отвечай коротко и чётко, используя только русский язык.
"""


class Config(TypedDict):
    enabled: bool
    llm_settings: dict[str, Any]
    system_prompt: str
    debug: bool


class LLMFallbackContextPlugin(MagicPlugin):
    name = 'llm_fallback_context'
    version = '0.1.0'

    _logger = getLogger(name)

    config: Config = {
        "enabled": True,
        "llm_settings": {
            "type": "ollama",
        },
        "system_prompt": _DEFAULT_SYSTEM_PROMPT,
        "debug": True,
    }

    def __init__(self):
        super().__init__()
        self._cp = InMemorySaver()

    def init(self, pm: PluginManager, *_args, **_kwargs):
        self._tools = self._load_tools(pm)

        # На некоторых версиях pydantic вызов model_json_schema() падает и роняет агента позже,
        # так что вызываем его заранее тут.
        for tool in self._tools:
            if isinstance(tool.tool_call_schema, type) and issubclass(tool.tool_call_schema, BaseModel):
                tool.tool_call_schema.model_json_schema()

    def _tools_from_step(self, step: OperationStep) -> list[BaseTool]:
        if isinstance(step.step, BaseTool):
            return [step.step]

        self._logger.error("Step %s is not a langchain tool", str(step))

        return []

    def _load_tools(self, pm: PluginManager) -> list[BaseTool]:
        return [tool for step in pm.get_operation_sequence('lc_tools') for tool in self._tools_from_step(step)]

    def _get_llm(self, pm: PluginManager) -> BaseChatModel:
        llm = call_all_as_wrappers(
            pm.get_operation_sequence("get_lc_llm"),
            None,
            self.config["llm_settings"],
        )

        if not isinstance(llm, BaseChatModel):
            raise Exception(f"Не удалось получить LLM")

        return llm

    def _create_graph(self, pm: PluginManager) -> CompiledStateGraph[MessagesState]:
        return create_react_agent(
            model=self._get_llm(pm),
            tools=self._load_tools(pm),
            prompt=self.config['system_prompt'],
            checkpointer=self._cp,
            debug=self.config['debug'],
        )

    @staticmethod
    def _get_agent_config(va: VAApiExt, pm: PluginManager) -> RunnableConfig:
        return {
            'configurable': {
                'thread_id': 'default',
                'irene_va_api': va,
                'irene_pm': pm,
            }
        }

    def _make_chat_context(self, pm: PluginManager) -> VAContext:
        def chat(va: VAApiExt, initial_msg: str):
            graph = self._create_graph(pm)  # TODO: Cache

            def _response_from_state(s: dict[str, Any]) -> str:
                message = s['messages'][-1]
                assert isinstance(message, AIMessage)
                assert isinstance(message.content, str)
                return message.content

            user_msg = initial_msg

            while True:
                state = graph.invoke(
                    {
                        "messages": [HumanMessage(user_msg)],
                    },
                    self._get_agent_config(va, pm),
                )

                user_msg = yield _response_from_state(state)

        return construct_context(chat)

    @operation('create_root_context')
    @before('load_commands')
    @step_name('inject_llm_fallback_context')
    def create_root_context(
            self,
            nxt: Callable,
            ctx: VAContext,
            pm: PluginManager,
            *args, **kwargs
    ):
        if self.config['enabled']:
            ctx = self._make_chat_context(pm)
        return nxt(ctx, pm, *args, **kwargs)
