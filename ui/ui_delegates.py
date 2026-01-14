"""ui_delegates.py
Extracted delegates and sortable item from ui_main.py
"""
from PyQt6.QtWidgets import QTreeWidgetItem, QComboBox, QCompleter, QStyledItemDelegate, QDateEdit, QWidget, QStyleOptionViewItem, QStyle
from PyQt6.QtCore import Qt, QModelIndex, QDate, QAbstractItemModel
from PyQt6.QtGui import QColor, QBrush, QPainter, QFont
import sys
import os
from datetime import datetime
from constants.constants import CIRCLE_SIZE, LEFT_PADDING, TEXT_SHIFT, ICON_SIZE

class SortableTreeWidgetItem(QTreeWidgetItem):
    """Custom tree widget item with proper sorting for different data types"""

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window

    def _get_id(self):
        """Helper to get ID safely"""
        try:
            val = self.data(2, Qt.ItemDataRole.UserRole)
            if val is not None:
                return int(val)
            return int(self.text(2))
        except (ValueError, TypeError):
            return 0

    def __lt__(self, other):
        """Custom less-than comparison for sorting"""
        tree = self.treeWidget()
        if not tree:
            return False

        column = tree.sortColumn()
       
        # Helper for secondary sort by ID
        def sort_by_id_secondary():
            return self._get_id() < other._get_id()

        # Column 0: Schedule Type (text)
        if column == 0:
            t1 = self.text(0).lower()
            t2 = other.text(0).lower()
            if t1 != t2:
                return t1 < t2
            return sort_by_id_secondary()

        # Column 1: Status (custom sort by color/priority)
        elif column == 1:
            status_order = {
                'red': 0,    # Overdue
                'green': 1,  # In Progress
                'grey': 2,   # Upcoming
                'blue': 3    # Completed
            }
            self_status_color = self.data(1, Qt.ItemDataRole.UserRole)
            other_status_color = other.data(1, Qt.ItemDataRole.UserRole)
            
            self_order = status_order.get(self_status_color, 99)
            other_order = status_order.get(other_status_color, 99)
            
            if self_order != other_order:
                return self_order < other_order
            return sort_by_id_secondary()

        # Column 2: ID (integer)
        elif column == 2:
            id1 = self._get_id()
            id2 = other._get_id()
            return id1 < id2

        # Column 3: WBS (text)
        elif column == 3:
            try:
                parts1 = [int(x) for x in self.text(3).split('.') if x.isdigit()]
                parts2 = [int(x) for x in other.text(3).split('.') if x.isdigit()]
                if parts1 != parts2:
                    return parts1 < parts2
            except:
                t1 = self.text(3).lower()
                t2 = other.text(3).lower()
                if t1 != t2:
                    return t1 < t2
            return sort_by_id_secondary()

        # Column 4: Task Name (text, ignore symbols and spaces)
        elif column == 4:
            text1 = self.text(4).replace('▶', '').replace('◆', '').strip().lstrip()
            text2 = other.text(4).replace('▶', '').replace('◆', '').strip().lstrip()
            if text1.lower() != text2.lower():
                return text1.lower() < text2.lower()
            return sort_by_id_secondary()

        # Column 5: Start Date
        elif column == 5:
            try:
                main_window = self.main_window
                if main_window:
                    date_format_str = main_window._get_strftime_format_string()
                    date1 = datetime.strptime(self.text(5), date_format_str)
                    date2 = datetime.strptime(other.text(5), date_format_str)
                    if date1 != date2:
                        return date1 < date2
                else:
                    if self.text(5) != other.text(5):
                        return self.text(5) < other.text(5)
            except ValueError:
                if self.text(5) != other.text(5):
                    return self.text(5) < other.text(5)
            return sort_by_id_secondary()

        # Column 6: End Date
        elif column == 6:
            try:
                main_window = self.main_window
                if main_window:
                    date_format_str = main_window._get_strftime_format_string()
                    text1 = self.text(6) if self.text(6) != "Milestone" else self.text(5)
                    text2 = other.text(6) if other.text(6) != "Milestone" else other.text(5)
                    date1 = datetime.strptime(text1, date_format_str)
                    date2 = datetime.strptime(text2, date_format_str)
                    if date1 != date2:
                        return date1 < date2
                else:
                    if self.text(6) != other.text(6):
                        return self.text(6) < other.text(6)
            except ValueError:
                if self.text(6) != other.text(6):
                    return self.text(6) < other.text(6)
            return sort_by_id_secondary()

        # Column 7: Duration (numeric)
        elif column == 7:
            try:
                val1 = float(self.text(7)) if self.text(7) else 0
                val2 = float(other.text(7)) if other.text(7) else 0
                if val1 != val2:
                    return val1 < val2
            except ValueError:
                if self.text(7) != other.text(7):
                    return self.text(7) < other.text(7)
            return sort_by_id_secondary()

        # Column 8: % Complete (numeric)
        elif column == 8:
            try:
                val1 = float(self.text(8).replace('%', '').strip())
                val2 = float(other.text(8).replace('%', '').strip())
                if val1 != val2:
                    return val1 < val2
            except ValueError:
                if self.text(8) != other.text(8):
                    return self.text(8) < other.text(8)
            return sort_by_id_secondary()

        # Default: text comparison
        else:
            t1 = self.text(column).lower()
            t2 = other.text(column).lower()
            if t1 != t2:
                return t1 < t2
            return sort_by_id_secondary()

