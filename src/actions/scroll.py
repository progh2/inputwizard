import sys
from typing import Optional, Tuple


def scroll(direction: int, ticks: int, qt_pos: Optional[Tuple[float, float]] = None) -> None:
    """direction: +1 위, -1 아래 / qt_pos: 스크롤을 발생시킬 Qt 화면 좌표"""
    if sys.platform == "darwin":
        from src.actions._macos import scroll as _scroll
        _scroll(direction, ticks, qt_pos)
    else:
        from pynput.mouse import Controller
        Controller().scroll(0, direction * ticks)
