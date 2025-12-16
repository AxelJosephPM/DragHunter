class Colors:
    BG = "#0d0f12"
    PANEL = "#11151a"
    BORDER = "#243041"
    ACCENT_RED = "#f03a47"
    ACCENT_CYAN = "#2de2e6"
    ACCENT_GREEN = "#9ef01a"
    TEXT = "#e6eaef"
    MUTED = "#6f7784"


def build_stylesheet() -> str:
    """Qt stylesheet inspirado en la estética industrial de Akira."""
    return f"""
    QWidget {{
        background-color: {Colors.BG};
        color: {Colors.TEXT};
        font-family: "Cascadia Mono", "Consolas", "Courier New", monospace;
        font-size: 11px;
        letter-spacing: 0.5px;
    }}
    QGroupBox {{
        background-color: {Colors.PANEL};
        border: 1px solid {Colors.ACCENT_CYAN};
        border-radius: 0px;
        margin-top: 8px;
        padding: 4px;
        font-weight: 700;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 6px;
        padding: 0 4px;
        color: {Colors.ACCENT_RED};
        background-color: {Colors.BG};
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {Colors.BG};
        border: 1px solid {Colors.ACCENT_CYAN};
        border-radius: 0px;
        padding: 4px;
        selection-background-color: {Colors.ACCENT_RED};
        selection-color: {Colors.BG};
    }}
    QPlainTextEdit {{
        background-color: #0a0c10;
        border: 1px solid {Colors.ACCENT_RED};
        padding: 6px;
        border-radius: 0px;
    }}
    QTabBar::tab {{
        background: {Colors.PANEL};
        color: {Colors.TEXT};
        padding: 6px 10px;
        border: 1px solid {Colors.ACCENT_CYAN};
        border-bottom: none;
        border-radius: 0px;
        min-width: 110px;
    }}
    QTabBar::tab:selected {{
        background: {Colors.ACCENT_RED};
        color: {Colors.BG};
    }}
    QPushButton {{
        background-color: #161a20;
        border: 1px solid {Colors.ACCENT_CYAN};
        padding: 6px 12px;
        border-radius: 0px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        border-color: {Colors.ACCENT_RED};
    }}
    QPushButton#runButton {{
        background-color: {Colors.ACCENT_RED};
        color: {Colors.BG};
        border: 1px solid {Colors.ACCENT_RED};
    }}
    QPushButton#stopButton {{
        background-color: {Colors.BG};
        color: {Colors.ACCENT_RED};
        border: 1px solid {Colors.ACCENT_RED};
    }}
    QLabel {{
        color: {Colors.TEXT};
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {Colors.ACCENT_CYAN};
        background: {Colors.BG};
    }}
    QCheckBox::indicator:checked {{
        background: {Colors.ACCENT_RED};
        border: 1px solid {Colors.ACCENT_RED};
    }}
    """
