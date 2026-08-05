"""macOS 전용 Quartz CGEvent 기반 이벤트 주입."""
import os
from typing import Optional, Tuple


def is_trusted() -> bool:
    """접근성 권한 현재 상태 (팝업 없이 조용히 확인)."""
    from Quartz import AXIsProcessTrusted
    return bool(AXIsProcessTrusted())


def request_accessibility() -> bool:
    """권한 요청 팝업 띄우기 + 현재 상태 반환."""
    from Quartz import AXIsProcessTrustedWithOptions
    return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True}))


def open_accessibility_settings():
    """손쉬운 사용 설정 창 바로 열기."""
    os.system(
        "open 'x-apple.systempreferences:"
        "com.apple.preference.security?Privacy_Accessibility'"
    )


def copy(pid: Optional[int] = None):
    _send_key(8, _cmd(), pid)   # keycode 8 = 'c'


def paste(pid: Optional[int] = None):
    _send_key(9, _cmd(), pid)   # keycode 9 = 'v'


def toggle_ime(pid: Optional[int] = None):
    # Caps Lock keycode 57 = 한국 macOS 한영 전환
    _send_key(57, 0, pid)


def scroll(direction: int, ticks: int, qt_pos: Optional[Tuple[float, float]] = None):
    from Quartz import (
        CGEventCreateScrollWheelEvent, CGEventSetLocation,
        CGEventPost, kCGHIDEventTap, kCGScrollEventUnitLine,
    )
    from AppKit import NSScreen

    event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 1, direction * ticks)

    if qt_pos is not None:
        screen_h = NSScreen.mainScreen().frame().size.height
        CGEventSetLocation(event, (qt_pos[0], screen_h - qt_pos[1]))

    CGEventPost(kCGHIDEventTap, event)


# ── 내부 헬퍼 ────────────────────────────────────────────────

def _cmd() -> int:
    from Quartz import kCGEventFlagMaskCommand
    return kCGEventFlagMaskCommand


def _send_key(keycode: int, flags: int, pid: Optional[int]):
    from Quartz import (
        CGEventCreateKeyboardEvent, CGEventSetFlags,
        CGEventPost, CGEventPostToPid, kCGHIDEventTap,
    )
    down = CGEventCreateKeyboardEvent(None, keycode, True)
    up   = CGEventCreateKeyboardEvent(None, keycode, False)
    if flags:
        CGEventSetFlags(down, flags)
        CGEventSetFlags(up, flags)

    my_pid = os.getpid()
    if pid and pid != my_pid:
        CGEventPostToPid(pid, down)
        CGEventPostToPid(pid, up)
    else:
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)
