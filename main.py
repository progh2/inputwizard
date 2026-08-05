import sys
from PySide6.QtWidgets import QApplication

from src.ui.main_window import FloatingWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = FloatingWindow()
    window.show()
    window.raise_()

    # 창 표시 후 Dock 아이콘 숨기기 + Accessory 모드 설정
    if sys.platform == "darwin":
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyAccessory
            ok = NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
            policy = NSApp.activationPolicy()
            # 0=Regular, 1=Accessory, 2=Prohibited
            print(f"[IW] activation policy 설정 → {ok}, 현재={policy} (1=Accessory=포커스 안 빼앗음)")
        except Exception as e:
            print(f"[IW] activation policy 설정 실패: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
