from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

def apply_dark_theme(app):
    """应用深色主题"""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(palette)

def apply_light_theme(app):
    """应用浅色主题"""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 163, 224))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    
    app.setPalette(palette)

# 全局样式表
STYLESHEET = """
    QMainWindow {
        background-color: palette(window);
    }
    
    QWidget {
        background-color: palette(window);
        color: palette(windowText);
    }
    
    QPushButton {
        background-color: palette(button);
        border: 1px solid palette(dark);
        padding: 5px 15px;
        border-radius: 3px;
        outline: none;
    }
    
    QPushButton:hover {
        background-color: palette(light);
    }
    
    QPushButton:pressed {
        background-color: palette(dark);
    }
    
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: palette(base);
        border: 1px solid palette(dark);
        padding: 3px;
        border-radius: 3px;
    }
    
    QTableWidget {
        background-color: palette(base);
        alternate-background-color: palette(alternateBase);
        border: 1px solid palette(dark);
    }
    
    QTableWidget::item:selected {
        background-color: palette(highlight);
        color: palette(highlightedText);
    }
    
    QHeaderView::section {
        background-color: palette(button);
        padding: 5px;
        border: 1px solid palette(dark);
    }
    
    QTabWidget::pane {
        border: 1px solid palette(dark);
    }
    
    QTabBar::tab {
        background-color: palette(button);
        border: 1px solid palette(dark);
        padding: 5px 10px;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background-color: palette(window);
        border-bottom-color: palette(window);
    }
    
    QGroupBox {
        border: 1px solid palette(dark);
        margin-top: 6px;
        padding-top: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px;
    }
    
    QProgressBar {
        border: 1px solid palette(dark);
        border-radius: 3px;
        text-align: center;
    }
    
    QProgressBar::chunk {
        background-color: palette(highlight);
    }
    
    QMenuBar {
        background-color: palette(window);
        border-bottom: 1px solid palette(dark);
    }
    
    QMenuBar::item {
        spacing: 3px;
        padding: 3px 10px;
        background: transparent;
    }
    
    QMenuBar::item:selected {
        background-color: palette(highlight);
        color: palette(highlightedText);
    }
    
    QMenu {
        background-color: palette(window);
        border: 1px solid palette(dark);
    }
    
    QMenu::item {
        padding: 5px 30px 5px 30px;
    }
    
    QMenu::item:selected {
        background-color: palette(highlight);
        color: palette(highlightedText);
    }
"""