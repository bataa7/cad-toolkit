import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.abspath(os.path.join(base_path, relative_path))
    return path.replace('\\', '/')

def get_modern_dark_style():
    """
    Returns a QSS stylesheet for a premium 'Cyber-Tech' dark theme
    Features:
    - Deep blue-grey background (#1e222d)
    - Vivid blue accents (#29b6f6)
    - Soft gradients and shadows
    - Modern flat design with subtle depth
    """
    icon_path = resource_path("resources/checkbox_checked_dark.svg")
    
    return """
    /* Main Window & Background */
    QMainWindow, QWidget {
        background-color: #1e222d;
        color: #eceff1;
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 10pt;
    }

    /* GroupBox - Card Style */
    QGroupBox {
        border: 1px solid #37474f;
        border-radius: 8px;
        margin-top: 28px;
        background-color: #263238;
        padding: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 6px 12px;
        background-color: #29b6f6;
        color: #000000;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        margin-left: 10px;
        font-weight: bold;
    }

    /* Buttons - Modern Flat with Hover Effect */
    QPushButton {
        background-color: #37474f;
        border: 1px solid #455a64;
        border-radius: 6px;
        padding: 8px 20px;
        color: #ffffff;
        font-weight: 500;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #455a64;
        border-color: #29b6f6;
        color: #29b6f6;
    }
    QPushButton:pressed {
        background-color: #29b6f6;
        color: #000000;
        border-color: #29b6f6;
    }
    QPushButton:disabled {
        background-color: #263238;
        border-color: #37474f;
        color: #546e7a;
    }

    /* Input Fields - Clean & Spacious */
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
        background-color: #263238;
        border: 1px solid #455a64;
        border-radius: 6px;
        padding: 6px 10px;
        color: #eceff1;
        selection-background-color: #29b6f6;
        selection-color: #000000;
    }
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #29b6f6;
        background-color: #2c393f;
    }

    /* ComboBox - Modern Dropdown */
    QComboBox {
        background-color: #37474f;
        border: 1px solid #455a64;
        border-radius: 6px;
        padding: 6px 12px;
        color: #ffffff;
    }
    QComboBox:hover {
        border-color: #29b6f6;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left-width: 0px;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
    QComboBox QAbstractItemView {
        background-color: #37474f;
        color: #ffffff;
        selection-background-color: #29b6f6;
        selection-color: #000000;
        border: 1px solid #455a64;
        outline: none;
    }

    /* Tab Widget - Capsule/Modern Style */
    QTabWidget::pane {
        border: 1px solid #37474f;
        background-color: #263238;
        border-radius: 8px;
        margin-top: -1px;
    }
    QTabBar::tab {
        background-color: #1e222d;
        border: 1px solid #37474f;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 24px;
        margin-right: 4px;
        color: #90a4ae;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background-color: #263238;
        color: #29b6f6;
        border-bottom: 2px solid #263238; /* Blend with pane */
        border-top: 2px solid #29b6f6;
    }
    QTabBar::tab:hover:!selected {
        background-color: #2c393f;
        color: #eceff1;
    }

    /* Progress Bar - Sleek */
    QProgressBar {
        border: none;
        border-radius: 4px;
        text-align: center;
        background-color: #37474f;
        color: #ffffff;
        height: 12px;
    }
    QProgressBar::chunk {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #29b6f6, stop:1 #039be5);
        border-radius: 4px;
    }

    /* List Widget - Clean Lists */
    QListWidget {
        background-color: #263238;
        border: 1px solid #37474f;
        border-radius: 6px;
        color: #eceff1;
        outline: none;
    }
    QListWidget::item {
        padding: 8px 12px;
        border-bottom: 1px solid #37474f;
    }
    QListWidget::item:selected {
        background-color: #37474f;
        color: #29b6f6;
        border-left: 3px solid #29b6f6;
    }
    QListWidget::item:hover:!selected {
        background-color: #2c393f;
    }

    /* ScrollBar - Minimalist */
    QScrollBar:vertical {
        border: none;
        background: #1e222d;
        width: 12px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #455a64;
        min-height: 20px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: #607d8b;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::horizontal {
        border: none;
        background: #1e222d;
        height: 12px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: #455a64;
        min-width: 20px;
        border-radius: 6px;
        margin: 2px;
    }

    /* MenuBar & Menus */
    QMenuBar {
        background-color: #1e222d;
        color: #eceff1;
        border-bottom: 1px solid #37474f;
    }
    QMenuBar::item {
        padding: 6px 12px;
        background: transparent;
    }
    QMenuBar::item:selected {
        background-color: #37474f;
        color: #29b6f6;
        border-radius: 4px;
    }
    QMenu {
        background-color: #263238;
        border: 1px solid #37474f;
        color: #eceff1;
        padding: 4px;
        border-radius: 6px;
    }
    QMenu::item {
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #29b6f6;
        color: #000000;
    }

    /* CheckBox */
    QCheckBox {
        spacing: 8px;
        color: #eceff1;
        padding: 4px;
    }
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid #546e7a;
        background-color: #263238;
    }
    QCheckBox::indicator:unchecked:hover {
        border-color: #29b6f6;
    }
    QCheckBox::indicator:checked {
        border-color: #29b6f6;
        image: url("%s");
    }
    QCheckBox::indicator:checked:hover {
        border-color: #4fc3f7;
    }

    /* Status Bar */
    QStatusBar {
        background-color: #263238;
        color: #90a4ae;
        border-top: 1px solid #37474f;
    }
    
    /* ToolTip */
    QToolTip {
        background-color: #37474f;
        color: #ffffff;
        border: 1px solid #29b6f6;
        border-radius: 4px;
        padding: 4px;
    }
    """ % icon_path

