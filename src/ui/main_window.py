import sys
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QPushButton, QMenu, QSizePolicy,
)
from PySide6.QtGui import QAction, QCursor

from src.ui.styles import CONTAINER, SCROLL_BTN, ACTION_BTN
from src.actions import scroll as scroll_action
from src.actions import clipboard as clipboard_action
from src.actions import ime as ime_action
import src.config as config_store

_HOLD_DELAY_MS   = 500
_HOLD_INTERVAL_MS = 80


class FloatingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._cfg = config_store.load()
        self._drag_pos: QPoint | None = None
        self._last_outside_pos: QPoint | None = None

        self._setup_window()
        self._build_ui()
        self._apply_always_on_top(self._cfg.get("always_on_top", True))
        self._restore_position()
        self._start_pos_tracker()

    # ── 창 설정 ──────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("InputWizard")

    # ── UI 빌드 ──────────────────────────────────────────────

    def _build_ui(self):
        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet(CONTAINER)
        self.setCentralWidget(container)

        layout = QGridLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        self._btn_ime   = self._make_btn("가\nA",  ACTION_BTN, "한/영 전환")
        self._btn_copy  = self._make_btn("⌘\nC",  ACTION_BTN, "복사 (Cmd/Ctrl+C)")
        self._btn_paste = self._make_btn("⌘\nV",  ACTION_BTN, "붙여넣기 (Cmd/Ctrl+V)")
        self._btn_up    = self._make_btn("▲",      SCROLL_BTN, "위로 스크롤")
        self._btn_down  = self._make_btn("▼",      SCROLL_BTN, "아래로 스크롤")

        for btn in (self._btn_ime, self._btn_copy, self._btn_paste):
            btn.setFixedSize(46, 46)
        self._btn_up.setFixedSize(38, 46)
        self._btn_down.setFixedSize(38, 46)

        layout.addWidget(self._btn_ime,   0, 0)
        layout.addWidget(self._btn_copy,  1, 0)
        layout.addWidget(self._btn_paste, 2, 0)
        layout.addWidget(self._btn_up,    0, 1)

        # 스크롤 버튼 사이 빈 공간
        spacer = QWidget()
        spacer.setFixedSize(38, 46)
        spacer.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(spacer, 1, 1)

        layout.addWidget(self._btn_down,  2, 1)

        self.adjustSize()

        self._btn_ime.clicked.connect(ime_action.toggle_ime)
        self._btn_copy.clicked.connect(clipboard_action.copy)
        self._btn_paste.clicked.connect(clipboard_action.paste)

        self._setup_scroll_btn(self._btn_up,   +1)
        self._setup_scroll_btn(self._btn_down, -1)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    @staticmethod
    def _make_btn(text: str, style: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.setToolTip(tooltip)
        btn.setFocusPolicy(Qt.NoFocus)
        return btn

    # ── 스크롤 버튼 ──────────────────────────────────────────

    def _setup_scroll_btn(self, btn: QPushButton, direction: int):
        timer = QTimer(self)
        timer.setInterval(_HOLD_INTERVAL_MS)

        def do_scroll():
            ticks = self._cfg.get("scroll_ticks", 3)
            pos = self._last_outside_pos
            qt_pos = (pos.x(), pos.y()) if pos else None
            scroll_action.scroll(direction, ticks, qt_pos)

        timer.timeout.connect(do_scroll)

        def on_press():
            do_scroll()
            QTimer.singleShot(_HOLD_DELAY_MS, lambda: timer.start() if btn.isDown() else None)

        btn.pressed.connect(on_press)
        btn.released.connect(timer.stop)

    # ── 마우스 위치 추적 (창 밖 마지막 위치 저장) ───────────

    def _start_pos_tracker(self):
        self._pos_timer = QTimer(self)
        self._pos_timer.setInterval(50)
        self._pos_timer.timeout.connect(self._update_outside_pos)
        self._pos_timer.start()

    def _update_outside_pos(self):
        pos = QCursor.pos()
        if not self.geometry().contains(pos):
            self._last_outside_pos = pos

    # ── 컨텍스트 메뉴 ────────────────────────────────────────

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        aot = self._cfg.get("always_on_top", True)
        act_aot = QAction(f"{'✓ ' if aot else ''}항상 위", self)
        act_aot.triggered.connect(self._toggle_always_on_top)
        menu.addAction(act_aot)

        scroll_menu = menu.addMenu("스크롤 강도")
        cur = self._cfg.get("scroll_ticks", 3)
        for ticks in (1, 3, 5, 10):
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

    @staticmethod
    def _quit():
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
            x = max(screen.left() - self.width() + 20, min(new_pos.x(), screen.right() - 20))
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - 20))
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            self._save_position()
