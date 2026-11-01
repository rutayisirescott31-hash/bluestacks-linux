"""
Theme and QSS Stylesheet for BlueStacks Linux.
Authentic BlueStacks 5 gaming visual styling.
"""

STYLESHEET = """
QWidget {
    background-color: #0F141C;
    color: #E2E8F0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #0080FF;
    selection-color: #FFFFFF;
}

/* Header */
#HeaderFrame {
    background-color: #161D29;
    border-bottom: 2px solid #20293A;
    padding: 6px 16px;
}

#TitleLabel {
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

#SubtitleLabel {
    color: #00A8FF;
    font-size: 11px;
    font-weight: 600;
}

#StatusBadge {
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 11px;
}

#StatusBadge[status="Running"] {
    background-color: rgba(0, 230, 118, 0.15);
    color: #00E676;
    border: 1px solid #00E676;
}

#StatusBadge[status="Booting"] {
    background-color: rgba(255, 170, 0, 0.15);
    color: #FFAA00;
    border: 1px solid #FFAA00;
}

#StatusBadge[status="Stopped"] {
    background-color: rgba(148, 163, 184, 0.15);
    color: #94A3B8;
    border: 1px solid #475569;
}

/* Tabs */
QTabWidget::pane {
    border: none;
    background-color: #0F141C;
}

QTabBar::tab {
    background-color: #161D29;
    color: #94A3B8;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #20293A;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #0F141C;
    color: #00A8FF;
    border-top: 2px solid #00A8FF;
}

QTabBar::tab:hover:!selected {
    background-color: #1E2738;
    color: #E2E8F0;
}

/* PushButtons */
QPushButton {
    background-color: #1E2738;
    color: #FFFFFF;
    border: 1px solid #2D3A50;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #273349;
    border-color: #0080FF;
}

QPushButton:pressed {
    background-color: #192130;
}

QPushButton#PrimaryButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0070E0, stop:1 #00A8FF);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0080F5, stop:1 #33B8FF);
}

QPushButton#DangerButton {
    background-color: rgba(239, 68, 68, 0.2);
    color: #EF4444;
    border: 1px solid #EF4444;
}

QPushButton#DangerButton:hover {
    background-color: #EF4444;
    color: #FFFFFF;
}

/* Sidebar Tool Buttons */
#SidebarButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px;
    color: #94A3B8;
}

#SidebarButton:hover {
    background-color: #222B3D;
    color: #00A8FF;
    border-color: #00A8FF;
}

/* Cards & Frames */
#GameCard {
    background-color: #161D29;
    border: 1px solid #20293A;
    border-radius: 10px;
    padding: 14px;
}

#GameCard:hover {
    border: 1px solid #0080FF;
    background-color: #1A2332;
}

#CardTitle {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
}

/* Table Widget */
QTableWidget {
    background-color: #161D29;
    border: 1px solid #20293A;
    border-radius: 8px;
    gridline-color: #20293A;
    outline: none;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #20293A;
}

QTableWidget::item:selected {
    background-color: #1E2B40;
    color: #00A8FF;
}

QHeaderView::section {
    background-color: #121822;
    color: #94A3B8;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid #20293A;
    font-weight: 600;
}

/* ComboBox & Inputs */
QComboBox, QLineEdit, QSpinBox {
    background-color: #161D29;
    border: 1px solid #2D3A50;
    border-radius: 6px;
    padding: 6px 12px;
    color: #FFFFFF;
}

QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #0080FF;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* ScrollBars */
QScrollBar:vertical {
    background: #0F141C;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2D3A50;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #0080FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #20293A;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: 700;
    color: #00A8FF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
"""
