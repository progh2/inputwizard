"""진단 스크립트 — 권한·PID·이벤트 주입 테스트"""
import sys, os, time

print(f"Python 실행 경로: {sys.executable}")
print()

# 1. 접근성 권한
from ApplicationServices import AXIsProcessTrusted, AXIsProcessTrustedWithOptions
trusted = AXIsProcessTrusted()
print(f"[1] 접근성 권한(조용히): {trusted}")
if not trusted:
    print("    → 권한 없음. 시스템 팝업 요청...")
    AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True})
    print("    → 허용 후 다시 실행하세요.")
    sys.exit(1)

# 2. 현재 활성 앱
from AppKit import NSWorkspace
app = NSWorkspace.sharedWorkspace().frontmostApplication()
print(f"[2] 현재 활성 앱: {app.localizedName()} (PID={app.processIdentifier()})")
print(f"    내 PID: {os.getpid()}")

# 3. 현재 입력 소스
import subprocess
r = subprocess.run(
    ['defaults', 'read', 'com.apple.HIToolbox', 'AppleCurrentKeyboardLayoutInputSourceID'],
    capture_output=True, text=True
)
print(f"[3] 현재 입력 소스: {r.stdout.strip()}")

# 4. 5초 후 스티커 앱(또는 아무 텍스트 앱)에 Cmd+C 전송 테스트
print()
print("[4] 5초 후 CGEventPost로 Cmd+C 전송합니다.")
print("    → 지금 텍스트를 선택해두세요. 성공하면 클립보드에 복사됩니다.")

for i in range(5, 0, -1):
    print(f"    {i}...", end="\r")
    time.sleep(1)

from Quartz import (
    CGEventCreateKeyboardEvent, CGEventSetFlags,
    CGEventPost, CGEventPostToPid, kCGHIDEventTap, kCGEventFlagMaskCommand,
)

# 방법 A: kCGHIDEventTap (현재 key window로)
print("\n    방법A: CGEventPost(kCGHIDEventTap)  ", end="")
down = CGEventCreateKeyboardEvent(None, 8, True)
CGEventSetFlags(down, kCGEventFlagMaskCommand)
CGEventPost(kCGHIDEventTap, down)
up = CGEventCreateKeyboardEvent(None, 8, False)
CGEventSetFlags(up, kCGEventFlagMaskCommand)
CGEventPost(kCGHIDEventTap, up)
print("전송 완료")

time.sleep(0.5)

# 방법 B: CGEventPostToPid
pid = app.processIdentifier()
print(f"    방법B: CGEventPostToPid({pid})  ", end="")
down = CGEventCreateKeyboardEvent(None, 8, True)
CGEventSetFlags(down, kCGEventFlagMaskCommand)
CGEventPostToPid(pid, down)
up = CGEventCreateKeyboardEvent(None, 8, False)
CGEventSetFlags(up, kCGEventFlagMaskCommand)
CGEventPostToPid(pid, up)
print("전송 완료")

print()
print("→ 클립보드 내용 확인: 방법A 또는 방법B 중 뭐가 동작했나요?")
print("  Cmd+V로 붙여넣기 해서 복사된 텍스트가 있으면 성공입니다.")
