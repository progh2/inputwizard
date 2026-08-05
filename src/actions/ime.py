import sys


def toggle_ime() -> None:
    if sys.platform == "darwin":
        _toggle_macos()
    elif sys.platform == "win32":
        _toggle_windows()
    else:
        _toggle_linux()


def _toggle_macos() -> None:
    # Caps Lock 키 시뮬레이션 (한국 macOS에서 한영 전환 키)
    from pynput.keyboard import Controller, Key
    kb = Controller()
    kb.press(Key.caps_lock)
    kb.release(Key.caps_lock)


def _toggle_windows() -> None:
    import ctypes
    VK_HANGUL = 0x15
    KEYEVENTF_KEYUP = 0x0002
    ctypes.windll.user32.keybd_event(VK_HANGUL, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_HANGUL, 0, KEYEVENTF_KEYUP, 0)


def _toggle_linux() -> None:
    import os
    display = os.environ.get("WAYLAND_DISPLAY")
    if display:
        os.system("ydotool key 0x90")
    else:
        os.system("xdotool key hangul")
