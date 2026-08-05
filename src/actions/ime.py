import sys
from typing import Optional


def toggle_ime(pid: Optional[int] = None) -> None:
    if sys.platform == "darwin":
        from src.actions._macos import toggle_ime as _toggle
        _toggle(pid)
    elif sys.platform == "win32":
        _toggle_windows()
    else:
        _toggle_linux()


def _toggle_windows() -> None:
    import ctypes
    VK_HANGUL, KEYEVENTF_KEYUP = 0x15, 0x0002
    ctypes.windll.user32.keybd_event(VK_HANGUL, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_HANGUL, 0, KEYEVENTF_KEYUP, 0)


def _toggle_linux() -> None:
    import os
    if os.environ.get("WAYLAND_DISPLAY"):
        os.system("ydotool key 0x90")
    else:
        os.system("xdotool key hangul")
