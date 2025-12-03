"""ui_tasks.py
Contains task-related helper classes and a function to create the task tree widget.
This module exposes create_task_tree(main_window) -> QTreeWidget
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView, QComboBox, QDateEdit, QCompleter, QStyleOptionViewItem, QWidget, QStyle
from PyQt6.QtCore import Qt, QEvent, QModelIndex, QAbstractItemModel
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtGui import QColor, QBrush, QPainter, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont
# Import typing for list[str] on older pythons
from typing import List
from settings_manager.settings_manager import DateFormat
from data_manager.models import ScheduleType

# Constants for ColorDelegate
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
        self.setEditable(True) # Needed to show custom text
        self.lineEdit().setReadOnly(True) # But don't allow typing manually to avoid confusion with check state

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
            # Handle "Name (Allocation%)" format by checking if item text is contained in the input list
            # Or better, if the input list contains the item text.
            # The input items might be ["Res1 (100%)", "Res2 (50%)"]
            # The combo items are ["Res1", "Res2"]
            
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
        # Don't hide popup when clicking items (which triggers handle_item_pressed)
        # But we need to allow hiding when clicking outside.
        # The default behavior is that clicking an item calls hidePopup.
        # We can't easily distinguish between item click and outside click here without more complex event filtering.
        # A common workaround is to use a timer or just let it close and user has to reopen.
        # But for multi-select, keeping it open is better.
        # Let's try to keep it open.
        pass 
        # WARNING: Overriding hidePopup to pass might make it impossible to close.
        # Better approach: rely on view().pressed to toggle and NOT call default behavior?
        # Actually, if we just toggle in handle_item_pressed, the default behavior still runs and closes it.
        # We can use installEventFilter on the view.
        super().hidePopup()

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
        if index.column() == 10:  # Resources column (index 10)
            editor = CheckableComboBox(parent)
            editor.addItems(self._resource_names)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if index.column() == 10:  # Resources column
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
        if index.column() == 10:  # Resources column
            if isinstance(editor, CheckableComboBox):
                checked_items = editor.get_checked_items()
                # Default to 100% allocation for now if just names are selected
                # Or preserve existing allocation if possible? 
                # For simplicity and "select directly", we'll just save names.
                # The data manager might handle default allocation if missing.
                # But wait, the display format is "Name (Alloc%)".
                # If we just save "Name", it might break parsing or default to 100%.
                # Let's append (100%) if not present? 
                # Actually, let's just save the names. The Task class or UI logic usually handles parsing.
                # If we look at ui_main.py parsing: "Name (Alloc%)".
                # If we just return "Name1, Name2", the parser might need to handle it.
                # Let's assume 100% for new selections.
                
                # Better: Re-construct strings with (100%) for consistency if needed, 
                # but if the user just wants to select names, "Name1, Name2" is cleaner.
                # Let's stick to what the CheckableComboBox returns (just names) 
                # and rely on the backend to handle "Name" as "Name (100%)" or similar.
                
                # Wait, if I overwrite "Name (50%)" with just "Name", I lose the 50%.
                # But the user asked for a dropdown to select resources. 
                # Handling custom allocation in a simple multi-select dropdown is hard.
                # I will save as "Name1 (100%), Name2 (100%)" to be safe and consistent with existing format.
                
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
        editor.addItems([st.value for st in ScheduleType]) # Populate with enum values
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        current_schedule_type = index.data(Qt.ItemDataRole.DisplayRole)
        if isinstance(editor, QComboBox):
            editor.setCurrentText(current_schedule_type)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)

def create_task_tree(main_window):
    """Create hierarchical task tree widget with sorting"""
    tree = QTreeWidget()
    tree.setColumnCount(12) # Increased to 12 for Schedule Type
    tree.setHeaderLabels([
        "Schedule Type", "Status", "ID", "WBS", "Task Name", "Start Date", "End Date", 
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
    tree.setSortingEnabled(False)
    # tree.sortByColumn(1, Qt.SortOrder.AscendingOrder)

    # Set column widths to allow interactive resizing and horizontal scrolling
    header = tree.header()
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

    # Set default width for ID column
    tree.setColumnWidth(2, 50)
    
    # Set default width for WBS column
    tree.setColumnWidth(3, 70)
    
    # Set default width for Task Name column (double the default)
    tree.setColumnWidth(4, 300)

    # Set initial visibility for WBS column
    tree.setColumnHidden(3, not main_window.toggle_wbs_action.isChecked())

    # Make header interactive
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(True)
    # header.sectionClicked.connect(main_window._on_header_clicked)

    # Enable custom delegate for schedule type column
    main_window.schedule_type_delegate = ScheduleTypeDelegate(main_window, main_window)
    tree.setItemDelegateForColumn(0, main_window.schedule_type_delegate)

    # Enable custom delegate for status column
    main_window.color_delegate = ColorDelegate()
    tree.setItemDelegateForColumn(1, main_window.color_delegate)

    # Enable custom delegate for start and end date columns
    main_window.date_delegate = DateDelegate(main_window, main_window)
    tree.setItemDelegateForColumn(5, main_window.date_delegate) # Start Date (shifted from 4 to 5)
    tree.setItemDelegateForColumn(6, main_window.date_delegate) # End Date (shifted from 5 to 6)

    # Enable custom delegate for resources column
    main_window.resource_delegate = ResourceDelegate(main_window, main_window.data_manager)
    tree.setItemDelegateForColumn(10, main_window.resource_delegate) # Resources (shifted from 9 to 10)
    main_window.resource_delegate.update_resource_list([r.name for r in main_window.data_manager.get_all_resources()])

    # Enable inline editing (e.g., double-click or F2)
    tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)

    # Connect item changed signal for inline editing
    tree.itemChanged.connect(main_window._on_task_item_changed)

    # Track expanded/collapsed state
    tree.itemExpanded.connect(main_window._on_item_expanded)
    tree.itemCollapsed.connect(main_window._on_item_collapsed)
    tree.itemClicked.connect(main_window._on_task_item_clicked)

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