import sys
from pynput.mouse import Controller as MouseController

_mouse = MouseController()


def scroll(direction: int, ticks: int) -> None:
    """direction: +1 위, -1 아래"""
    if sys.platform == "darwin":
        # macOS는 dy 반전
        _mouse.scroll(0, direction * ticks)
    else:
        _mouse.scroll(0, direction * ticks)
