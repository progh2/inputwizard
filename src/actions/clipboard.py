import sys
from typing import Optional


def copy(pid: Optional[int] = None) -> None:
    if sys.platform == "darwin":
        from src.actions._macos import copy as _copy
        _copy(pid)
    else:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        with kb.pressed(Key.ctrl):
            kb.press("c"); kb.release("c")


def paste(pid: Optional[int] = None) -> None:
    if sys.platform == "darwin":
        from src.actions._macos import paste as _paste
        _paste(pid)
    else:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        with kb.pressed(Key.ctrl):
            kb.press("v"); kb.release("v")
