"""ui_tasks.py
Contains task-related helper classes and a function to create the task tree widget.
This module exposes create_task_tree(main_window) -> QTreeWidget
"""

from PyQt6.QtWidgets import QTreeWidget, QHeaderView, QComboBox, QDateEdit, QStyleOptionViewItem, QWidget, QStyle, QAbstractItemView
from PyQt6.QtCore import Qt, QModelIndex, QAbstractItemModel, QDate
from PyQt6.QtGui import QColor, QBrush, QPainter, QStandardItemModel, QStandardItem,  QShortcut, QKeySequence, QFont, QFontDatabase
from PyQt6.QtWidgets import QStyledItemDelegate
from settings_manager.settings_manager import DateFormat
from data_manager.models import ScheduleType
from constants.constants import CIRCLE_SIZE, LEFT_PADDING, TEXT_SHIFT

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

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """Disable editing for this column"""
        return None

class NoEditDelegate(QStyledItemDelegate):
    """Delegate to disable editing for specific columns"""
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        return None

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

class CheckableComboBox(QComboBox):
    """ComboBox with checkable items for multi-selection"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)
        self._update_text()

    def addItem(self, text, data=None):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def set_checked_items(self, items):
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
           
            is_checked = False
            for input_item in items:
                if item.text() == input_item or input_item.startswith(f"{item.text()} ("):
                    is_checked = True
                    break
            
            item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
        self._update_text()

    def get_checked_items(self):
        checked_items = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_items.append(item.text())
        return checked_items

    def _update_text(self):
        items = self.get_checked_items()
        text = ", ".join(items)
        self.setEditText(text)
        
    def hidePopup(self):
        pass
        super().hidePopup()

class ResourceDelegate(QStyledItemDelegate):
    """Custom delegate for resource assignment with a dropdown"""
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._resource_names = []

    def update_resource_list(self, resource_names: list[str]):
        """Update the internal list of resource names"""
        self._resource_names = resource_names

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.column() == 10: 
            editor = CheckableComboBox(parent)
            editor.addItems(self._resource_names)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if index.column() == 10:
            current_resources_str = index.data(Qt.ItemDataRole.DisplayRole)
            if isinstance(editor, CheckableComboBox):
                # Parse comma-separated list
                if current_resources_str:
                    current_resources = [r.strip() for r in current_resources_str.split(',')]
                    editor.set_checked_items(current_resources)
                else:
                    editor.set_checked_items([])
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.column() == 10:
            if isinstance(editor, CheckableComboBox):
                checked_items = editor.get_checked_items()               
                formatted_items = [f"{item} (100%)" for item in checked_items]
                new_resources_str = ", ".join(formatted_items)
                model.setData(index, new_resources_str, Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)

class ScheduleTypeDelegate(QStyledItemDelegate):
    """Custom delegate for Schedule Type column with a QComboBox"""
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QComboBox(parent)
        editor.addItems(["Auto Scheduled (Auto)", "Manually Scheduled (Manual)"])
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        current_schedule_type = index.data(Qt.ItemDataRole.DisplayRole)
        if isinstance(editor, QComboBox):
            if current_schedule_type == "Auto":
                editor.setCurrentText("Auto Scheduled (Auto)")
            elif current_schedule_type == "Manual":
                editor.setCurrentText("Manually Scheduled (Manual)")
            else:
                editor.setCurrentText(current_schedule_type)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QComboBox):
            text = editor.currentText()
            # Map back to code
            if "(Auto)" in text:
                model.setData(index, "Auto", Qt.ItemDataRole.EditRole)
            elif "(Manual)" in text:
                model.setData(index, "Manual", Qt.ItemDataRole.EditRole)
            else:
                # Handle unexpected values by extracting contents in parentheses if available
                import re
                match = re.search(r'\((.*?)\)', text)
                if match:
                    model.setData(index, match.group(1), Qt.ItemDataRole.EditRole)
                else:
                    model.setData(index, text, Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)

class TaskNameDelegate(QStyledItemDelegate):
    """Custom delegate for Task Name column with font styling"""
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Paint cell with custom font styling"""
        # Get the tree widget item
        tree_widget = self.parent()
        if hasattr(tree_widget, 'itemFromIndex'):
            item = tree_widget.itemFromIndex(index)
        else:
            # Fallback to default painting
            super().paint(painter, option, index)
            return
        
        if not item:
            super().paint(painter, option, index)
            return
        
        # Get task ID from column 2
        task_id = item.data(2, Qt.ItemDataRole.UserRole)
        if task_id is None or not self.main_window:
            super().paint(painter, option, index)
            return
        
        # Get task from data manager
        task = self.main_window.data_manager.get_task(task_id)
        if not task:
            super().paint(painter, option, index)
            return
        
        # Get font styling properties
        font_family = getattr(task, 'font_family', None)
        font_size = getattr(task, 'font_size', None)
        font_color = getattr(task, 'font_color', '#000000')
        bg_color = getattr(task, 'background_color', '#FFFFFF')
        is_bold = getattr(task, 'font_bold', False)
        is_italic = getattr(task, 'font_italic', False)
        is_underline = getattr(task, 'font_underline', False)
        
        # Determine defaults from option
        default_font = option.font
        
        if not font_family:
            font_family = default_font.family()
        
        if not font_size:
             font_size = default_font.pointSize()
        
        # Validate font family and fallback to default if not available
        available_families = QFontDatabase.families()
        if font_family not in available_families:
            fallback_fonts = ['Arial', 'Helvetica', 'Sans Serif', 'Segoe UI', 'Tahoma']
            found = False
            for fallback in fallback_fonts:
                if fallback in available_families:
                    font_family = fallback
                    found = True
                    break
            if not found:
                 font_family = 'Arial'

        # Draw background
        painter.save()
        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if bg_color and bg_color.lower() != '#ffffff':
                 painter.fillRect(option.rect, QColor(bg_color))
            else:
                 painter.fillRect(option.rect, Qt.BrushStyle.NoBrush) 
        
        # Create and set font
        font = QFont(font_family, font_size)
        font.setBold(is_bold)
        font.setItalic(is_italic)
        font.setUnderline(is_underline)
        painter.setFont(font)
        
        # Set text color
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            default_colors = ['#000000', '#00000000', 'black']
            if str(font_color).lower() in default_colors:
                 painter.setPen(option.palette.text().color())
            else:
                 painter.setPen(QColor(font_color))
        
        # Draw text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            painter.drawText(option.rect.adjusted(5, 0, -5, 0), 
                           Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, 
                           text)
        
        painter.restore()

