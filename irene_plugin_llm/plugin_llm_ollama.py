from typing import Any, Optional, Callable

from langchain_core.language_models import BaseChatModel

name = 'llm_ollama'
version = '0.1.0'

config = {
    'model': 'qwen2.5:14b',
}


def get_lc_llm(
        nxt: Callable,
        llm: Optional[BaseChatModel],
        llm_settings: dict[str, Any],
        *args, **kwargs
) -> Optional[BaseChatModel]:
    if llm is None and llm_settings['type'] == 'ollama':
        from langchain_ollama import ChatOllama

        settings = llm_settings.copy()
        settings.pop("type")

        llm = ChatOllama(**{**config, **settings})

    return nxt(llm, llm_settings, *args, **kwargs)
