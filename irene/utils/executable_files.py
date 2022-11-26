import os
from os.path import abspath
from typing import Optional


def is_executable(file: str) -> bool:
    return os.path.isfile(file) and os.access(file, os.X_OK)


def get_executable_path(cmd: str) -> Optional[str]:
    """
    Возвращает абсолютный путь к исполняемому файлу, соответствующему переданной команде.
    """
    if os.name == "nt" and not cmd.endswith(".exe"):
        cmd += ".exe"

    if is_executable(cmd):
        return abspath(cmd)

    envdir_list = [os.curdir] + os.environ["PATH"].split(os.pathsep)

    for envdir in envdir_list:
        if is_executable(program_path := os.path.join(envdir, cmd)):
            return abspath(program_path)

    return None
