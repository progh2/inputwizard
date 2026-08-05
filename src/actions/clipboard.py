import sys
from pynput.keyboard import Controller as KeyboardController, Key

_kb = KeyboardController()

_MOD = Key.cmd if sys.platform == "darwin" else Key.ctrl


def copy() -> None:
    with _kb.pressed(_MOD):
        _kb.press("c")
        _kb.release("c")


def paste() -> None:
    with _kb.pressed(_MOD):
        _kb.press("v")
        _kb.release("v")
