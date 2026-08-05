import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import FloatingWindow


def main():
    # macOS에서 Dock 아이콘 숨기기
    if sys.platform == "darwin":
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyAccessory
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = FloatingWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
