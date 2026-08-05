import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import FloatingWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = FloatingWindow()
    window.show()
    window.raise_()

    # macOS에서 Dock 아이콘 숨기기 — 창 표시 후에 적용해야 창이 사라지지 않음
    if sys.platform == "darwin":
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyAccessory
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except Exception:
            pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