def create_task_tree(main_window):
    """Create hierarchical task tree widget with sorting"""
    tree = QTreeWidget()
    tree.setColumnCount(12)
    tree.setHeaderLabels([
        "Schedule Type", "Status", "ID", "WBS", "Task Name", "Start Date", "End Date", 
        main_window.data_manager.settings.get_duration_label(),
        "% Complete", "Dependencies", "Resources", "Notes"
    ])

    # Add tooltips to headers
    header = tree.headerItem()
    tooltips = [
        "How the task is scheduled (e.g., Manually Scheduled or Auto Scheduled)",
        "The current status of the task (e.g., In Progress, Overdue)",
        "The unique identifier for the task",
        "Work Breakdown Structure code",
        "The name of the task",
        "The start date of the task",
        "The end date of the task",
        "The duration of the task",
        "The percentage of completion for the task",
        "Predecessor tasks",
        "Assigned resources",
        "Additional notes for the task"
    ]
    for i, tooltip in enumerate(tooltips):
        header.setToolTip(i, tooltip)

    tree.setAlternatingRowColors(True)
    tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    tree.setIndentation(0)
    tree.setRootIsDecorated(True)
    tree.setSortingEnabled(False)
    header = tree.header()
    header.setSortIndicator(2, Qt.SortOrder.AscendingOrder)
    
    # First, resize all sections to their content
    for i in range(tree.columnCount()):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    # Then, allow interactive resizing for all columns except Notes (which will stretch)
    for i in range(tree.columnCount()):
        if i != 11:  # All columns except Notes
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
    
    # Make Notes column (index 11) stretch to fill remaining space
    header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)
    header.setStretchLastSection(False)
    tree.setColumnWidth(2, 50) # Default width for ID column
    tree.setColumnWidth(3, 70) # Default width for WBS column
    tree.setColumnWidth(4, 500) # Default width for Task Name column
    tree.setColumnHidden(3, not main_window.toggle_wbs_action.isChecked())
    
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(True)
    
    main_window.schedule_type_delegate = ScheduleTypeDelegate(main_window, main_window)
    tree.setItemDelegateForColumn(0, main_window.schedule_type_delegate)
    main_window.color_delegate = ColorDelegate()
    tree.setItemDelegateForColumn(1, main_window.color_delegate)
    
    main_window.no_edit_delegate = NoEditDelegate()
    tree.setItemDelegateForColumn(2, main_window.no_edit_delegate) # ID
    tree.setItemDelegateForColumn(3, main_window.no_edit_delegate) # WBS
    main_window.date_delegate = DateDelegate(main_window, main_window)
    tree.setItemDelegateForColumn(5, main_window.date_delegate)
    tree.setItemDelegateForColumn(6, main_window.date_delegate)
    main_window.resource_delegate = ResourceDelegate(main_window, main_window.data_manager)
    tree.setItemDelegateForColumn(10, main_window.resource_delegate)
    main_window.resource_delegate.update_resource_list([r.name for r in main_window.data_manager.get_all_resources()])
    main_window.task_name_delegate = TaskNameDelegate(tree, main_window)
    
    tree.setItemDelegateForColumn(4, main_window.task_name_delegate) # Task Name column
    tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
    tree.itemChanged.connect(main_window._on_task_item_changed)
    tree.itemExpanded.connect(main_window._on_item_expanded)
    tree.itemCollapsed.connect(main_window._on_item_collapsed)
    tree.itemClicked.connect(main_window._on_task_item_clicked)
    tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    tree.customContextMenuRequested.connect(main_window._show_task_context_menu)

    toggle_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), tree)
    toggle_shortcut.activated.connect(main_window._toggle_expand_collapse)
    expand_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Plus), tree)
    expand_shortcut.activated.connect(main_window._expand_selected)

    collapse_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Minus), tree)
    collapse_shortcut.activated.connect(main_window._collapse_selected)

    return tree

    tree.main_window = main_window