import sys
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy,
)
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QMenu

from src.ui.styles import CONTAINER, SCROLL_BTN, ACTION_BTN, IME_KO_BTN, IME_EN_BTN, WARNING_STYLE
from src.actions import scroll as scroll_action
from src.actions import clipboard as clipboard_action
from src.actions import ime as ime_action
import src.config as config_store

_HOLD_DELAY_MS    = 500
_HOLD_INTERVAL_MS = 80
_PERM_CHECK_MS    = 4_000
_LANG_CHECK_MS    = 600       # 입력 언어 감지 주기
_ACTIVATE_DELAY   = 80        # 이전 앱 활성화 → 이벤트 전송 딜레이(ms)


class FloatingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._cfg                = config_store.load()
        self._drag_pos: QPoint | None = None
        self._last_outside_pos: QPoint | None = None
        self._target_pid: int | None = None
        self._prev_in_window     = False
        self._input_lang         = "en"

        self._setup_window()
        self._build_ui()
        self._apply_always_on_top(self._cfg.get("always_on_top", True))
        self._restore_position()
        self._start_trackers()

    # ── 창 설정 ──────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("InputWizard")
        self.setContextMenuPolicy(Qt.NoContextMenu)

    # ── UI 빌드 ──────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget(self)
        root.setObjectName("container")
        root.setStyleSheet(CONTAINER)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(4)

        # 권한 경고 배너
        self._warn_bar = QLabel("⚠ 접근성 권한 필요  [클릭하여 설정]")
        self._warn_bar.setStyleSheet(WARNING_STYLE)
        self._warn_bar.setAlignment(Qt.AlignCenter)
        self._warn_bar.setCursor(Qt.PointingHandCursor)
        self._warn_bar.mousePressEvent = lambda _: self._open_accessibility()
        self._warn_bar.setVisible(False)
        outer.addWidget(self._warn_bar)

        grid_w = QWidget()
        layout = QGridLayout(grid_w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        outer.addWidget(grid_w)

        # 한/영 버튼은 나중에 언어에 따라 스타일 교체하므로 별도 보관
        self._btn_ime   = self._make_btn("가\nA",  ACTION_BTN, "한/영 전환")
        self._btn_copy  = self._make_btn("⌘\nC",  ACTION_BTN, "복사 (Cmd/Ctrl+C)")
        self._btn_paste = self._make_btn("⌘\nV",  ACTION_BTN, "붙여넣기 (Cmd/Ctrl+V)")
        self._btn_up    = self._make_btn("▲",      SCROLL_BTN, "위로 스크롤")
        self._btn_down  = self._make_btn("▼",      SCROLL_BTN, "아래로 스크롤")

        self._action_btns = [
            self._btn_ime, self._btn_copy, self._btn_paste,
            self._btn_up, self._btn_down,
        ]

        for btn in (self._btn_ime, self._btn_copy, self._btn_paste):
            btn.setFixedSize(46, 46)
        self._btn_up.setFixedSize(38, 46)
        self._btn_down.setFixedSize(38, 46)

        layout.addWidget(self._btn_ime,   0, 0)
        layout.addWidget(self._btn_copy,  1, 0)
        layout.addWidget(self._btn_paste, 2, 0)
        layout.addWidget(self._btn_up,    0, 1)

        spacer = QWidget(); spacer.setFixedSize(38, 46)
        layout.addWidget(spacer, 1, 1)

        layout.addWidget(self._btn_down, 2, 1)
        self.adjustSize()

        self._btn_ime.clicked.connect(self._on_ime)
        self._btn_copy.clicked.connect(self._on_copy)
        self._btn_paste.clicked.connect(self._on_paste)
        self._setup_scroll_btn(self._btn_up,   +1)
        self._setup_scroll_btn(self._btn_down, -1)

    @staticmethod
    def _make_btn(text, style, tooltip):
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.setToolTip(tooltip)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setContextMenuPolicy(Qt.PreventContextMenu)
        return btn

    # ── 액션: 이전 앱 활성화 → 딜레이 → 이벤트 전송 ─────────

    def _run_with_focus_restore(self, action_fn):
        """이전 앱 포커스를 되돌린 뒤 action_fn 실행."""
        pid = self._target_pid
        if sys.platform == "darwin" and pid:
            try:
                from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
                app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                if app and not app.isTerminated():
                    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            except Exception:
                pass
            QTimer.singleShot(_ACTIVATE_DELAY, action_fn)
        else:
            action_fn()

    def _on_ime(self):
        pid = self._target_pid
        self._run_with_focus_restore(lambda: ime_action.toggle_ime(pid))

    def _on_copy(self):
        pid = self._target_pid
        self._run_with_focus_restore(lambda: clipboard_action.copy(pid))

    def _on_paste(self):
        pid = self._target_pid
        self._run_with_focus_restore(lambda: clipboard_action.paste(pid))

    # ── 스크롤 버튼 ──────────────────────────────────────────

    def _setup_scroll_btn(self, btn, direction):
        timer = QTimer(self)
        timer.setInterval(_HOLD_INTERVAL_MS)

        def do_scroll():
            ticks  = self._cfg.get("scroll_ticks", 3)
            pos    = self._last_outside_pos
            qt_pos = (pos.x(), pos.y()) if pos else None
            scroll_action.scroll(direction, ticks, qt_pos)

        timer.timeout.connect(do_scroll)

        def on_press():
            do_scroll()
            QTimer.singleShot(_HOLD_DELAY_MS, lambda: timer.start() if btn.isDown() else None)

        btn.pressed.connect(on_press)
        btn.released.connect(timer.stop)

    # ── 타이머 기반 추적 ──────────────────────────────────────

    def _start_trackers(self):
        # 마우스 위치 + 창 진입 시 PID 캡처
        t1 = QTimer(self)
        t1.setInterval(50)
        t1.timeout.connect(self._tick_mouse)
        t1.start()

        # 접근성 권한 체크 (macOS)
        if sys.platform == "darwin":
            t2 = QTimer(self)
            t2.setInterval(_PERM_CHECK_MS)
            t2.timeout.connect(self._check_perm)
            t2.start()
            QTimer.singleShot(0, self._check_perm)

            # 입력 언어 감지
            t3 = QTimer(self)
            t3.setInterval(_LANG_CHECK_MS)
            t3.timeout.connect(self._update_lang)
            t3.start()
            QTimer.singleShot(0, self._update_lang)

    def _tick_mouse(self):
        pos       = QCursor.pos()
        in_window = self.geometry().contains(pos)

        if not in_window:
            self._last_outside_pos = pos
            if self._prev_in_window:
                self._prev_in_window = False
        else:
            if not self._prev_in_window:
                # 창 밖 → 창 안: 이 시점엔 아직 이전 앱이 frontmost
                self._prev_in_window = True
                self._capture_pid()

    def _capture_pid(self):
        if sys.platform != "darwin":
            return
        try:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app:
                pid = app.processIdentifier()
                if pid != __import__("os").getpid():
                    self._target_pid = pid
        except Exception:
            pass

    # ── 입력 언어 감지 + 버튼 업데이트 ──────────────────────

    def _update_lang(self):
        if sys.platform != "darwin":
            return
        from src.actions._macos import current_input_lang
        lang = current_input_lang()
        if lang != self._input_lang:
            self._input_lang = lang
            self._refresh_ime_btn(lang)

    def _refresh_ime_btn(self, lang: str):
        if lang == "ko":
            self._btn_ime.setText("가\n↔")
            self._btn_ime.setStyleSheet(IME_KO_BTN)
            self._btn_ime.setToolTip("한/영 전환  [현재: 한글]")
        else:
            self._btn_ime.setText("A\n↔")
            self._btn_ime.setStyleSheet(IME_EN_BTN)
            self._btn_ime.setToolTip("한/영 전환  [현재: 영문]")

    # ── 접근성 권한 ──────────────────────────────────────────

    def _check_perm(self):
        from src.actions._macos import is_trusted
        trusted = is_trusted()
        self._warn_bar.setVisible(not trusted)
        for btn in self._action_btns:
            btn.setEnabled(trusted)
        self.adjustSize()

    def _open_accessibility(self):
        from src.actions._macos import request_accessibility, open_accessibility_settings
        request_accessibility()
        open_accessibility_settings()

    # ── 컨텍스트 메뉴 (우클릭만) ─────────────────────────────

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        aot = self._cfg.get("always_on_top", True)
        act_aot = QAction(f"{'✓ ' if aot else ''}항상 위", self)
        act_aot.triggered.connect(self._toggle_always_on_top)
        menu.addAction(act_aot)

        sm = menu.addMenu("스크롤 강도")
        cur = self._cfg.get("scroll_ticks", 3)
        for t in (1, 3, 5, 10):
            a = QAction(f"{'✓ ' if cur == t else ''}{t}틱", self)
            a.triggered.connect(lambda _, v=t: self._set_scroll_ticks(v))
            sm.addAction(a)

        menu.addSeparator()
        aq = QAction("종료", self)
        aq.triggered.connect(self._quit)
        menu.addAction(aq)
        menu.exec(self.mapToGlobal(pos))

    def _toggle_always_on_top(self):
        aot = not self._cfg.get("always_on_top", True)
        self._cfg["always_on_top"] = aot
        self._apply_always_on_top(aot)
        config_store.save(self._cfg)

    def _apply_always_on_top(self, on):
        flags = self.windowFlags()
        flags = (flags | Qt.WindowStaysOnTopHint) if on else (flags & ~Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)
        self.show()

    def _set_scroll_ticks(self, t):
        self._cfg["scroll_ticks"] = t
        config_store.save(self._cfg)

    @staticmethod
    def _quit():
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    # ── 위치 ─────────────────────────────────────────────────

    def _restore_position(self):
        self.move(self._cfg.get("x", 100), self._cfg.get("y", 100))

    def _save_position(self):
        p = self.pos()
        self._cfg["x"], self._cfg["y"] = p.x(), p.y()
        config_store.save(self._cfg)

    def closeEvent(self, event):
        self._save_position()
        super().closeEvent(event)

    # ── 드래그 + 우클릭 메뉴 ─────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            np = event.globalPosition().toPoint() - self._drag_pos
            sc = self.screen().availableGeometry()
            x = max(sc.left() - self.width() + 20, min(np.x(), sc.right() - 20))
            y = max(sc.top(), min(np.y(), sc.bottom() - 20))
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            self._save_position()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.pos())
