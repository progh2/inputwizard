import sys
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QPushButton, QMenu, QSizePolicy
)
from PySide6.QtGui import QAction

from src.ui.styles import SCROLL_BTN, ACTION_BTN
from src.actions import scroll as scroll_action
from src.actions import clipboard as clipboard_action
from src.actions import ime as ime_action
import src.config as config_store


# 연속 스크롤 설정
_HOLD_DELAY_MS = 500
_HOLD_INTERVAL_MS = 100


class FloatingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._cfg = config_store.load()
        self._drag_pos: QPoint | None = None

        self._setup_window()
        self._build_ui()
        self._apply_always_on_top(self._cfg.get("always_on_top", True))
        self._restore_position()
        self._make_non_activating()

    # ── 창 설정 ──────────────────────────────────────────────

    def _setup_window(self):
        flags = (
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle("InputWizard")

    def _make_non_activating(self):
        """macOS: 창이 포커스를 가져가지 않도록 NSWindow 레벨 설정."""
        if sys.platform != "darwin":
            return
        try:
            from AppKit import NSApp
            # NSFloatingWindowLevel = 5, NSNormalWindowLevel = 0
            # WA_ShowWithoutActivating + Tool 플래그로 대부분 처리되지만
            # NSApp.windows() 중 마지막에 추가된 창에 setLevel_ 보강
            ns_windows = NSApp.windows()
            if ns_windows:
                ns_windows[-1].setLevel_(5)  # NSFloatingWindowLevel
        except Exception:
            pass

    # ── UI 빌드 ──────────────────────────────────────────────

    def _build_ui(self):
        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background-color: transparent;
            }
        """)
        self.setCentralWidget(container)

        layout = QGridLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # 좌측 버튼 3개
        self._btn_ime = self._make_btn("韓", ACTION_BTN, "한/영 전환")
        self._btn_copy = self._make_btn("📋", ACTION_BTN, "복사 (Cmd/Ctrl+C)")
        self._btn_paste = self._make_btn("📌", ACTION_BTN, "붙여넣기 (Cmd/Ctrl+V)")

        # 우측 스크롤 버튼 2개
        self._btn_up = self._make_btn("↑", SCROLL_BTN, "위로 스크롤")
        self._btn_down = self._make_btn("↓", SCROLL_BTN, "아래로 스크롤")

        btn_w, btn_h = 44, 44
        scroll_w = 36

        for btn in (self._btn_ime, self._btn_copy, self._btn_paste):
            btn.setFixedSize(btn_w, btn_h)

        self._btn_up.setFixedSize(scroll_w, btn_h)
        self._btn_down.setFixedSize(scroll_w, btn_h)

        layout.addWidget(self._btn_ime,   0, 0)
        layout.addWidget(self._btn_copy,  1, 0)
        layout.addWidget(self._btn_paste, 2, 0)
        layout.addWidget(self._btn_up,    0, 1, 1, 1)
        layout.addWidget(self._btn_down,  2, 1, 1, 1)

        # 스크롤 버튼 가운데 공간 채우기
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer, 1, 1)

        self.adjustSize()

        # 클릭 연결
        self._btn_ime.clicked.connect(self._on_ime)
        self._btn_copy.clicked.connect(self._on_copy)
        self._btn_paste.clicked.connect(self._on_paste)

        # 스크롤: 클릭 + 꾹 누르기
        self._setup_scroll_button(self._btn_up, direction=1)
        self._setup_scroll_button(self._btn_down, direction=-1)

        # 우클릭 메뉴
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    @staticmethod
    def _make_btn(text: str, style: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.setToolTip(tooltip)
        btn.setFocusPolicy(Qt.NoFocus)
        return btn

    # ── 스크롤 버튼 꾹 누르기 ────────────────────────────────

    def _setup_scroll_button(self, btn: QPushButton, direction: int):
        timer = QTimer(self)
        timer.setInterval(_HOLD_INTERVAL_MS)

        def do_scroll():
            scroll_action.scroll(direction, self._cfg.get("scroll_ticks", 3))

        timer.timeout.connect(do_scroll)

        def _pressed():
            do_scroll()
            QTimer.singleShot(_HOLD_DELAY_MS, lambda: timer.start() if btn.isDown() else None)

        btn.pressed.connect(_pressed)
        btn.released.connect(timer.stop)

    # ── 액션 ─────────────────────────────────────────────────

    def _on_ime(self):
        ime_action.toggle_ime()

    def _on_copy(self):
        clipboard_action.copy()

    def _on_paste(self):
        clipboard_action.paste()

    # ── 컨텍스트 메뉴 ────────────────────────────────────────

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        # 항상 위 토글
        aot = self._cfg.get("always_on_top", True)
        act_aot = QAction(f"{'✓ ' if aot else ''}항상 위", self)
        act_aot.triggered.connect(self._toggle_always_on_top)
        menu.addAction(act_aot)

        # 스크롤 강도
        scroll_menu = menu.addMenu("스크롤 강도")
        for ticks in (1, 3, 5, 10):
            cur = self._cfg.get("scroll_ticks", 3)
            act = QAction(f"{'✓ ' if cur == ticks else ''}{ticks}틱", self)
            act.triggered.connect(lambda _, t=ticks: self._set_scroll_ticks(t))
            scroll_menu.addAction(act)

        menu.addSeparator()
        act_quit = QAction("종료", self)
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_quit)

        menu.exec(self.mapToGlobal(pos))

    def _toggle_always_on_top(self):
        aot = not self._cfg.get("always_on_top", True)
        self._cfg["always_on_top"] = aot
        self._apply_always_on_top(aot)
        config_store.save(self._cfg)

    def _apply_always_on_top(self, on: bool):
        flags = self.windowFlags()
        if on:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _set_scroll_ticks(self, ticks: int):
        self._cfg["scroll_ticks"] = ticks
        config_store.save(self._cfg)

    def _quit(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    # ── 위치 저장/복원 ────────────────────────────────────────

    def _restore_position(self):
        self.move(self._cfg.get("x", 100), self._cfg.get("y", 100))

    def _save_position(self):
        pos = self.pos()
        self._cfg["x"] = pos.x()
        self._cfg["y"] = pos.y()
        config_store.save(self._cfg)

    def closeEvent(self, event):
        self._save_position()
        super().closeEvent(event)

    # ── 드래그 이동 ───────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            screen = self.screen().availableGeometry()
            # 창이 화면 밖으로 완전히 벗어나지 않도록 제한
            x = max(screen.left() - self.width() + 20, min(new_pos.x(), screen.right() - 20))
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - 20))
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            self._save_position()
