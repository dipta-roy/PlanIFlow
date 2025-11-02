"""ui_tasks.py
Contains task-related helper classes and a function to create the task tree widget.
This module exposes create_task_tree(main_window) -> QTreeWidget
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView, QComboBox, QDateEdit, QCompleter, QStyleOptionViewItem, QWidget, QStyle
from PyQt6.QtCore import Qt, QEvent, QModelIndex, QAbstractItemModel
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtGui import QColor, QBrush, QPainter
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont
# Import typing for list[str] on older pythons
from typing import List
from settings_manager import DateFormat

# Constants for ColorDelegate
CIRCLE_SIZE = 10
LEFT_PADDING = 8
TEXT_SHIFT = 15

class SortableTreeWidgetItem(QTreeWidgetItem):
    """Custom QTreeWidgetItem that allows sorting by data role and controls editability"""
    def __init__(self, parent=None):
        super().__init__(parent)
        print("SortableTreeWidgetItem instance created!")

    def __lt__(self, other_item):
        column = self.treeWidget().sortColumn()
        try:
            return self.data(column, Qt.ItemDataRole.DisplayRole) < other_item.data(column, Qt.ItemDataRole.DisplayRole)
        except TypeError:
            # Handle cases where data types might not be directly comparable (e.g., mixed strings and numbers)
            return str(self.data(column, Qt.ItemDataRole.DisplayRole)) < str(other_item.data(column, Qt.ItemDataRole.DisplayRole))

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
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window

    def _get_qdate_format_string(self) -> str:
        """Converts the DateFormat enum to a QDateEdit compatible format string."""
        if self.main_window and self.main_window.data_manager:
            date_format_enum = self.main_window.data_manager.settings.default_date_format
            if date_format_enum == DateFormat.DD_MM_YYYY:
                return "dd-MM-yyyy"
            elif date_format_enum == DateFormat.DD_MMM_YYYY:
                return "dd-MMM-yyyy"
            else: # DateFormat.YYYY_MM_DD
                return "yyyy-MM-dd"
        return "yyyy-MM-dd" # Default fallback

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat(self._get_qdate_format_string())
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        date_str = index.data(Qt.ItemDataRole.DisplayRole)
        if date_str and date_str != "Milestone":
            date = QDate.fromString(date_str, self._get_qdate_format_string())
            editor.setDate(date)
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QDateEdit):
            model.setData(index, editor.date().toString(self._get_qdate_format_string()), Qt.ItemDataRole.EditRole)
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
        if index.column() == 9:  # Resources column
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
        if index.column() == 9:  # Resources column
            current_resources_str = index.data(Qt.ItemDataRole.DisplayRole)
            if isinstance(editor, QComboBox):
                editor.setCurrentText(current_resources_str)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.column() == 9:  # Resources column
            if isinstance(editor, QComboBox):
                # Get text from line edit, as it can be multiple comma-separated resources
                new_resources_str = editor.lineEdit().text()
                model.setData(index, new_resources_str, Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)

def create_task_tree(main_window):
    """Create hierarchical task tree widget with sorting"""
    tree = QTreeWidget()
    tree.setColumnCount(11) # Increased to 11 for WBS
    tree.setHeaderLabels([
        "Status", "ID", "WBS", "Task Name", "Start Date", "End Date", 
        main_window.data_manager.settings.get_duration_label(),
        "% Complete", "Dependencies", "Resources", "Notes"
    ])

    # Configure tree
    tree.setAlternatingRowColors(True)
    tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    tree.setIndentation(0)

    tree.setRootIsDecorated(True)

    # Enable sorting
    tree.setSortingEnabled(True)
    tree.sortByColumn(1, Qt.SortOrder.AscendingOrder)

    # Set column widths to allow interactive resizing
    header = tree.header()
    for i in range(tree.columnCount()):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Task Name column stretches

    # Set initial visibility for WBS column
    tree.setColumnHidden(2, not main_window.toggle_wbs_action.isChecked())

    # Make header interactive
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(True)
    header.sectionClicked.connect(main_window._on_header_clicked)

    # Enable custom delegate for status column
    main_window.color_delegate = ColorDelegate()
    tree.setItemDelegateForColumn(0, main_window.color_delegate)

    # Enable custom delegate for start and end date columns
    main_window.date_delegate = DateDelegate(main_window, main_window)
    tree.setItemDelegateForColumn(4, main_window.date_delegate) # Start Date (shifted)
    tree.setItemDelegateForColumn(5, main_window.date_delegate) # End Date (shifted)

    # Enable custom delegate for resources column
    main_window.resource_delegate = ResourceDelegate(main_window, main_window.data_manager)
    tree.setItemDelegateForColumn(9, main_window.resource_delegate) # Resources (shifted)

    # Enable inline editing (e.g., double-click or F2)
    tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)

    # Connect item changed signal for inline editing
    tree.itemChanged.connect(main_window._on_task_item_changed)

    # Track expanded/collapsed state
    tree.itemExpanded.connect(main_window._on_item_expanded)
    tree.itemCollapsed.connect(main_window._on_item_collapsed)

    # Context menu
    tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    tree.customContextMenuRequested.connect(main_window._show_task_context_menu)

    # Keyboard shortcuts
    from PyQt6.QtGui import QShortcut, QKeySequence

    toggle_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), tree)
    toggle_shortcut.activated.connect(main_window._toggle_expand_collapse)

    expand_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Plus), tree)
    expand_shortcut.activated.connect(main_window._expand_selected)

    collapse_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Minus), tree)
    collapse_shortcut.activated.connect(main_window._collapse_selected)

    return tree

    tree.main_window = main_window