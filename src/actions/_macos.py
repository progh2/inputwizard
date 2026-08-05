"""macOS 전용 Quartz CGEvent 기반 이벤트 주입."""
import os
import subprocess
from typing import Optional, Tuple


# ── 접근성 권한 ──────────────────────────────────────────────

def is_trusted() -> bool:
    from ApplicationServices import AXIsProcessTrusted
    return bool(AXIsProcessTrusted())


def request_accessibility() -> bool:
    from ApplicationServices import AXIsProcessTrustedWithOptions
    return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True}))


def open_accessibility_settings():
    os.system(
        "open 'x-apple.systempreferences:"
        "com.apple.preference.security?Privacy_Accessibility'"
    )


# ── 이전 앱 활성화 + 딜레이 후 이벤트 전송 ──────────────────

def activate_pid_then(pid: Optional[int], delay_ms: int, callback) -> None:
    """pid 앱을 foreground로 올린 뒤 delay_ms 후 callback 실행."""
    if not pid or pid == os.getpid():
        callback()
        return
    try:
        from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if app and not app.isTerminated():
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    except Exception:
        pass
    # PySide6 QTimer는 여기서 직접 사용 불가 → 호출자 측에서 singleShot 사용
    # delay_ms 정보를 반환해서 호출자가 처리
    return delay_ms


# ── 키보드 이벤트 ────────────────────────────────────────────

def copy(pid: Optional[int] = None):
    _send_key(8, _cmd(), pid)


def paste(pid: Optional[int] = None):
    _send_key(9, _cmd(), pid)


def toggle_ime(pid: Optional[int] = None):
    _send_key(57, 0, pid)   # keycode 57 = Caps Lock = 한영 전환


# ── 스크롤 이벤트 ────────────────────────────────────────────

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


# ── 입력 언어 감지 ───────────────────────────────────────────

def current_input_lang() -> str:
    """'ko' 또는 'en' 반환 (0.1초 이내)."""
    try:
        r = subprocess.run(
            ['defaults', 'read', 'com.apple.HIToolbox',
             'AppleCurrentKeyboardLayoutInputSourceID'],
            capture_output=True, text=True, timeout=0.3,
        )
        return 'ko' if 'Korean' in r.stdout else 'en'
    except Exception:
        return 'en'


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

    if pid and pid != os.getpid():
        CGEventPostToPid(pid, down)
        CGEventPostToPid(pid, up)
    else:
        CGEventPost(kCGHIDEventTap, down)
        CGEventPost(kCGHIDEventTap, up)
