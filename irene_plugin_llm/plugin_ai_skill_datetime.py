import datetime

from langchain_core.tools import tool

from irene.plugin_loader.magic_plugin import operation

name = 'ai_skill_datetime'
version = '0.1.0'


@operation('lc_tools')
@tool(parse_docstring=True)
def get_date_and_time() -> str:
    """
    Возвращает текущие дату и время.
    """
    return datetime.datetime.now().isoformat(sep=' ', timespec='minutes')
