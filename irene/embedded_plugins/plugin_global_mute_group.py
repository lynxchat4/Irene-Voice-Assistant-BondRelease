from typing import Optional, Callable

from irene.face.abc import MuteGroup
from irene.face.mute_group import MuteGroupImpl
from irene.plugin_loader.magic_plugin import step_name

name = 'global_mute_group'
version = '0.1.0'

_global_mute_group = MuteGroupImpl()


@step_name('default')
def get_mute_group(
        nxt: Callable,
        prev: Optional[MuteGroup],
        *args,
        **kwargs,
):
    if prev is None:
        prev = _global_mute_group

    return nxt(prev, *args, **kwargs)
