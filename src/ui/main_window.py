import os
import sys
from PySide6.QtCore import Qt, QPoint, QTimer, QObject, QEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QPushButton, QLabel, QMenu, QMessageBox,
)
from PySide6.QtGui import QAction, QCursor

from src.ui.styles import CONTAINER, SCROLL_BTN, ACTION_BTN, IME_KO_BTN, IME_EN_BTN, WARNING_STYLE
from src.actions import scroll as scroll_action
from src.actions import clipboard as clipboard_action
from src.actions import ime as ime_action
import src.config as config_store

_HOLD_DELAY_MS    = 500
_HOLD_INTERVAL_MS = 80
_PERM_CHECK_MS    = 4_000
_LANG_CHECK_MS    = 600
_ACTIVATE_DELAY   = 150   # 이전 앱 완전 활성화 대기


# ── 버튼 hover 시 PID 캡처 이벤트 필터 ──────────────────────

class _HoverPIDFilter(QObject):
    """버튼에 마우스가 올라오는 순간 frontmost 앱 PID를 캡처."""
    def __init__(self, callback):
        super().__init__()
        self._cb = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self._cb()
        return False


class FloatingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._cfg              = config_store.load()
        self._drag_pos         = None
        self._last_outside_pos = None
        self._target_pid       = None
        self._input_lang       = "en"
        self._hover_filter     = _HoverPIDFilter(self._capture_pid)

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

        self._btn_ime   = self._make_btn("가\nA",  ACTION_BTN, "한/영 전환")
        self._btn_copy  = self._make_btn("⌘\nC",  ACTION_BTN, "복사 (Cmd+C)")
        self._btn_paste = self._make_btn("⌘\nV",  ACTION_BTN, "붙여넣기 (Cmd+V)")
        self._btn_up    = self._make_btn("▲",      SCROLL_BTN, "위로 스크롤")
        self._btn_down  = self._make_btn("▼",      SCROLL_BTN, "아래로 스크롤")

        self._action_btns = [
            self._btn_ime, self._btn_copy, self._btn_paste,
            self._btn_up, self._btn_down,
        ]

        # 버튼마다 hover 진입 시 PID 캡처 필터 설치
        for btn in self._action_btns:
            btn.installEventFilter(self._hover_filter)

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

    def _make_btn(self, text, style, tooltip):
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.setToolTip(tooltip)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setContextMenuPolicy(Qt.PreventContextMenu)
        return btn

    # ── PID 캡처 ─────────────────────────────────────────────

    def _capture_pid(self):
        """버튼 위에 마우스가 올라오는 순간 = 아직 이전 앱이 frontmost."""
        if sys.platform != "darwin":
            return
        try:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app:
                pid = int(app.processIdentifier())
                if pid != os.getpid():
                    self._target_pid = pid
                    print(f"[InputWizard] target pid={pid} ({app.localizedName()})")
        except Exception as e:
            print(f"[InputWizard] pid 캡처 실패: {e}")

    # ── 액션: 이전 앱 활성화 → 딜레이 → 이벤트 전송 ─────────

    def _run_with_focus_restore(self, action_fn):
        pid = self._target_pid
        if sys.platform == "darwin" and pid:
            try:
                from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
                app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                if app and not app.isTerminated():
                    ok = app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                    print(f"[InputWizard] activate pid={pid} → {ok}")
                else:
                    print(f"[InputWizard] 앱 없음 또는 종료됨 pid={pid}")
            except Exception as e:
                print(f"[InputWizard] activate 실패: {e}")
            QTimer.singleShot(_ACTIVATE_DELAY, action_fn)
        else:
            print(f"[InputWizard] pid 없음, fallback CGEventPost")
            action_fn()

    def _on_ime(self):
        pid = self._target_pid
        print(f"[InputWizard] 한영전환 → pid={pid}")
        self._run_with_focus_restore(lambda: ime_action.toggle_ime(pid))

    def _on_copy(self):
        pid = self._target_pid
        print(f"[InputWizard] 복사 → pid={pid}")
        self._run_with_focus_restore(lambda: clipboard_action.copy(pid))

    def _on_paste(self):
        pid = self._target_pid
        print(f"[InputWizard] 붙여넣기 → pid={pid}")
        self._run_with_focus_restore(lambda: clipboard_action.paste(pid))

    # ── 스크롤 버튼 ──────────────────────────────────────────

    def _setup_scroll_btn(self, btn, direction):
        timer = QTimer(self)
        timer.setInterval(_HOLD_INTERVAL_MS)

        def do_scroll():
            pos    = self._last_outside_pos
            qt_pos = (pos.x(), pos.y()) if pos else None
            scroll_action.scroll(direction, self._cfg.get("scroll_ticks", 3), qt_pos)

        timer.timeout.connect(do_scroll)

        def on_press():
            do_scroll()
            QTimer.singleShot(_HOLD_DELAY_MS, lambda: timer.start() if btn.isDown() else None)

        btn.pressed.connect(on_press)
        btn.released.connect(timer.stop)

    # ── 타이머: 마우스 위치 + 접근성 권한 + 입력 언어 ─────────

    def _start_trackers(self):
        t1 = QTimer(self)
        t1.setInterval(50)
        t1.timeout.connect(self._tick_mouse)
        t1.start()

        if sys.platform == "darwin":
            t2 = QTimer(self)
            t2.setInterval(_PERM_CHECK_MS)
            t2.timeout.connect(self._check_perm)
            t2.start()
            QTimer.singleShot(0, self._check_perm)

            t3 = QTimer(self)
            t3.setInterval(_LANG_CHECK_MS)
            t3.timeout.connect(self._update_lang)
            t3.start()
            QTimer.singleShot(0, self._update_lang)

    def _tick_mouse(self):
        pos = QCursor.pos()
        if not self.geometry().contains(pos):
            self._last_outside_pos = pos

        if sys.platform == "darwin":
            self._update_target_pid_from_frontmost()

    def _update_target_pid_from_frontmost(self):
        try:
            from AppKit import NSWorkspace
            front = NSWorkspace.sharedWorkspace().frontmostApplication()
            if front:
                pid = int(front.processIdentifier())
                if pid != os.getpid() and pid != self._target_pid:
                    print(f"[IW] frontmost → {front.localizedName()} pid={pid}")
                    self._target_pid = pid
        except Exception as e:
            pass

    # ── 입력 언어 감지 ────────────────────────────────────────

    def _update_lang(self):
        from src.actions._macos import current_input_lang
        lang = current_input_lang()
        if lang != self._input_lang:
            self._input_lang = lang
            self._refresh_ime_btn(lang)

    def _refresh_ime_btn(self, lang):
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

    def _show_perm_status(self):
        from src.actions._macos import is_trusted
        from ApplicationServices import AXIsProcessTrusted
        trusted = is_trusted()
        pid     = os.getpid()
        import sys as _sys
        msg = QMessageBox(self)
        msg.setWindowTitle("InputWizard — 권한 상태")
        status = "✅ 허용됨" if trusted else "❌ 없음"
        msg.setText(
            f"접근성(손쉬운 사용) 권한: {status}\n\n"
            f"Python 경로:\n{_sys.executable}\n\n"
            f"프로세스 PID: {pid}\n"
            f"마지막 대상 PID: {self._target_pid}\n\n"
            + ("" if trusted else
               "→ 시스템 설정 › 개인 정보 보호 및 보안 ›\n"
               "   손쉬운 사용에서 이 터미널(또는 Python)을 허용하세요.")
        )
        if not trusted:
            msg.addButton("설정 열기", QMessageBox.ButtonRole.ActionRole).clicked.connect(
                self._open_accessibility
            )
        msg.addButton("닫기", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

    # ── 컨텍스트 메뉴 ────────────────────────────────────────

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        aot = self._cfg.get("always_on_top", True)
        a = QAction(f"{'✓ ' if aot else ''}항상 위", self)
        a.triggered.connect(self._toggle_always_on_top)
        menu.addAction(a)

        sm = menu.addMenu("스크롤 강도")
        cur = self._cfg.get("scroll_ticks", 3)
        for t in (1, 3, 5, 10):
            sa = QAction(f"{'✓ ' if cur == t else ''}{t}틱", self)
            sa.triggered.connect(lambda _, v=t: self._set_scroll_ticks(v))
            sm.addAction(sa)

        menu.addSeparator()

        pa = QAction("🔐 권한 상태 확인", self)
        pa.triggered.connect(self._show_perm_status)
        menu.addAction(pa)

        menu.addSeparator()

        qa = QAction("종료", self)
        qa.triggered.connect(self._quit)
        menu.addAction(qa)

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

    # ── 드래그 + 우클릭 ──────────────────────────────────────

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
