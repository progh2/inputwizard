BTN_BASE = """
    QPushButton {{
        background-color: rgba(50, 50, 50, 210);
        color: white;
        border: 1px solid rgba(255,255,255,60);
        border-radius: 8px;
        font-size: {font_size}px;
        padding: 0px;
    }}
    QPushButton:hover {{
        background-color: rgba(80, 80, 80, 230);
        border: 1px solid rgba(255,255,255,120);
    }}
    QPushButton:pressed {{
        background-color: rgba(30, 30, 30, 240);
    }}
"""

SCROLL_BTN = BTN_BASE.format(font_size=16)
ACTION_BTN = BTN_BASE.format(font_size=14)