def get_modern_light_style():
    """
    Returns a QSS stylesheet for a modern light theme
    Features:
    - Clean white background (#ffffff)
    - Soft grey panels (#f5f5f5)
    - Professional blue accents (#0277bd)
    - Modern flat design
    """
    icon_path = resource_path("resources/checkbox_checked.svg")
    
    return """
    /* Main Window & Background */
    QMainWindow, QWidget {
        background-color: #ffffff;
        color: #333333;
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 10pt;
    }

    /* GroupBox - Card Style */
    QGroupBox {
        border: 1px solid #d0d0d0;
        border-radius: 8px;
        margin-top: 28px;
        background-color: #f9f9f9;
        padding: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 6px 12px;
        background-color: #fbc02d;
        color: #01579b;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        margin-left: 10px;
        font-weight: bold;
    }

    /* Buttons - Modern Flat with Hover Effect */
    QPushButton {
        background-color: #e0e0e0;
        border: 1px solid #c0c0c0;
        border-radius: 6px;
        padding: 8px 20px;
        color: #333333;
        font-weight: 500;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #d6d6d6;
        border-color: #0277bd;
        color: #0277bd;
    }
    QPushButton:pressed {
        background-color: #0277bd;
        color: #ffffff;
        border-color: #0277bd;
    }
    QPushButton:disabled {
        background-color: #f0f0f0;
        border-color: #d0d0d0;
        color: #a0a0a0;
    }

    /* Input Fields - Clean & Spacious */
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 1px solid #c0c0c0;
        border-radius: 6px;
        padding: 6px 10px;
        color: #333333;
        selection-background-color: #0277bd;
        selection-color: #ffffff;
    }
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #0277bd;
        background-color: #ffffff;
    }

    /* ComboBox - Modern Dropdown */
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #c0c0c0;
        border-radius: 6px;
        padding: 6px 12px;
        color: #333333;
    }
    QComboBox:hover {
        border-color: #0277bd;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left-width: 0px;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #333333;
        selection-background-color: #0277bd;
        selection-color: #ffffff;
        border: 1px solid #c0c0c0;
        outline: none;
    }

    /* Tab Widget - Capsule/Modern Style */
    QTabWidget::pane {
        border: 1px solid #d0d0d0;
        background-color: #f9f9f9;
        border-radius: 8px;
        margin-top: -1px;
    }
    QTabBar::tab {
        background-color: #f0f0f0;
        border: 1px solid #d0d0d0;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 10px 24px;
        margin-right: 4px;
        color: #666666;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background-color: #f9f9f9;
        color: #0277bd;
        border-bottom: 2px solid #f9f9f9; /* Blend with pane */
        border-top: 2px solid #0277bd;
    }
    QTabBar::tab:hover:!selected {
        background-color: #e6e6e6;
        color: #333333;
    }

    /* Progress Bar - Sleek */
    QProgressBar {
        border: none;
        border-radius: 4px;
        text-align: center;
        background-color: #e0e0e0;
        color: #333333;
        height: 12px;
    }
    QProgressBar::chunk {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4fc3f7, stop:1 #0277bd);
        border-radius: 4px;
    }

    /* List Widget - Clean Lists */
    QListWidget {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        color: #333333;
        outline: none;
    }
    QListWidget::item {
        padding: 8px 12px;
        border-bottom: 1px solid #f0f0f0;
    }
    QListWidget::item:selected {
        background-color: #e1f5fe;
        color: #0277bd;
        border-left: 3px solid #0277bd;
    }
    QListWidget::item:hover:!selected {
        background-color: #f5f5f5;
    }

    /* ScrollBar - Minimalist */
    QScrollBar:vertical {
        border: none;
        background: #f0f0f0;
        width: 12px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #c0c0c0;
        min-height: 20px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: #a0a0a0;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::horizontal {
        border: none;
        background: #f0f0f0;
        height: 12px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: #c0c0c0;
        min-width: 20px;
        border-radius: 6px;
        margin: 2px;
    }

    /* MenuBar & Menus */
    QMenuBar {
        background-color: #ffffff;
        color: #333333;
        border-bottom: 1px solid #d0d0d0;
    }
    QMenuBar::item {
        padding: 6px 12px;
        background: transparent;
    }
    QMenuBar::item:selected {
        background-color: #e1f5fe;
        color: #0277bd;
        border-radius: 4px;
    }
    QMenu {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        color: #333333;
        padding: 4px;
        border-radius: 6px;
    }
    QMenu::item {
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #0277bd;
        color: #ffffff;
    }

    /* CheckBox */
    QCheckBox {
        spacing: 8px;
        color: #333333;
        padding: 4px;
    }
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid #bdbdbd;
        background-color: #ffffff;
    }
    QCheckBox::indicator:unchecked:hover {
        border-color: #0277bd;
    }
    QCheckBox::indicator:checked {
        border-color: #0277bd;
        image: url("%s");
    }
    QCheckBox::indicator:checked:hover {
        border-color: #01579b;
    }

    /* Status Bar */
    QStatusBar {
        background-color: #f5f5f5;
        color: #666666;
        border-top: 1px solid #d0d0d0;
    }
    
    /* ToolTip */
    QToolTip {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #0277bd;
        border-radius: 4px;
        padding: 4px;
    }
    """ % icon_path
