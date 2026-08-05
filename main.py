import sys
from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.main_window import FloatingWindow


def _check_macos_accessibility():
    """접근성 권한 없으면 macOS 시스템 팝업 + 안내 메시지."""
    try:
        from src.actions._macos import check_accessibility
        if not check_accessibility():
            msg = QMessageBox()
            msg.setWindowTitle("접근성 권한 필요")
            msg.setText(
                "키보드·마우스 이벤트를 전송하려면 접근성 권한이 필요합니다.\n\n"
                "시스템 설정 → 개인 정보 보호 및 보안 → 손쉬운 사용에서\n"
                "터미널(또는 Python)을 허용한 뒤 앱을 다시 실행하세요."
            )
            msg.exec()
    except Exception:
        pass


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    if sys.platform == "darwin":
        _check_macos_accessibility()

    window = FloatingWindow()
    window.show()
    window.raise_()

    # 창 표시 후 Dock 아이콘 숨기기
    if sys.platform == "darwin":
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyAccessory
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except Exception:
            pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
