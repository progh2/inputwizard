import sys
from PySide6.QtWidgets import QApplication

from src.ui.main_window import FloatingWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = FloatingWindow()
    window.show()
    window.raise_()

    # 창 표시 후 Dock 아이콘 숨기기 (순서 중요)
    if sys.platform == "darwin":
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyAccessory
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except Exception:
            pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
