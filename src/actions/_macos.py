"""macOS 전용 Quartz CGEvent 기반 이벤트 주입."""
from typing import Optional, Tuple


def check_accessibility() -> bool:
    """접근성 권한 확인. 없으면 macOS 시스템 팝업 자동 표시."""
    from Quartz import AXIsProcessTrustedWithOptions
    return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True}))


def copy():
    _send_key(8, _cmd())   # keycode 8 = 'c'


def paste():
    _send_key(9, _cmd())   # keycode 9 = 'v'


def toggle_ime():
    # Caps Lock (keycode 57) = 한국 macOS 한영 전환 키
    _send_key(57)


def scroll(direction: int, ticks: int, qt_pos: Optional[Tuple[float, float]] = None):
    from Quartz import (
        CGEventCreateScrollWheelEvent, CGEventSetLocation,
        CGEventPost, kCGHIDEventTap, kCGScrollEventUnitLine,
    )
    from AppKit import NSScreen

    event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 1, direction * ticks)

    if qt_pos is not None:
        # Qt 좌표(좌상단 원점) → macOS 좌표(좌하단 원점) 변환
        screen_h = NSScreen.mainScreen().frame().size.height
        CGEventSetLocation(event, (qt_pos[0], screen_h - qt_pos[1]))

    CGEventPost(kCGHIDEventTap, event)


# ── 내부 헬퍼 ────────────────────────────────────────────────

def _cmd() -> int:
    from Quartz import kCGEventFlagMaskCommand
    return kCGEventFlagMaskCommand


def _send_key(keycode: int, flags: int = 0):
    from Quartz import (
        CGEventCreateKeyboardEvent, CGEventSetFlags,
        CGEventPost, kCGHIDEventTap,
    )
    down = CGEventCreateKeyboardEvent(None, keycode, True)
    up   = CGEventCreateKeyboardEvent(None, keycode, False)
    if flags:
        CGEventSetFlags(down, flags)
        CGEventSetFlags(up, flags)
    CGEventPost(kCGHIDEventTap, down)
    CGEventPost(kCGHIDEventTap, up)