class ColorDelegate(QStyledItemDelegate):
    """Custom delegate to show colored status indicators"""
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Paint cell with color indicator and text"""
        # Get status color from item data
        color_name = index.data(Qt.ItemDataRole.UserRole)
        status_text = index.data(Qt.ItemDataRole.DisplayRole)
        
        # Draw background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            painter.fillRect(option.rect, option.palette.base())
            text_color = option.palette.text().color()
        
        if color_name and status_text:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Color mapping
            color_map = {
                'red': QColor(244, 67, 54),
                'green': QColor(76, 175, 80),
                'grey': QColor(158, 158, 158),
                'blue': QColor(33, 150, 243)
            }
            
            color = color_map.get(color_name, QColor(128, 128, 128))
            
            # Draw circle on the left side with padding
            rect = option.rect
            x = rect.x() + LEFT_PADDING  # Left padding
            y = rect.y() + (rect.height() - CIRCLE_SIZE) // 2
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x, y, CIRCLE_SIZE, CIRCLE_SIZE)
            
            # Draw text to the right of the circle
            text_rect = rect.adjusted(CIRCLE_SIZE + TEXT_SHIFT, 0, 0, 0)  # Shift text right
            
            # Set text color
            painter.setPen(text_color)
            
            # Draw the status text
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, status_text)
            
            painter.restore()
        else:
            # Fallback to default painting if no color data
            super().paint(painter, option, index)
    
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        """Provide size hint for the cell"""
        size = super().sizeHint(option, index)
        # Ensure minimum height for the circle
        size.setHeight(max(size.height(), 24))
        return size


class DateDelegate(QStyledItemDelegate):
    """Custom delegate for date editing with a QDateEdit calendar popup"""
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("yyyy-MM-dd")
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        date_str = index.data(Qt.ItemDataRole.DisplayRole)
        if date_str and date_str != "Milestone":
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            editor.setDate(date)
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QDateEdit):
            model.setData(index, editor.date().toString("yyyy-MM-dd"), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)


class ResourceDelegate(QStyledItemDelegate):
    """Custom delegate for resource assignment with a dropdown"""
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._resource_names = [] # Store resource names internally

    def update_resource_list(self, resource_names: list[str]):
        """Update the internal list of resource names"""
        self._resource_names = resource_names

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.column() == 10:  # Resources column
            editor = QComboBox(parent)
            editor.setEditable(True) # Allow typing for multiple resources or new ones
            editor.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            
            editor.addItems(self._resource_names) # Use the internal list
            
            # Set up completer for suggestions
            completer = QCompleter(editor.model(), editor)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            editor.setCompleter(completer)
            
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if index.column() == 10:  # Resources column
            current_resources_str = index.data(Qt.ItemDataRole.DisplayRole)
            if isinstance(editor, QComboBox):
                editor.setCurrentText(current_resources_str)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.column() == 10:  # Resources column
            if isinstance(editor, QComboBox):
                # Get text from line edit, as it can be multiple comma-separated resources
                new_resources_str = editor.lineEdit().text()
                model.setData(index, new_resources_str, Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ExpandCollapseDelegate(QStyledItemDelegate):
    """Custom delegate to show expand/collapse buttons"""
    
    def __init__(self, tree_widget):
        super().__init__()
        self.tree_widget = tree_widget
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Paint expand/collapse icon"""
        # Manually paint background to respect theme
        painter.fillRect(option.rect, option.palette.base())
        if option.state & QStyle.StateFlag.State_Selected:
             painter.fillRect(option.rect, option.palette.highlight())

        # Get the tree widget item
        item = self.tree_widget.itemFromIndex(index)
        
        # Only draw icon if item has children
        if item and item.childCount() > 0:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw expand/collapse icon
            rect = option.rect
            x = rect.x() + (rect.width() - ICON_SIZE) // 2
            y = rect.y() + (rect.height() - ICON_SIZE) // 2
            
            # Determine if expanded
            is_expanded = item.isExpanded()
            
            # Draw circular button
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(180, 180, 180, 150)))
            painter.drawEllipse(x, y, ICON_SIZE, ICON_SIZE)
            
            # Draw border
            painter.setPen(QColor(100, 100, 100))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(x, y, ICON_SIZE, ICON_SIZE)
            
            # Draw +/- symbol
            painter.setPen(QColor(50, 50, 50))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            symbol = "−" if is_expanded else "+"
            painter.drawText(x, y, ICON_SIZE, ICON_SIZE, 
                           Qt.AlignmentFlag.AlignCenter, symbol)
            
            painter.restore()
    
    def editorEvent(self, event, model, option, index):
        """Handle click on expand/collapse icon"""
        if event.type() == event.Type.MouseButtonRelease:
            item = self.tree_widget.itemFromIndex(index)
            if item and item.childCount() > 0:
                # Toggle expansion
                item.setExpanded(not item.isExpanded())
                return True
        return super().editorEvent(event, model, option, index)
    
    def sizeHint(self, option, index):
        """Provide size hint for the cell"""
        return super().sizeHint(option, index)