from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

class ThemeManager:
    @staticmethod
    def apply_light_mode():
        """Apply light mode theme"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
    
    @staticmethod
    def apply_dark_mode():
        """Apply dark mode theme"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText,
                            QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
                            QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                            QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight,
                            QColor(80, 80, 80))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText,
                            QColor(127, 127, 127))
        
        app.setPalette(dark_palette)
    
    @staticmethod
    @staticmethod
    def get_stylesheet(dark_mode: bool, font_size: int = 9) -> str:
        """Get additional stylesheet for widgets"""
        
        # Base style with dynamic font size
        base_style = f"""
            QWidget {{
                font-size: {font_size}pt;
            }}
        """
        
        if dark_mode:
            return base_style + """
                QTreeWidget {
                    show-decoration-selected: 1;
                    outline: 0;
                    background-color: #353535;
                    color: white;
                }
                QTreeWidget::item {
                    border: 0px;
                    padding: 3px;
                    background-color: transparent;
                    color: white;
                }
                QTreeWidget::item:hover {
                    background-color: #3d3d3d;
                }
                QTreeWidget::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QTreeWidget::branch {
                    background: #2b2b2b;
                }
                QTreeWidget::branch:has-siblings:!adjoins-item {
                    border-image: url(none);
                    background: #2b2b2b;
                }
                QTreeWidget::branch:has-siblings:adjoins-item {
                    border-image: url(none);
                    background: #2b2b2b;
                }
                QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                    border-image: url(none);
                    background: #2b2b2b;
                }
                QTreeWidget::branch:has-children:!has-siblings:closed,
                QTreeWidget::branch:closed:has-children:has-siblings {
                    border-image: url(none);
                    image: url(none);
                }
                QTreeWidget::branch:open:has-children:!has-siblings,
                QTreeWidget::branch:open:has-children:has-siblings {
                    border-image: url(none);
                    image: url(none);
                }
                QHeaderView::section {
                    background-color: #3d3d3d;
                    color: white;
                    padding: 5px;
                    border: 1px solid #6d6d6d;
                    font-weight: bold;
                }
                QHeaderView::section:hover {
                    background-color: #4d4d4d;
                }
                QHeaderView::section:checked {
                    background-color: #2a82da;
                }
                QHeaderView::up-arrow {
                    image: url(none);
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 6px solid white;
                    width: 0px;
                    height: 0px;
                }
                QHeaderView::down-arrow {
                    image: url(none);
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid white;
                    width: 0px;
                    height: 0px;
                }
                QTableWidget {
                    gridline-color: #6d6d6d;
                    background-color: #2b2b2b;
                    alternate-background-color: #353535;
                }
                QTableWidget::item:selected {
                    background-color: #2a82da;
                }
                
                QTabWidget::pane {
                    border: 1px solid #6d6d6d;
                }
                QTabBar::tab {
                    background-color: #3d3d3d;
                    color: white;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #2a82da;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    border: 1px solid #6d6d6d;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:pressed {
                    background-color: #2a82da;
                }
            """
        else:
            return base_style + """
                QTreeWidget {
                    show-decoration-selected: 1;
                    outline: 0;
                }
                QTreeWidget::item {
                    border: 0px;
                    padding: 3px;
                }
                QTreeWidget::item:hover {
                    background-color: #e8f4f8;
                }
                QTreeWidget::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QTreeWidget::branch {
                    background: white;
                }              
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 5px;
                    border: 1px solid #d0d0d0;
                    font-weight: bold;
                }
                QHeaderView::section:hover {
                    background-color: #d0d0d0;
                }
                QHeaderView::section:checked {
                    background-color: #2a82da;
                    color: white;
                }
                QHeaderView::up-arrow {
                    image: url(none);
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 6px solid black;
                    width: 0px;
                    height: 0px;
                }
                QHeaderView::down-arrow {
                    image: url(none);
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid black;
                    width: 0px;
                    height: 0px;
                }
                QTableWidget {
                    gridline-color: #d0d0d0;
                    alternate-background-color: #f5f5f5;
                }
                QTableWidget::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 5px;
                    border: 1px solid #d0d0d0;
                }
                QTabBar::tab {
                    background-color: #e0e0e0;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #d0d0d0;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #2a82da;
                    color: white;
                }
            """