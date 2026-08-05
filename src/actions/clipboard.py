import sys


def copy() -> None:
    if sys.platform == "darwin":
        from src.actions._macos import copy as _copy
        _copy()
    else:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        with kb.pressed(Key.ctrl):
            kb.press("c"); kb.release("c")


def paste() -> None:
    if sys.platform == "darwin":
        from src.actions._macos import paste as _paste
        _paste()
    else:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        with kb.pressed(Key.ctrl):
            kb.press("v"); kb.release("v")
