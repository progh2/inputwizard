"""키캡 스타일 버튼 디자인."""

# 전체 컨테이너 — 미니 키보드 바디 느낌
CONTAINER = """
#container {
    background-color: rgba(30, 28, 36, 220);
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 25);
}
"""

# 공통 키캡 베이스
_KEYCAP = """
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {top}, stop:0.55 {mid}, stop:1 {bot});
    color: {fg};
    border: 1px solid {border};
    border-bottom: 3px solid {shadow};
    border-radius: 7px;
    font-family: "Arial Rounded MT Bold", "Helvetica Rounded", Arial, sans-serif;
    font-size: {fs}px;
    font-weight: bold;
    padding-bottom: 1px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {top_h}, stop:1 {bot_h});
    border-bottom: 3px solid {shadow};
}}
QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {bot}, stop:1 {top});
    border-bottom: 1px solid {shadow};
    padding-top: 2px;
    padding-bottom: 0px;
}}
"""

# 밝은 크림 키캡 (액션 버튼)
ACTION_BTN = _KEYCAP.format(
    top="#f5efe0", mid="#e8e0cc", bot="#d4c8b0",
    top_h="#fdf6e8", bot_h="#ddd4bc",
    fg="#2c2620",
    border="#b8ab94", shadow="#8a7d66",
    fs=13,
)

# 딥 블루 키캡 (스크롤 버튼)
SCROLL_BTN = _KEYCAP.format(
    top="#5c7cfa", mid="#4c6ef5", bot="#3b5bdb",
    top_h="#748ffc", bot_h="#4263eb",
    fg="#ffffff",
    border="#364fc7", shadow="#1c3a9e",
    fs=15,
)

# 한/영 버튼 — 한글 모드 (따뜻한 주황/빨강 계열)
IME_KO_BTN = _KEYCAP.format(
    top="#ff8c6b", mid="#f76b3c", bot="#e05525",
    top_h="#ffa080", bot_h="#f07840",
    fg="#ffffff",
    border="#c04020", shadow="#8a2c12",
    fs=13,
)

# 한/영 버튼 — 영문 모드 (크림 기본)
IME_EN_BTN = _KEYCAP.format(
    top="#f5efe0", mid="#e8e0cc", bot="#d4c8b0",
    top_h="#fdf6e8", bot_h="#ddd4bc",
    fg="#2c2620",
    border="#b8ab94", shadow="#8a7d66",
    fs=13,
)

# 권한 경고 배너
WARNING_STYLE = """
    QLabel {
        background-color: rgba(220, 80, 50, 200);
        color: white;
        border-radius: 6px;
        font-size: 11px;
        font-weight: bold;
        padding: 4px 6px;
    }
    QLabel:hover {
        background-color: rgba(240, 100, 60, 220);
    }
"""
