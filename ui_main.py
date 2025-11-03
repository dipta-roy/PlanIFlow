"""
Main UI - PyQt6 Application Interface
Enhanced with hierarchical tasks, dependency types, and status indicators
"""

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton, QTabWidget,
                             QLabel, QMenuBar, QMenu, QToolBar, QStatusBar, QFileDialog,
                             QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QDateEdit, QTextEdit, QListWidget, QMessageBox, QCheckBox,
                             QGroupBox, QSplitter, QAbstractItemView, QHeaderView,
                             QComboBox, QScrollArea, QTreeWidget, QTreeWidgetItem,
                             QStyledItemDelegate, QStyleOptionViewItem, QInputDialog, QStyle, QCompleter)
from PyQt6.QtCore import Qt, QDate, QTimer, QModelIndex, QEvent, QAbstractItemModel
from PyQt6.QtGui import QAction, QIcon, QColor, QBrush, QPainter, QFont, QPixmap
from datetime import datetime, timedelta
import os
import sys
import json
import logging
import re
from data_manager import DataManager, Task, Resource, DependencyType, TaskStatus
from calendar_manager import CalendarManager
from gantt_chart import GanttChart
from exporter import Exporter
from themes import ThemeManager
from settings_manager import ProjectSettings, DurationUnit, DateFormat 
from ui_project_settings import ProjectSettingsDialog, DateFormatDialog
from ui_delegates import SortableTreeWidgetItem, ColorDelegate, DateDelegate, ResourceDelegate
from ui_helpers import get_resource_path, set_application_icon
from ui_menu_toolbar import create_menu_bar, create_toolbar
from ui_dashboard import update_dashboard
from ui_resources import ResourceSheet


# Constants for ColorDelegate
CIRCLE_SIZE = 10
LEFT_PADDING = 8
TEXT_SHIFT = 15

# Constants for status filters
STATUS_ALL = "All"
STATUS_OVERDUE = "Overdue"
STATUS_IN_PROGRESS = "In Progress"
STATUS_UPCOMING = "Upcoming"
STATUS_COMPLETED = "Completed"

# Constants for resource paths
LOGO_PATH = 'images/logo.ico'

class MainWindow(QMainWindow):
    """Main application window with enhanced features"""
    
    def __init__(self):
        super().__init__()
        
        set_application_icon(self, LOGO_PATH)
        
        # Initialize managers
        self.calendar_manager = CalendarManager()
        self.data_manager = DataManager(self.calendar_manager)
        self.current_file = None
        self.dark_mode = False
        self.last_save_time = None
        
        # Expanded tasks tracking for tree view
        self.expanded_tasks = set()
        
        # Listen to settings changes
        self.data_manager.settings.add_listener(self._on_settings_changed)
        
        # Setup UI
        self._update_window_title()
        self.setGeometry(100, 100, 1400, 800)
        
        create_menu_bar(self)
        create_toolbar(self)
        self._create_central_widget()
        self._create_status_bar()
        
        # Apply initial theme
        ThemeManager.apply_light_mode()
        self._apply_stylesheet()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(10000)  
       
        # Try to load last project
        self._try_load_last_project()
   
    def _set_application_icon(self):
        """Set application icon for window and taskbar"""
        icon_path = get_resource_path(LOGO_PATH)
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            
            # Also set for QApplication (affects taskbar)
            app = QApplication.instance()
            if app:
                app.setWindowIcon(icon)
        else:
            print(f"Warning: Logo file not found at {icon_path}")
            
    def _auto_refresh(self):
        """Auto-refresh with smarter logic"""
        # Only refresh if not currently editing
        if not self.task_tree.isPersistentEditorOpen(self.task_tree.currentIndex()):
            # Only update dashboard and charts, not the tree
            self._update_gantt_chart()
            self._update_dashboard()
    
    def _update_window_title(self):
        """Update window title with project name"""
        self.setWindowTitle(f"PlanIFlow - {self.data_manager.project_name}")
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        close_action = QAction("&Close Project", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self._close_project)
        file_menu.addAction(close_action)
        
        file_menu.addSeparator()
        
        import_excel_action = QAction("Import from &Excel...", self)
        import_excel_action.triggered.connect(self._import_excel)
        file_menu.addAction(import_excel_action)
        
        export_excel_action = QAction("Export to E&xcel...", self)
        export_excel_action.triggered.connect(self._export_excel)
        file_menu.addAction(export_excel_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("&Edit")
        # Add Task
        add_task_action = QAction("Add &Task", self)
        add_task_action.setShortcut("Ctrl+T")
        add_task_action.triggered.connect(self._add_task_dialog)
        edit_menu.addAction(add_task_action)
        
        add_milestone_action = QAction("Add &Milestone", self)
        add_milestone_action.setShortcut("Ctrl+M")
        add_milestone_action.triggered.connect(self._add_milestone_dialog)
        edit_menu.addAction(add_milestone_action)
        
        # Add Subtask
        add_subtask_action = QAction("Add &Subtask", self)
        add_subtask_action.setShortcut("Ctrl+Shift+T")
        add_subtask_action.triggered.connect(self._add_subtask_dialog)
        edit_menu.addAction(add_subtask_action)
        
        indent_action = QAction("&Indent Task", self)
        indent_action.setShortcut("Tab")
        indent_action.triggered.connect(self._indent_task)
        edit_menu.addAction(indent_action)
        
        outdent_action = QAction("&Outdent Task", self)
        outdent_action.setShortcut("Shift+Tab")
        outdent_action.triggered.connect(self._outdent_task)
        edit_menu.addAction(outdent_action)
        
        edit_menu.addSeparator()
        
        insert_above_action = QAction("Insert Task &Above", self)
        insert_above_action.setShortcut("Ctrl+Shift+A")
        insert_above_action.triggered.connect(self._insert_task_above)
        edit_menu.addAction(insert_above_action)
        
        insert_below_action = QAction("Insert Task &Below", self)
        insert_below_action.setShortcut("Ctrl+Shift+B")
        insert_below_action.triggered.connect(self._insert_task_below)
        edit_menu.addAction(insert_below_action)
        
        edit_menu.addSeparator()
        
        convert_action = QAction("&Convert Task/Milestone", self)
        convert_action.setShortcut("Ctrl+Shift+M")
        convert_action.triggered.connect(self._convert_to_milestone)
        edit_menu.addAction(convert_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("&Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._update_all_views)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        self.aupand_all_action = QAction("&Expand All Tasks", self)
        expand_all_action.triggered.connect(self._expand_all_tasks)
        view_menu.addAction(expand_all_action)
        
        collapse_all_action = QAction("&Collapse All Tasks", self)
        collapse_all_action.triggered.connect(self._collapse_all_tasks)
        view_menu.addAction(collapse_all_action)
        
        view_menu.addSeparator()
        
        dark_mode_action = QAction("&Dark Mode", self)
        dark_mode_action.setCheckable(True)
        dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        
        view_menu.addSeparator()

        self.toggle_wbs_action = QAction("&Show WBS Column", self)
        self.toggle_wbs_action.setCheckable(True)
        self.toggle_wbs_action.setChecked(True) # Default to visible
        self.toggle_wbs_action.triggered.connect(self._toggle_wbs_column_visibility)
        view_menu.addAction(self.toggle_wbs_action)
        
        view_menu.addSeparator()
        
        sort_menu = view_menu.addMenu("&Sort By")
        
        sort_id_action = QAction("Task &ID", self)
        sort_id_action.triggered.connect(lambda: self._sort_by_column(1))
        sort_menu.addAction(sort_id_action)
        
        sort_name_action = QAction("Task &Name", self)
        sort_name_action.triggered.connect(lambda: self._sort_by_column(2))
        sort_menu.addAction(sort_name_action)
        
        sort_start_action = QAction("&Start Date", self)
        sort_start_action.triggered.connect(lambda: self._sort_by_column(3))
        sort_menu.addAction(sort_start_action)
        
        sort_end_action = QAction("&End Date", self)
        sort_end_action.triggered.connect(lambda: self._sort_by_column(4))
        sort_menu.addAction(sort_end_action)
        
        sort_duration_action = QAction("&Duration", self)
        sort_duration_action.triggered.connect(lambda: self._sort_by_column(5))
        sort_menu.addAction(sort_duration_action)
        
        sort_complete_action = QAction("% &Complete", self)
        sort_complete_action.triggered.connect(lambda: self._sort_by_column(6))
        sort_menu.addAction(sort_complete_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        
        duration_unit_action = QAction("&Duration Unit...", self)
        duration_unit_action.triggered.connect(self._show_duration_unit_settings)
        settings_menu.addAction(duration_unit_action)
        
        calendar_action = QAction("&Calendar Settings...", self)
        calendar_action.triggered.connect(self._show_calendar_settings)
        settings_menu.addAction(calendar_action)
        
        date_format_action = QAction("&Date Format...", self)
        date_format_action.triggered.connect(self._show_date_format_settings)
        settings_menu.addAction(date_format_action)
        
        view_menu.addSeparator()
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        legend_action = QAction("&Legends", self)
        legend_action.triggered.connect(self._show_status_legend)
        help_menu.addAction(legend_action)
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _toggle_wbs_column_visibility(self):
        """Toggle visibility of the WBS column"""
        is_visible = self.toggle_wbs_action.isChecked()
        self.task_tree.setColumnHidden(2, not is_visible)
        self.status_label.setText(f"✓ WBS column visibility toggled: {is_visible}")

    def _sort_by_column(self, column: int):
        """Sort tree by specific column"""
        current_order = self.task_tree.header().sortIndicatorOrder()
        # Toggle order if clicking same column
        if self.task_tree.sortColumn() == column:
            new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            new_order = Qt.SortOrder.AscendingOrder
        
        self.task_tree.sortByColumn(column, new_order)
        
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.setIconSize(QSize(24, 24))
        
        logo_path = get_resource_path(LOGO_PATH)
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, 
                                                     Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setStyleSheet("padding: 5px;")
            toolbar.addWidget(logo_label)
            
            # Add separator after logo
            toolbar.addSeparator()
        # Project Name Display
        toolbar.addWidget(QLabel("Project: "))
        self.project_name_label = QLabel(self.data_manager.project_name)
        self.project_name_label.setStyleSheet("font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.project_name_label)
        
        project_settings_btn = QAction("⚙️ Project Settings", self)
        project_settings_btn.setToolTip("Open Project Settings")
        project_settings_btn.triggered.connect(self._show_project_settings_dialog)
        toolbar.addAction(project_settings_btn)
        
        toolbar.addSeparator()
        
        # Add Task
        add_task_btn = QAction("➕ Add Task", self)
        add_task_btn.triggered.connect(self._add_task_dialog)
        toolbar.addAction(add_task_btn)
        
        # Add Subtask
        add_subtask_btn = QAction("➕ Add Subtask", self)
        add_subtask_btn.triggered.connect(self._add_subtask_dialog)
        toolbar.addAction(add_subtask_btn)
        
        # Edit Task
        edit_task_btn = QAction("✏️ Edit Task", self)
        edit_task_btn.triggered.connect(self._edit_task_dialog)
        toolbar.addAction(edit_task_btn)
        
        # Delete Task
        delete_task_btn = QAction("🗑️ Delete Task", self)
        delete_task_btn.triggered.connect(self._delete_task)
        toolbar.addAction(delete_task_btn)
        
        # *** ADD MILESTONE BUTTON ***
        add_milestone_btn = QAction("◆ Add Milestone", self)
        add_milestone_btn.setToolTip("Add a milestone (0 duration task)")
        add_milestone_btn.triggered.connect(self._add_milestone_dialog)
        toolbar.addAction(add_milestone_btn)
        toolbar.addSeparator()
        
        # *** ADD INSERT TASK BELOW BUTTON ***
        insert_task_btn = QAction("⬇ Insert Task", self)
        insert_task_btn.setToolTip("Insert task below selected")
        insert_task_btn.triggered.connect(self._insert_task_below)
        toolbar.addAction(insert_task_btn)
        
        # Indent/Outdent
        indent_btn = QAction("→ Indent", self)
        indent_btn.triggered.connect(self._indent_task)
        toolbar.addAction(indent_btn)
        
        outdent_btn = QAction("← Outdent", self)
        outdent_btn.triggered.connect(self._outdent_task)
        toolbar.addAction(outdent_btn)
        
        toolbar.addSeparator()
        
        # Bulk Indent/Outdent
        bulk_indent_btn = QAction("⇥ Bulk Indent", self)
        bulk_indent_btn.setToolTip("Indent selected tasks")
        bulk_indent_btn.triggered.connect(self._bulk_indent_tasks)
        toolbar.addAction(bulk_indent_btn)
        
        bulk_outdent_btn = QAction("⇤ Bulk Outdent", self)
        bulk_outdent_btn.setToolTip("Outdent selected tasks")
        bulk_outdent_btn.triggered.connect(self._bulk_outdent_tasks)
        toolbar.addAction(bulk_outdent_btn)
        
        toolbar.addSeparator()
        
        # *** ADD EXPAND/COLLAPSE BUTTONS ***
        expand_selected_btn = QAction("⊕ Expand Selected", self)
        expand_selected_btn.setToolTip("Expand selected summary task and all subtasks")
        expand_selected_btn.triggered.connect(self._expand_selected_single_item)
        toolbar.addAction(expand_selected_btn)
        
        collapse_selected_btn = QAction("⊖ Collapse Selected", self)
        collapse_selected_btn.setToolTip("Collapse selected summary task")
        collapse_selected_btn.triggered.connect(self._collapse_selected)
        toolbar.addAction(collapse_selected_btn)
        
        expand_all_btn = QAction("⊞ Expand All", self)
        expand_all_btn.setToolTip("Expand all summary tasks")
        expand_all_btn.triggered.connect(self._expand_all_tasks)
        toolbar.addAction(expand_all_btn)
        
        collapse_all_btn = QAction("⊟ Collapse All", self)
        collapse_all_btn.setToolTip("Collapse all summary tasks")
        collapse_all_btn.triggered.connect(self._collapse_all_tasks)
        toolbar.addAction(collapse_all_btn)
        
        toolbar.addSeparator()
        # Add Resource
        add_resource_btn = QAction("👤 Add Resource", self)
        add_resource_btn.triggered.connect(self._add_resource_dialog)
        toolbar.addAction(add_resource_btn)
        
        toolbar.addSeparator()
        
        # Save
        save_btn = QAction("💾 Save", self)
        save_btn.triggered.connect(self._save_project)
        toolbar.addAction(save_btn)
        
        # Export
        export_btn = QAction("📊 Export Excel", self)
        export_btn.triggered.connect(self._export_excel)
        toolbar.addAction(export_btn)
        

    def _create_central_widget(self):
        """Create central widget with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Search/Filter bar
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search tasks by name...")
        self.search_box.textChanged.connect(self._filter_tasks)
        filter_layout.addWidget(self.search_box)
        
        filter_layout.addWidget(QLabel("Filter by Resource:"))
        self.resource_filter = QComboBox()
        self.resource_filter.addItem("All Resources")
        self.resource_filter.currentTextChanged.connect(self._filter_tasks)
        filter_layout.addWidget(self.resource_filter)
        
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([STATUS_ALL, STATUS_OVERDUE, STATUS_IN_PROGRESS, STATUS_UPCOMING, STATUS_COMPLETED])
        self.status_filter.currentTextChanged.connect(self._filter_tasks)
        filter_layout.addWidget(self.status_filter)
        
        clear_filter_btn = QPushButton("Clear Filters")
        clear_filter_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_filter_btn)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Task List Tab (now with tree view)
        self.task_tree = self._create_task_tree()
        self.task_tree.installEventFilter(self)
        self.tabs.addTab(self.task_tree, "📋 Task List")
        
        # Gantt Chart Tab
        gantt_tab_widget = QWidget()
        gantt_tab_layout = QVBoxLayout(gantt_tab_widget)
        
        # Checkboxes for Gantt chart options
        gantt_options_layout = QHBoxLayout()

        self.show_summary_tasks_checkbox = QCheckBox("Show Summary Tasks")
        self.show_summary_tasks_checkbox.setChecked(True) # Default to showing summary tasks
        self.show_summary_tasks_checkbox.stateChanged.connect(self._toggle_gantt_summary_tasks)
        gantt_options_layout.addWidget(self.show_summary_tasks_checkbox)

        self.show_critical_path_checkbox = QCheckBox("Show Critical Path")
        self.show_critical_path_checkbox.setChecked(False) # Default to not showing critical path
        self.show_critical_path_checkbox.stateChanged.connect(self._toggle_gantt_critical_path)
        gantt_options_layout.addWidget(self.show_critical_path_checkbox)
        gantt_options_layout.addStretch() # Push checkboxes to the left

        gantt_tab_layout.addLayout(gantt_options_layout)
        
        self.gantt_chart = GanttChart(dark_mode=self.dark_mode)
        
        # Create a QScrollArea and set the Gantt chart as its widget
        gantt_scroll_area = QScrollArea()
        gantt_scroll_area.setWidgetResizable(True) # Allow the widget to resize with the scroll area
        gantt_scroll_area.setWidget(self.gantt_chart)
        gantt_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        gantt_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        gantt_tab_layout.addWidget(gantt_scroll_area)
        self.tabs.addTab(gantt_tab_widget, "📊 Gantt Chart")
        
        # Resource Summary Tab
        self.resource_summary = self._create_resource_summary()
        self.tabs.addTab(self.resource_summary, "👥 Resources")
        
        # Dashboard Tab
        self.dashboard = self._create_dashboard()
        self.tabs.addTab(self.dashboard, "📈 Dashboard")
        
        layout.addWidget(self.tabs)
    
    def _create_task_tree(self):
        from ui_tasks import create_task_tree
        self.task_tree = create_task_tree(self)
        return self.task_tree

    def _show_task_context_menu(self, position):
        """Show context menu on task right-click"""
        item = self.task_tree.itemAt(position)
        if not item:
            return
        
        # Get task ID from column 1
        task_id = item.data(1, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id) if task_id else None
        
        menu = QMenu(self)
        
        # *** ADD INSERT OPTIONS ***
        insert_above_action = QAction("➕ Insert Task Above", self)
        insert_above_action.triggered.connect(self._insert_task_above)
        menu.addAction(insert_above_action)
        
        insert_below_action = QAction("➕ Insert Task Below", self)
        insert_below_action.triggered.connect(self._insert_task_below)
        menu.addAction(insert_below_action)
        
        menu.addSeparator()
        
        # Edit action
        edit_action = QAction("✏️ Edit Task", self)
        edit_action.triggered.connect(self._edit_task_dialog)
        menu.addAction(edit_action)
        
        # Delete action
        delete_action = QAction("🗑️ Delete Task", self)
        delete_action.triggered.connect(self._delete_task)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # *** ADD CONVERT TO MILESTONE OPTION ***
        if task and not getattr(task, 'is_summary', False):
            is_milestone = getattr(task, 'is_milestone', False)
            
            if is_milestone:
                convert_action = QAction("🔄 Convert to Task", self)
                convert_action.triggered.connect(self._convert_to_milestone)
                menu.addAction(convert_action)
            else:
                convert_action = QAction("🔄 Convert to Milestone", self)
                convert_action.triggered.connect(self._convert_to_milestone)
                menu.addAction(convert_action)
            
            menu.addSeparator()
            
        # Expand/Collapse actions for summary tasks
        if task and task.is_summary:
            if item.isExpanded():
                collapse_action = QAction("⊖ Collapse", self)
                collapse_action.triggered.connect(self._collapse_selected)
                menu.addAction(collapse_action)
                
                collapse_all_action = QAction("⊟ Collapse All Children", self)
                collapse_all_action.triggered.connect(lambda: self._collapse_item_recursively(item))
                menu.addAction(collapse_all_action)
            else:
                expand_action = QAction("⊕ Expand", self)
                expand_action.triggered.connect(self._expand_selected_single_item)
                menu.addAction(expand_action)
                
                expand_all_action = QAction("⊞ Expand All Children", self)
                expand_all_action.triggered.connect(self._expand_all_children_of_selected)
                menu.addAction(expand_all_action)
            
            menu.addSeparator()
        
        # Indent/Outdent
        indent_action = QAction("→ Indent", self)
        indent_action.triggered.connect(self._indent_task)
        menu.addAction(indent_action)
        
        if task and task.parent_id is not None:
            outdent_action = QAction("← Outdent", self)
            outdent_action.triggered.connect(self._outdent_task)
            menu.addAction(outdent_action)
        
        menu.addSeparator()
        
        # Add subtask
        add_subtask_action = QAction("➕ Add Subtask", self)
        add_subtask_action.triggered.connect(self._add_subtask_dialog)
        menu.addAction(add_subtask_action)
        
        menu.exec(self.task_tree.mapToGlobal(position))
        
    def _on_tree_clicked(self, index):
        """Handle click on tree item to toggle expand/collapse for summary tasks"""
        item = self.task_tree.itemFromIndex(index)
        if item:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)

            if task and task.is_summary:
                item.setExpanded(not item.isExpanded())
                if item.isExpanded():
                    self.expanded_tasks.add(task_id)
                else:
                    self.expanded_tasks.discard(task_id)
    def _show_header_context_menu(self, position):
        """Show context menu on header right-click"""
        header = self.task_tree.header()
        column = header.logicalIndexAt(position)
        
        menu = QMenu(self)
        
        # Sort ascending
        sort_asc_action = QAction(f"Sort Ascending", self)
        sort_asc_action.triggered.connect(lambda: self.task_tree.sortByColumn(column, Qt.SortOrder.AscendingOrder))
        menu.addAction(sort_asc_action)
        
        # Sort descending
        sort_desc_action = QAction(f"Sort Descending", self)
        sort_desc_action.triggered.connect(lambda: self.task_tree.sortByColumn(column, Qt.SortOrder.DescendingOrder))
        menu.addAction(sort_desc_action)
        
        menu.addSeparator()
        
        # Reset to default (ID ascending)
        reset_action = QAction("Reset to Default (ID)", self)
        reset_action.triggered.connect(lambda: self.task_tree.sortByColumn(1, Qt.SortOrder.AscendingOrder))
        menu.addAction(reset_action)
        
        menu.exec(header.mapToGlobal(position))
        
    def _on_header_clicked(self, logical_index):
        """Handle header click for sorting"""
        # Toggle sort order
        current_order = self.task_tree.header().sortIndicatorOrder()
        new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        
        # Sort by the clicked column
        self.task_tree.sortByColumn(logical_index, new_order)
    
    def _create_resource_summary(self):
        self.resource_summary = ResourceSheet(self, self.data_manager)
        return self.resource_summary


    def _create_dashboard(self):
        from ui_dashboard import create_dashboard
        self.dashboard = create_dashboard(self)
        return self.dashboard

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.save_time_label = QLabel("")
        self.status_bar.addPermanentWidget(self.save_time_label)
    
    # Tree View Methods
    
    def eventFilter(self, obj, event):
        """Event filter to catch Tab and Shift+Tab for indent/outdent"""
        if obj == self.task_tree and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._outdent_task()
                    return True  # Event handled
                else:
                    self._indent_task()
                    return True  # Event handled
        return super().eventFilter(obj, event)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Track expanded items"""
        # Get task ID from column 1
        task_id = item.data(1, Qt.ItemDataRole.UserRole)
        if task_id:
            self.expanded_tasks.add(task_id)
    
    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Track collapsed items"""
        # Get task ID from column 1
        task_id = item.data(1, Qt.ItemDataRole.UserRole)
        if task_id:
            self.expanded_tasks.discard(task_id)

    def _on_task_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle single click on tree item to toggle expand/collapse for summary tasks"""
        # Check if the clicked item has children (i.e., it's a summary task)
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id:
                if item.isExpanded():
                    self.expanded_tasks.add(task_id)
                else:
                    self.expanded_tasks.discard(task_id)
    
    def _on_task_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle inline editing of task properties"""
        # Block signals to prevent recursive calls during update
        self.task_tree.blockSignals(True)

        task_id = item.data(1, Qt.ItemDataRole.UserRole) # Task ID is in column 1
        task = self.data_manager.get_task(task_id)

        if not task:
            self.task_tree.blockSignals(False)
            return

        original_task = Task.from_dict(task.to_dict()) # Create a copy to revert if validation fails

        try:
            new_value = item.text(column)
            changed = False

            if column == 3:  # Task Name
                # Clean up display markers before saving to actual task name
                cleaned_name = new_value.lstrip(' ▶◆')
                if task.name != cleaned_name:
                    task.name = cleaned_name
                    changed = True
            elif column == 4:  # Start Date
                new_start_date = datetime.strptime(new_value, self._get_strftime_format_string())
                if task.start_date.date() != new_start_date.date():
                    task.start_date = new_start_date
                    changed = True
            elif column == 5:  # End Date
                if not task.is_milestone: # Milestones have fixed end date
                    new_end_date = datetime.strptime(new_value, self._get_strftime_format_string())
                    if task.end_date.date() != new_end_date.date():
                        task.end_date = new_end_date
                        changed = True
            elif column == 6:  # Duration
                new_duration = float(new_value)
                if task.is_milestone and new_duration > 0:
                    task.is_milestone = False
                    task.set_duration_and_update_end(new_duration, self.data_manager.settings.duration_unit, self.calendar_manager)
                    changed = True
                elif not task.is_milestone and new_duration == 0:
                    task.is_milestone = True
                    task.end_date = task.start_date
                    changed = True
                elif not task.is_milestone:
                    current_duration_unit = self.data_manager.settings.duration_unit
                    if abs(task.get_duration(current_duration_unit, self.calendar_manager) - new_duration) > 0.01:
                        task.set_duration_and_update_end(new_duration, current_duration_unit, self.calendar_manager)
                        changed = True
            elif column == 7:  # % Complete
                try:
                    new_percent_complete = int(new_value.strip('%'))
                    if not (0 <= new_percent_complete <= 100):
                        raise ValueError("Percentage must be between 0 and 100.")
                    if task.percent_complete != new_percent_complete:
                        task.percent_complete = new_percent_complete
                        changed = True
                    item.setText(7, f"{task.percent_complete}%")
                except ValueError as ve:
                    QMessageBox.critical(self, "Input Error", f"Invalid input for % Complete: {ve}")
                    self._revert_task_item_in_ui(item, original_task)
                    self.task_tree.blockSignals(False)
                    return
            elif column == 8:  # Dependencies
                new_predecessors = []
                if new_value.strip():
                    for pred_str in new_value.split(','):
                        pred_str = pred_str.strip()
                        if not pred_str:
                            continue

                        lag_days = 0
                        dep_type = DependencyType.FS.name

                        # Regex to handle formats like "1", "1 FS", "1FS+2d", "1 (FS-1d)"
                        # Updated regex: (?:([+-])(\d+)(d)?)?
                        # Group 3: sign (+ or -)
                        # Group 4: digits (the lag value)
                        # Group 5: 'd' if present, None otherwise
                        match = re.match(r'(\d+)\s*([A-Z]{2})?(?:([+-])(\d+)(d)?)?', pred_str)
                        if match:
                            pred_id = int(match.group(1))
                            if match.group(2):
                                dep_type = match.group(2)
                            
                            # Check if lag part was matched
                            if match.group(3) and match.group(4):
                                lag_days = int(match.group(4))
                                if match.group(3) == '-':
                                    lag_days = -lag_days
                            
                            new_predecessors.append((pred_id, dep_type, lag_days))

                if task.predecessors != new_predecessors:
                    task.predecessors = new_predecessors
                    changed = True
                
                # Explicitly update the item's text with the formatted predecessors
                # This ensures the 'd' is added back for display
                formatted_predecessors = []
                for pred_id, dep_type, lag_days in new_predecessors:
                    lag_str = ""
                    if lag_days > 0:
                        lag_str = f"+{lag_days}d"
                    elif lag_days < 0:
                        lag_str = f"{lag_days}d"
                    formatted_predecessors.append(f"{pred_id}{dep_type}{lag_str}")
                item.setText(8, ", ".join(formatted_predecessors))
            elif column == 9:  # Resources
                new_resources = []
                if new_value.strip():
                    for r_str in new_value.split(','):
                        match = re.match(r'(.+?)\s*\((\d+)\s*%\)', r_str.strip())
                        if match:
                            new_resources.append((match.group(1).strip(), int(match.group(2))))
                        else:
                            # For backward compatibility, if no percentage is specified, assume 100%
                            new_resources.append((r_str.strip(), 100))
                if task.assigned_resources != new_resources:
                    task.assigned_resources = new_resources
                    changed = True
            elif column == 10:  # Notes
                if task.notes != new_value:
                    task.notes = new_value
                    changed = True

            if changed:
                if self.data_manager.update_task(task_id, task):
                    self._update_all_views()
                    self.status_label.setText(f"✓ Task '{task.name}' updated successfully")
                else:
                    QMessageBox.warning(self, "Validation Error",
                                      "Task update failed (e.g., circular dependency, invalid date).")
                    # Revert changes in UI if update failed
                    self._revert_task_item_in_ui(item, original_task)

        except Exception as e:
            QMessageBox.critical(self, "Input Error", f"Invalid input for {item.text(0)}: {e}")
            # Revert changes in UI if input was invalid
            self._revert_task_item_in_ui(item, original_task)

        self.task_tree.blockSignals(False)

    def _revert_task_item_in_ui(self, item: QTreeWidgetItem, original_task: Task):
        """Revert the UI item to its original task values"""
        # Temporarily block signals to prevent itemChanged from firing again
        self.task_tree.blockSignals(True)

        # Update each column with original data
        item.setText(3, original_task.name) # Task Name
        item.setText(4, original_task.start_date.strftime(self._get_strftime_format_string())) # Start Date
        if original_task.is_milestone:
            item.setText(5, original_task.start_date.strftime(self._get_strftime_format_string()))
        else:
            item.setText(5, original_task.end_date.strftime(self._get_strftime_format_string())) # End Date
        
        # Duration
        duration = original_task.get_duration(
            self.data_manager.settings.duration_unit,
            self.calendar_manager
        )
        if original_task.is_milestone:
            item.setText(6, "0")
        elif self.data_manager.settings.duration_unit == DurationUnit.HOURS:
            item.setText(6, f"{duration:.1f}")
        else:
            item.setText(6, str(int(duration)))

        item.setText(7, f"{original_task.percent_complete}%") # % Complete
        
        pred_texts = []
        for pred_id, dep_type, lag_days in original_task.predecessors:
            lag_str = ""
            if lag_days > 0:
                lag_str = f"+{lag_days}d"
            elif lag_days < 0:
                lag_str = f"{lag_days}d"
            
            pred_texts.append(f"{pred_id}{dep_type}{lag_str}")
        item.setText(8, ", ".join(pred_texts)) # Dependencies
        resource_texts = [f"{name} ({alloc}%)" for name, alloc in original_task.assigned_resources]
        item.setText(9, ", ".join(resource_texts)) # Resources
        item.setText(10, original_task.notes) # Notes

        self.task_tree.blockSignals(False)

    def _expand_all_tasks(self):
        """Expand all tasks in tree"""
        self.task_tree.expandAll()
        # Track all summary tasks as expanded
        for task in self.data_manager.get_all_tasks():
            if task.is_summary:
                self.expanded_tasks.add(task.id)
        self.status_label.setText("✓ Expanded all tasks")
    
    def _collapse_all_tasks(self):
        """Collapse all tasks in tree"""
        self.task_tree.collapseAll()
        self.expanded_tasks.clear()
    
    # Dialog Methods
    
    def _add_task_dialog(self):
        """Show add task dialog"""
        dialog = TaskDialog(self, self.data_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes']
            )
            
            if self.data_manager.add_task(task):
                self._update_all_views()
                self.status_label.setText(f"Task '{task.name}' added successfully")
            else:
                QMessageBox.warning(self, "Validation Error", 
                                  "Task has circular dependencies or invalid dates.")
    
    def _add_subtask_dialog(self):
        """Show add subtask dialog"""
        # Get selected task
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a parent task first.")
            return
        
        parent_id = selected_items[0].data(1, Qt.ItemDataRole.UserRole)
        parent_task = self.data_manager.get_task(parent_id)
        
        if not parent_task:
            return
        
        dialog = TaskDialog(self, self.data_manager, parent_task=parent_task)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes']
            )
            
            if self.data_manager.add_task(task, parent_id=parent_id):
                self._update_all_views()
                self.status_label.setText(f"Subtask '{task.name}' added to '{parent_task.name}'")
            else:
                QMessageBox.warning(self, "Validation Error", 
                                  "Task has circular dependencies or invalid dates.")
    
    def _edit_task_dialog(self):
        """Show edit task dialog"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a task to edit.")
            return
        
        task_id = selected_items[0].data(1, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        
        if task:
            dialog = TaskDialog(self, self.data_manager, task)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.task_data
                
                updated_task = Task(
                    name=task_data['name'],
                    start_date=task_data['start_date'],
                    end_date=task_data['end_date'],
                    percent_complete=task_data['percent_complete'],
                    predecessors=task_data['predecessors'],
                    assigned_resources=task_data['assigned_resources'],
                    notes=task_data['notes'],
                    task_id=task.id
                )
                
                if self.data_manager.update_task(task_id, updated_task):
                    self._update_all_views()
                    self.status_label.setText(f"Task '{updated_task.name}' updated successfully")
                else:
                    QMessageBox.warning(self, "Validation Error", 
                                      "Task update failed due to circular dependencies.")
    
    def _delete_task(self):
        """Delete selected task"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a task to delete.")
            return
        
        task_id = selected_items[0].data(1, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        
        if task:
            # Check if it has subtasks
            children = self.data_manager.get_child_tasks(task_id)
            msg = f"Delete task '{task.name}'?"
            if children:
                msg = f"Delete task '{task.name}' and all {len(children)} subtask(s)?"
            
            reply = QMessageBox.question(self, "Confirm Delete", msg,
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.data_manager.delete_task(task_id)
                self._update_all_views()
                self.status_label.setText("Task deleted")
    
    def _indent_task(self):
        """Indent selected task (make it a subtask of previous sibling in visual order)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to indent.")
            return
        
        current_item = selected_items[0]
        task_id = current_item.data(1, Qt.ItemDataRole.UserRole)
        
        if task_id is None:
            QMessageBox.warning(self, "Error", "Could not identify selected task.")
            return
        
        task = self.data_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Selected task not found.")
            return
        
        # Get the parent item (None if top-level)
        parent_item = current_item.parent()
        
        # Find the index of current item
        if parent_item is None:
            # Top-level item
            root = self.task_tree.invisibleRootItem()
            index = root.indexOfChild(current_item)
            
            if index == 0:
                QMessageBox.information(self, "Cannot Indent", 
                                      f"Cannot indent '{task.name}'.\n\n"
                                      "This is the first task. There is no task above it to indent under.")
                return
            
            # Get the previous sibling item
            previous_item = root.child(index - 1)
        else:
            # Child item
            index = parent_item.indexOfChild(current_item)
            
            if index == 0:
                QMessageBox.information(self, "Cannot Indent", 
                                      f"Cannot indent '{task.name}'.\n\n"
                                      "This is the first subtask under its parent.\n"
                                      "There is no task above it to indent under.")
                return
            
            # Get the previous sibling item
            previous_item = parent_item.child(index - 1)
        
        # Get the task ID of the previous item
        previous_task_id = previous_item.data(1, Qt.ItemDataRole.UserRole)
        if previous_task_id is None:
            QMessageBox.warning(self, "Error", "Could not identify previous task.")
            return
        
        previous_task = self.data_manager.get_task(previous_task_id)
        if not previous_task:
            QMessageBox.warning(self, "Error", "Previous task not found.")
            return
        
        # Perform the indent (make current task a child of previous task)
        if self.data_manager.move_task(task_id, previous_task_id):
            self.expanded_tasks.add(previous_task_id)  # Auto-expand the new parent
            self._update_all_views()
            self.status_label.setText(f"✓ '{task.name}' indented under '{previous_task.name}'")
        else:
            QMessageBox.warning(self, "Cannot Indent", 
                              f"Cannot indent '{task.name}' under '{previous_task.name}'.\n\n"
                              "This would create a circular dependency.")
    
    def _outdent_task(self):
        """Outdent selected task (move up one level)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to outdent.")
            return
        
        current_item = selected_items[0]
        task_id = current_item.data(1, Qt.ItemDataRole.UserRole)
        
        if task_id is None:
            QMessageBox.warning(self, "Error", "Could not identify selected task.")
            return
        
        task = self.data_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Selected task not found.")
            return
        
        if task.parent_id is None:
            QMessageBox.information(self, "Cannot Outdent", 
                                  f"Cannot outdent '{task.name}'.\n\n"
                                  "This task is already at the top level.")
            return
        
        parent = self.data_manager.get_task(task.parent_id)
        if not parent:
            QMessageBox.warning(self, "Error", "Parent task not found.")
            return
        
        # Get the grandparent ID (None means move to top level)
        new_parent_id = parent.parent_id
        
        # Perform the outdent
        if self.data_manager.move_task(task_id, new_parent_id):
            self._update_all_views()
            if new_parent_id is None:
                self.status_label.setText(f"✓ '{task.name}' moved to top level")
            else:
                grandparent = self.data_manager.get_task(new_parent_id)
                self.status_label.setText(f"✓ '{task.name}' outdented (now under '{grandparent.name}')")
        else:
            QMessageBox.warning(self, "Error", "Failed to outdent task.")
    
    def _add_resource_dialog(self):
        """Show add resource dialog"""
        dialog = ResourceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            resource_data = dialog.get_resource_data()
            
            resource = Resource(
                name=resource_data['name'],
                max_hours_per_day=resource_data['max_hours_per_day'],
                exceptions=resource_data['exceptions']
            )
            
            if self.data_manager.add_resource(resource):
                self._update_all_views()
                self.resource_summary._update_resource_delegates()
                self.status_label.setText(f"Resource '{resource.name}' added successfully")
            else:
                QMessageBox.warning(self, "Duplicate Resource", 
                                  "A resource with this name already exists.")
    
    
    def _delete_resource(self):
        """Delete selected resource"""
        selected_items = self.resource_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a resource to delete.")
            return
        
        row = selected_items[0].row()
        resource_name = self.resource_table.item(row, 0).text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete resource '{resource_name}'?",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_resource(resource_name)
            self._update_all_views()
            self.resource_summary._update_resource_delegates()
            self.status_label.setText("Resource deleted")    
    # Update Methods
    
    def _get_strftime_format_string(self) -> str:
        """Converts the DateFormat enum to a strftime compatible format string."""
        date_format_enum = self.data_manager.settings.default_date_format
        if date_format_enum == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y'
        elif date_format_enum == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y'
        else: # DateFormat.YYYY_MM_DD
            return '%Y-%m-%d'

    def _update_all_views(self):
        """Update all UI views"""
        # For very large projects, consider adding QApplication.processEvents()
        # or moving heavy updates to a separate thread to maintain UI responsiveness.

        self._update_task_tree()
        self._update_gantt_chart()
        
        # Update the data_manager reference in resource_summary
        self.resource_summary.data_manager = self.data_manager
        
        self.resource_summary._update_resource_delegates()
        self._update_resource_summary()
        self._update_dashboard()
        self._update_resource_filter()
        self._update_window_title()
        self.project_name_label.setText(self.data_manager.project_name)
        self.dashboard_project_name.setText(f"<h2>{self.data_manager.project_name}</h2>")
    
    def _update_task_tree(self):
        """Update hierarchical task tree"""
        # Store current sort column and order
        current_sort_column = self.task_tree.sortColumn()
        current_sort_order = self.task_tree.header().sortIndicatorOrder()
        
        # Disable sorting during update
        self.task_tree.setSortingEnabled(False)
        self.task_tree.blockSignals(True)
        self.task_tree.clear()
        
        # Ensure backward compatibility
        for task in self.data_manager.get_all_tasks():
            if not hasattr(task, 'is_milestone'):
                task.is_milestone = False
            if not hasattr(task, 'is_summary'):
                task.is_summary = False
        
        # Get filters
        search_text = self.search_box.text().lower()
        resource_filter = self.resource_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        # --- NEW FILTERING LOGIC ---
        tasks_to_display = set()
        all_tasks = self.data_manager.get_all_tasks()
        
        # Pass 1: Identify tasks that directly match the filter criteria
        for task in all_tasks:
            match_name = True
            if search_text:
                cleaned_search_text = search_text.replace('◆', '').replace('▶', '').strip()
                if cleaned_search_text and cleaned_search_text not in task.name.lower():
                    match_name = False
            
            match_resource = True
            if resource_filter != "All Resources":
                # Check if the resource_filter name exists in any of the assigned_resources tuples
                resource_names_assigned = [res[0] for res in task.assigned_resources]
                if resource_filter not in resource_names_assigned:
                    match_resource = False
            
            match_status = True
            if status_filter != STATUS_ALL:
                if status_filter != task.get_status_text():
                    match_status = False
            
            if match_name and match_resource and match_status:
                tasks_to_display.add(task.id)
        
        # Pass 2: Include all ancestors of tasks that are to be displayed
        # This ensures that if a child matches, its parent is also shown
        for task_id in list(tasks_to_display): # Iterate over a copy as set changes during iteration
            current_task = self.data_manager.get_task(task_id)
            while current_task and current_task.parent_id is not None:
                parent_task = self.data_manager.get_task(current_task.parent_id)
                if parent_task:
                    tasks_to_display.add(parent_task.id)
                    current_task = parent_task
                else:
                    break # Parent not found, stop
        
        # Helper function to add tasks to tree, only if they are in tasks_to_display
        # and their parent is also in tasks_to_display (or is None for top-level)
        added_items = {} # To store QTreeWidgetItem references by task ID

        def add_task_to_tree_filtered(task: Task, parent_item: QTreeWidgetItem = None, level: int = 0):
            if task.id not in tasks_to_display:
                return None

            # Create tree item
            item = SortableTreeWidgetItem(main_window=self)
            
            # Set flags for editability for each column
            for col_idx in range(self.task_tree.columnCount()):
                if col_idx == 0 or col_idx == 1 or col_idx == 2:  # Status, ID, and WBS columns
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            
            # COLUMN 0: Status
            status_color = task.get_status_color()
            status_text = task.get_status_text()
            item.setText(0, status_text)
            item.setData(0, Qt.ItemDataRole.UserRole, status_color)
            
            # COLUMN 1: Task ID (not editable)
            item.setText(1, str(task.id))
            item.setData(1, Qt.ItemDataRole.UserRole, task.id)
            item.setData(1, Qt.ItemDataRole.DisplayRole, task.id)  # Store as int, display as string
            
            # COLUMN 2: WBS (not editable)
            item.setText(2, task.wbs if task.wbs else "")

            # COLUMN 3: Task Name WITH MANUAL INDENTATION
            is_milestone = getattr(task, 'is_milestone', False)
            is_summary = getattr(task, 'is_summary', False)
            
            # Add spacing based on level (use em space for better appearance)
            indent = "    " * level  # 4 spaces per level
            
            if is_milestone:
                display_name = f"{indent}◆ {task.name}"
            elif is_summary:
                display_name = f"{indent}▶ {task.name}"
            else:
                display_name = f"{indent}{task.name}"
            
            item.setText(3, display_name)
            
            # Apply font styling
            font = item.font(3)
            if is_milestone:
                font.setItalic(True)
            elif is_summary:
                font.setBold(True)
            item.setFont(3, font)
            
            # COLUMN 4: Start Date
            item.setText(4, task.start_date.strftime(self._get_strftime_format_string()))
            
            # COLUMN 5: End Date
            if is_milestone:
                item.setText(5, task.start_date.strftime(self._get_strftime_format_string()))
            else:
                item.setText(5, task.end_date.strftime(self._get_strftime_format_string()))
            
            # COLUMN 6: Duration
            duration = task.get_duration(
                self.data_manager.settings.duration_unit,
                self.calendar_manager
            )
            
            if is_milestone:
                item.setText(6, "0")
            elif self.data_manager.settings.duration_unit == DurationUnit.HOURS:
                item.setText(6, f"{duration:.1f}")
            else:
                item.setText(6, str(int(duration)))
            
            # COLUMN 7: % Complete
            item.setText(7, f"{task.percent_complete}%")
            
            # COLUMN 8: Predecessors
            pred_texts = []
            for pred_id, dep_type, lag_days in task.predecessors:
                lag_str = ""
                if lag_days > 0:
                    lag_str = f"+{lag_days}d"
                elif lag_days < 0:
                    lag_str = f"{lag_days}d"
                
                pred_texts.append(f"{pred_id}{dep_type}{lag_str}")
            item.setText(8, ", ".join(pred_texts))
            
            # COLUMN 9: Resources
            resource_texts = [f"{name} ({alloc} %)" for name, alloc in task.assigned_resources]
            item.setText(9, ", ".join(resource_texts))
            
            # COLUMN 10: Notes
            item.setText(10, task.notes)
            
            # Set row color based on status
            color_map = {
                'red': QColor(255, 235, 238),
                'green': QColor(232, 245, 233),
                'grey': QColor(245, 245, 245),
                'blue': QColor(227, 242, 253)
            }
            
            # Special color for milestones
            if is_milestone:
                milestone_color = QColor(255, 255, 200)  # Light yellow
                for col in range(10):
                    item.setBackground(col, QBrush(milestone_color))
            elif not self.dark_mode:
                bg_color = color_map.get(status_color, QColor(255, 255, 255))
                # SLIGHTLY LIGHTER BACKGROUND FOR DEEPER LEVELS
                if level > 0:
                    bg_color = bg_color.lighter(100 + (level * 2))
                for col in range(10):
                    item.setBackground(col, QBrush(bg_color))
            
            # Add to tree
            if parent_item:
                parent_item.addChild(item)
            else:
                self.task_tree.addTopLevelItem(item)
            
            added_items[task.id] = item

            # Add children recursively, but only if they are also in tasks_to_display
            children = self.data_manager.get_child_tasks(task.id)
            for child in children:
                add_task_to_tree_filtered(child, item, level + 1)
            
            # Restore expanded state
            item.setExpanded(True)
            
            return item
        
        # Build tree starting from top-level tasks that are in tasks_to_display
        top_level_tasks = [t for t in self.data_manager.get_top_level_tasks() if t.id in tasks_to_display]
        for task in top_level_tasks:
            add_task_to_tree_filtered(task, None, 0)

        # Re-enable signals
        self.task_tree.blockSignals(False)
        
        # Set WBS column visibility
        self.task_tree.setColumnHidden(2, not self.toggle_wbs_action.isChecked())
        
        # Auto-adjust column widths to content after population
        self.task_tree.header().resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        
        # Re-enable sorting
        self.task_tree.setSortingEnabled(True)
        if current_sort_column >= 0:
            self.task_tree.sortByColumn(current_sort_column, current_sort_order)

    def _update_gantt_chart(self):
        """Update Gantt chart"""
        tasks = self.data_manager.get_all_tasks()
        self.gantt_chart.update_chart(tasks, self.data_manager)
    

    def _update_resource_summary(self):
        """Update resource summary"""
        self.resource_summary.update_summary()


    def _update_dashboard(self):
        """Update dashboard"""
        update_dashboard(self)
    
    def _update_resource_filter(self):
        """Update resource filter dropdown"""
        current = self.resource_filter.currentText()
        self.resource_filter.clear()
        self.resource_filter.addItem("All Resources")
        
        for resource in self.data_manager.get_all_resources():
            self.resource_filter.addItem(resource.name)
        
        index = self.resource_filter.findText(current)
        if index >= 0:
            self.resource_filter.setCurrentIndex(index)
    
    # Filter Methods
    
    def _filter_tasks(self):
        """Apply filters to task tree"""
        self._update_task_tree()
    
    def _clear_filters(self):
        """Clear all filters"""
        self.search_box.clear()
        self.resource_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(self.status_filter.findText(STATUS_ALL))
        self._update_task_tree()
    
    # File Operations
    
    def _new_project(self):
        """Create new project"""
        reply = QMessageBox.question(self, "New Project", 
                                    "Create a new project? Unsaved changes will be lost.",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_all()
            self.current_file = None
            self._update_all_views()
            self.status_label.setText("New project created")
            self._remove_last_project_path()

    def _close_project(self):
        """Close current project"""
        reply = QMessageBox.question(self, "Close Project", 
                                    "Close the current project? Unsaved changes will be lost.",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_all()
            self.current_file = None
            self._update_all_views()
            self.status_label.setText("Project closed")
            self._remove_last_project_path()
    
    def _rename_project(self):
        """Rename current project"""
        text, ok = QInputDialog.getText(self, "Rename Project", 
                                       "Enter new project name:",
                                       text=self.data_manager.project_name)
        
        if ok and text:
            self.data_manager.project_name = text
            self._update_all_views()
            self.status_label.setText(f"Project renamed to '{text}'")
    
    def _open_project(self):
        """Open existing project"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Project Files (*.json)"
        )
        
        if file_path:
            data_manager, calendar_manager, success = Exporter.load_from_json(file_path)
            
            if success:
                self.data_manager = data_manager
                self.data_manager.calendar_manager = calendar_manager
                self.calendar_manager = calendar_manager
                self.current_file = file_path
                self._update_all_views()
                self.status_label.setText(f"Opened: {self.data_manager.project_name}")
                self._save_last_project_path(file_path)
            else:
                QMessageBox.critical(self, "Error", "Failed to open project file.")
    
    def _save_project(self):
        """Save current project"""
        if self.current_file:
            if Exporter.save_to_json(self.data_manager, self.calendar_manager, self.current_file):
                self.last_save_time = datetime.now()
                self.save_time_label.setText(f"Last saved: {self.last_save_time.strftime('%H:%M:%S')}")
                self.status_label.setText("Project saved")
            else:
                QMessageBox.critical(self, "Error", "Failed to save project.")
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Save project with new name"""
        # Suggest filename based on project name
        suggested_name = self.data_manager.project_name.replace(" ", "_") + ".json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", suggested_name, "Project Files (*.json)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            
            if Exporter.save_to_json(self.data_manager, self.calendar_manager, file_path):
                self.current_file = file_path
                self.last_save_time = datetime.now()
                self.save_time_label.setText(f"Last saved: {self.last_save_time.strftime('%H:%M:%S')}")
                self.status_label.setText(f"Saved as: {self.data_manager.project_name}")
                self._save_last_project_path(file_path)
            else:
                QMessageBox.critical(self, "Error", "Failed to save project.")
    
    def _import_excel(self):
        """Import project from Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import from Excel", "", "Excel Files (*.xlsx)"
        )
        
        if file_path:
            data_manager, success = Exporter.import_from_excel(file_path)
            
            if success:
                self.data_manager = data_manager
                self.data_manager.calendar_manager = self.calendar_manager
                self._update_all_views()
                self.status_label.setText("Imported from Excel")
            else:
                QMessageBox.critical(self, "Error", "Failed to import Excel file.")
    
    def _export_excel(self):
        """Export project to Excel"""
        # Suggest filename based on project name
        suggested_name = self.data_manager.project_name.replace(" ", "_") + ".xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", suggested_name, "Excel Files (*.xlsx)"
        )
        
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            
            if Exporter.export_to_excel(self.data_manager, file_path):
                self.status_label.setText("Exported to Excel")
                QMessageBox.information(self, "Success", 
                                      f"Project exported successfully to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export to Excel.")
    
    # Settings
    
    def _show_calendar_settings(self):
        """Show calendar settings dialog"""
        dialog = CalendarSettingsDialog(self, self.calendar_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._update_all_views()
            self.status_label.setText("Calendar settings updated")
    
    def _toggle_dark_mode(self):
        """Toggle dark/light mode"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            ThemeManager.apply_dark_mode()
        else:
            ThemeManager.apply_light_mode()
        
        self._apply_stylesheet()
        self.gantt_chart.set_dark_mode(self.dark_mode)
        self._update_task_tree()  # Refresh colors
    
    def _toggle_gantt_summary_tasks(self, state):
        """Toggle visibility of summary tasks in Gantt chart"""
        show = state == Qt.CheckState.Checked.value
        self.gantt_chart.set_show_summary_tasks(show)
        self.status_label.setText(f"✓ Summary tasks visibility: {'Shown' if show else 'Hidden'}")

    def _toggle_gantt_critical_path(self, state):
        """Toggle visibility of critical path in Gantt chart"""
        show = state == Qt.CheckState.Checked.value
        self.gantt_chart.set_show_critical_path(show)
        self.status_label.setText(f"✓ Critical path visibility: {'Shown' if show else 'Hidden'}")

    def _set_gantt_axis_scale(self, scale: str):
        """Set the X-axis scale for the Gantt chart"""
        self.gantt_chart.set_axis_scale(scale)
        self.status_label.setText(f"✓ Gantt chart axis scale set to: {scale}")
        self._update_gantt_chart()

    def _apply_stylesheet(self):
        """Apply custom stylesheet"""
        stylesheet = ThemeManager.get_stylesheet(self.dark_mode)
        self.setStyleSheet(stylesheet)
    
    def _show_status_legend(self):
        """Show status indicator legend"""
        legend = QMessageBox(self)
        legend.setWindowTitle("Legends")
        legend.setText(
            "<h3>Task Status Indicators</h3>"
            "<p><b style='color: red;'>🔴 Overdue:</b> End date passed and not 100% complete</p>"
            "<p><b style='color: green;'>🟢 In Progress:</b> Started but not yet finished</p>"
            "<p style='color: grey;'><b>⚫ Upcoming:</b> Not yet started</p>"
            "<p><b style='color: blue;'>🔵 Completed:</b> 100% complete</p>"
            "<h3>Dependency Types</h3>"
            "<p><b>FS (Finish-to-Start):</b> Task B starts after Task A finishes</p>"
            "<p><b>SS (Start-to-Start):</b> Task B starts when Task A starts</p>"
            "<p><b>FF (Finish-to-Finish):</b> Task B finishes when Task A finishes</p>"
            "<p><b>SF (Start-to-Finish):</b> Task B finishes when Task A starts</p>"
        )
        legend.exec()
    
    def _show_about(self):
        """Show about dialog"""
        about_box = QMessageBox(self)
        about_box.setWindowTitle("About PlanIFlow - Project Planner")
        about_box.setText(
            f"<h2>PlanIFlow - Project Planner</h2>"
            f"<p>App Version: 1.2</p>"
            f"<p><b>Developed by: Dipta Roy</b></p>"
            "<p>A desktop project management application</p>"
            "<p><b>Key Features:</b></p>"
            "<ul>"
            "<li>Manage Tasks</li>"
            "<li>Manage Task Dependencies</li>"
            "<li>Estimate and Plan Project Timeline</li>"
            "<li>Track Project Status</li>"
            "<li>Visualize Project Timeline</li>"
            "<li>Resource Management</li>"
            "<li>Budget Management</li>"
            "</ul>"
        )
        about_box.setMinimumWidth(400) # Set a minimum width
        about_box.exec()
    
    # Utility Methods
    
    def _save_last_project_path(self, path: str):
        """Save last opened project path"""
        try:
            with open('.last_project', 'w') as f:
                f.write(path)
        except IOError as e:
            logging.error(f"Failed to save last project path: {e}")
    
    def _remove_last_project_path(self):
        """Remove the last opened project path file"""
        try:
            if os.path.exists('.last_project'):
                os.remove('.last_project')
        except IOError as e:
            logging.error(f"Failed to remove last project path: {e}")
    
    def _try_load_last_project(self):
        """Try to load last opened project"""
        try:
            if os.path.exists('.last_project'):
                with open('.last_project', 'r') as f:
                    path = f.read().strip()
                
                if os.path.exists(path):
                    data_manager, calendar_manager, success = Exporter.load_from_json(path)
                    if success:
                        self.data_manager = data_manager
                        self.data_manager.calendar_manager = calendar_manager
                        self.calendar_manager = calendar_manager
                        self.current_file = path
                        self._update_all_views()
                        self.status_label.setText(f"Loaded: {self.data_manager.project_name}")
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load last project: {e}")
        
    def _show_duration_unit_settings(self):
        """Show duration unit settings dialog"""
        dialog = DurationUnitDialog(self, self.data_manager.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_unit = dialog.get_selected_unit()
            old_unit = self.data_manager.settings.duration_unit
            
            if new_unit != old_unit:
                # Confirm change if there are tasks
                if self.data_manager.tasks:
                    reply = QMessageBox.question(
                        self, 
                        "Change Duration Unit",
                                f"Change duration unit from {old_unit.value} to {new_unit.value}?\n\n"
                                "Task durations will be recalculated based on the new unit.\n"
                                "This will update the display but preserve actual start/end dates.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                        
                        # Update setting (will trigger listener)
                        self.data_manager.settings.set_duration_unit(new_unit)
                        self.status_label.setText(f"Duration unit changed to {new_unit.value}")

    def _show_date_format_settings(self):
        """Show date format settings dialog"""
        dialog = DateFormatDialog(self, self.data_manager.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._update_all_views()
            self.status_label.setText("Date format settings updated")
                    
    def _show_project_settings_dialog(self):
        """Show project settings dialog"""
        dialog = ProjectSettingsDialog(self, self.data_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_project_name = dialog.get_project_name()
            new_start_date = dialog.get_project_start_date()

            if new_project_name != self.data_manager.project_name:
                self.data_manager.project_name = new_project_name
                self.status_label.setText(f"Project renamed to '{new_project_name}'")
            
            # Update project start date if changed
            if new_start_date and new_start_date != self.data_manager.settings.project_start_date:
                self.data_manager.settings.project_start_date = new_start_date
                self.status_label.setText("Project start date updated")

            self._update_all_views()
    
    def _on_settings_changed(self, old_unit: DurationUnit, new_unit: DurationUnit):
        """Handle settings changes"""
        # Update task tree header
        header_labels = [
            "Status", "ID", "WBS", "Task Name", "Start Date", "End Date", 
            self.data_manager.settings.get_duration_label(),
            "% Complete", "Dependencies", "Resources", "Notes"
        ]
        self.task_tree.setHeaderLabels(header_labels)
        
        # Ensure WBS column visibility is respected after header update
        self.task_tree.setColumnHidden(2, not self.toggle_wbs_action.isChecked())
        
        # Convert tasks
        self.data_manager.convert_all_tasks_to_unit(new_unit)
        
        # Refresh all views
        self._update_all_views()
    
    def _bulk_indent_tasks(self):
        """Indent multiple selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select one or more tasks to indent.")
            return
        
        # Get task IDs
        task_ids = []
        for item in selected_items:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                task_ids.append(task_id)
        
        if not task_ids:
            return
        
        # Perform bulk indent
        if self.data_manager.bulk_indent_tasks(task_ids):
            self._update_all_views()
            self.status_label.setText(f"✓ Indented {len(task_ids)} task(s)")
        else:
            QMessageBox.warning(self, "Cannot Indent", 
                              "Could not indent the selected tasks.\n"
                              "Make sure they have tasks above them to indent under.")
    
    def _bulk_outdent_tasks(self):
        """Outdent multiple selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select one or more tasks to outdent.")
            return
        
        # Get task IDs
        task_ids = []
        for item in selected_items:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                task_ids.append(task_id)
        
        if not task_ids:
            return
        
        # Perform bulk outdent
        if self.data_manager.bulk_outdent_tasks(task_ids):
            self._update_all_views()
            self.status_label.setText(f"✓ Outdented {len(task_ids)} task(s)")
        else:
            QMessageBox.warning(self, "Cannot Outdent", 
                              "Could not outdent the selected tasks.\n"
                              "Make sure they are not already at top level.")

    def _expand_all_children_of_selected(self):
        """Expand selected summary task and all its children recursively"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a summary task to expand its children.")
            return
        
        expanded_count = 0
        for item in selected_items:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                task = self.data_manager.get_task(task_id)
                if task and task.is_summary:
                    self._expand_item_recursively(item)
                    self.expanded_tasks.add(task_id)
                    # Also add all descendants to expanded_tasks for tracking
                    descendants = self.data_manager.get_all_descendants(task_id)
                    for desc in descendants:
                        if desc.is_summary:
                            self.expanded_tasks.add(desc.id)
                    expanded_count += 1
                else:
                    # If not a summary task, just expand the item if it has children
                    if item.childCount() > 0:
                        item.setExpanded(True)
                        if task_id:
                            self.expanded_tasks.add(task_id)
                        expanded_count += 1
        
        if expanded_count > 0:
            self.status_label.setText(f"✓ Expanded children of {expanded_count} task(s)")
        else:
            QMessageBox.information(self, "No Expandable Children", 
                                  "Selected task(s) have no subtasks to expand recursively.")
    
    def _expand_selected_single_item(self):
        """Expand only the selected summary task (not its children)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to expand.")
            return
        
        expanded_count = 0
        for item in selected_items:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                if item.childCount() > 0:
                    item.setExpanded(True)
                    self.expanded_tasks.add(task_id)
                    expanded_count += 1
        
        if expanded_count > 0:
            self.status_label.setText(f"✓ Expanded {expanded_count} task(s)")
        else:
            QMessageBox.information(self, "No Expandable Task", 
                                  "Selected task(s) have no subtasks to expand.")

    def _collapse_selected(self):
        """Collapse selected summary task"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a summary task to collapse.")
            return
        
        collapsed_count = 0
        for item in selected_items:
            # Get task ID from column 1
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            
            if task_id is not None:
                item.setExpanded(False)
                self.expanded_tasks.discard(task_id)
                collapsed_count += 1
        
        if collapsed_count > 0:
            self.status_label.setText(f"✓ Collapsed {collapsed_count} task(s)")

    def _expand_selected(self):
        """Expand only the selected summary task (not its children)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to expand.")
            return
        
        expanded_count = 0
        for item in selected_items:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                if item.childCount() > 0:
                    item.setExpanded(True)
                    self.expanded_tasks.add(task_id)
                    expanded_count += 1
        
        if expanded_count > 0:
            self.status_label.setText(f"✓ Expanded {expanded_count} task(s)")
        else:
            QMessageBox.information(self, "No Expandable Task", 
                                  "Selected task(s) have no subtasks to expand.")
        collapsed_count = 0
        for item in selected_items:
            # Get task ID from column 1
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            
            if task_id is not None:
                item.setExpanded(False)
                self.expanded_tasks.discard(task_id)
                collapsed_count += 1
        
        if collapsed_count > 0:
            self.status_label.setText(f"✓ Collapsed {collapsed_count} task(s)")
        expanded_count = 0
        for item in selected_items:
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                if item.childCount() > 0:
                    item.setExpanded(True)
                    self.expanded_tasks.add(task_id)
                    expanded_count += 1
        
        if expanded_count > 0:
            self.status_label.setText(f"✓ Expanded {expanded_count} task(s)")
        else:
            QMessageBox.information(self, "No Expandable Task", 
                                  "Selected task(s) have no subtasks to expand.")
            return
        
        collapsed_count = 0
        for item in selected_items:
            # Get task ID from column 1
            task_id = item.data(1, Qt.ItemDataRole.UserRole)
            
            if task_id is not None:
                item.setExpanded(False)
                self.expanded_tasks.discard(task_id)
                collapsed_count += 1
        
        if collapsed_count > 0:
            self.status_label.setText(f"✓ Collapsed {collapsed_count} task(s)")
    
    def _expand_item_recursively(self, item: QTreeWidgetItem):
        """Recursively expand an item and all its children"""
        item.setExpanded(True)
        for i in range(item.childCount()):
            child = item.child(i)
            self._expand_item_recursively(child)
    
    def _collapse_item_recursively(self, item: QTreeWidgetItem):
        """Recursively collapse an item and all its children"""
        for i in range(item.childCount()):
            child = item.child(i)
            self._collapse_item_recursively(child)
        item.setExpanded(False)
    
    def _expand_all_tasks(self):
        """Expand all tasks in tree"""
        self.task_tree.expandAll()
        # Track all summary tasks as expanded
        for task in self.data_manager.get_all_tasks():
            if task.is_summary:
                self.expanded_tasks.add(task.id)
        self.status_label.setText("✓ Expanded all tasks")
    
    def _collapse_all_tasks(self):
        """Collapse all tasks in tree"""
        self.task_tree.collapseAll()
        self.expanded_tasks.clear()
        self.status_label.setText("✓ Collapsed all tasks")
    
    def _toggle_expand_collapse(self):
        """Toggle expand/collapse for selected item"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            return
        
        # Note: This method currently operates on the first selected item.
        # If multiple items are selected, only the first one's state will be toggled.
        item = selected_items[0]
        if item.isExpanded():
            self._collapse_selected()
        else:
            self._expand_selected_single_item()
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        if self.auto_refresh_action.isChecked():
            self.refresh_timer.start(10000)
            self.status_label.setText("✓ Auto-refresh enabled")
        else:
            self.refresh_timer.stop()
            self.status_label.setText("✓ Auto-refresh disabled")
    
    def _auto_refresh(self):
        """Auto-refresh with smarter logic to preserve tree state"""
        # Only refresh if user is not actively interacting
        if not self.task_tree.hasFocus():
            # Only update charts and dashboard, skip tree to preserve expansion
            # self._update_gantt_chart() # Temporarily disable auto-refresh for Gantt chart to prevent resize
            self._update_dashboard()
            self._update_resource_summary()

    def _add_milestone_dialog(self):
        """Show add milestone dialog"""
        dialog = TaskDialog(self, self.data_manager, is_milestone=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['start_date'],  # Milestone: end = start
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                is_milestone=True  # *** MARK AS MILESTONE ***
            )
            
            if self.data_manager.add_task(task):
                self._update_all_views()
                self.status_label.setText(f"✓ Milestone '{task.name}' added successfully")
            else:
                QMessageBox.warning(self, "Validation Error", 
                                  "Milestone has circular dependencies or invalid dates.")

    def _insert_task_above(self):
        """Insert a new task above the selected task (renumbers IDs)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to insert above.")
            return
        
        # Get selected task
        task_id = selected_items[0].data(1, Qt.ItemDataRole.UserRole)
        selected_task = self.data_manager.get_task(task_id)
        
        if not selected_task:
            return
        
        # Show info about renumbering
        reply = QMessageBox.question(
            self,
            "Insert Task",
            f"Insert a new task before '{selected_task.name}' (ID {selected_task.id})?\n\n"
            f"The new task will get ID {selected_task.id}.\n"
            f"All tasks from ID {selected_task.id} onwards will be renumbered.\n"
            f"Predecessors will be updated automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Open dialog for new task
        dialog = TaskDialog(self, self.data_manager)
        
        # Pre-fill with dates just before the selected task
        if selected_task.start_date:
            default_end = selected_task.start_date - timedelta(days=1)
            default_start = default_end - timedelta(days=6)
            
            dialog.start_date_edit.setDate(QDate(default_start.year, default_start.month, default_start.day))
            dialog.end_date_edit.setDate(QDate(default_end.year, default_end.month, default_end.day))
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            new_task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                task_id=None  # Will be set by insert method
            )
            
            if self.data_manager.insert_task_before(new_task, selected_task.id):
                self._update_all_views()
                self.status_label.setText(
                    f"✓ Task '{new_task.name}' inserted at ID {new_task.id}. "
                    f"Tasks renumbered."
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to insert task.")
    
    def _insert_task_below(self):
        """Insert a new task below the selected task (renumbers IDs)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to insert below.")
            return
        
        # Get selected task
        task_id = selected_items[0].data(1, Qt.ItemDataRole.UserRole)
        selected_task = self.data_manager.get_task(task_id)
        
        if not selected_task:
            return
        
        # Show info about renumbering
        new_id = selected_task.id + 1
        reply = QMessageBox.question(
            self,
            "Insert Task",
            f"Insert a new task after '{selected_task.name}' (ID {selected_task.id})?\n\n"
            f"The new task will get ID {new_id}.\n"
            f"All tasks from ID {new_id} onwards will be renumbered.\n"
            f"Predecessors will be updated automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Open dialog for new task
        dialog = TaskDialog(self, self.data_manager)
        
        # Pre-fill with dates just after the selected task
        if selected_task.end_date:
            default_start = selected_task.end_date + timedelta(days=1)
            default_end = default_start + timedelta(days=6)
            
            dialog.start_date_edit.setDate(QDate(default_start.year, default_start.month, default_start.day))
            dialog.end_date_edit.setDate(QDate(default_end.year, default_end.month, default_end.day))
            
            # Auto-add the selected task as predecessor
            dialog._add_predecessor_row()
            if dialog.predecessor_rows:
                task_combo, dep_type_combo, lag_spin, _ = dialog.predecessor_rows[0]
                # Find and select the current task
                for i in range(task_combo.count()):
                    if task_combo.itemData(i) == selected_task.id:
                        task_combo.setCurrentIndex(i)
                        break
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            new_task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                task_id=None  # Will be set by insert method
            )
            
            if self.data_manager.insert_task_at_position(new_task, selected_task.id):
                self._update_all_views()
                self.status_label.setText(
                    f"✓ Task '{new_task.name}' inserted at ID {new_task.id}. "
                    f"Tasks renumbered."
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to insert task.")
    
    def _convert_to_milestone(self):
        """Convert selected task to milestone"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to convert.")
            return
        
        task_id = selected_items[0].data(1, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        
        if not task:
            return
        
        # Check if it's a summary task
        if getattr(task, 'is_summary', False):
            QMessageBox.warning(self, "Cannot Convert", 
                              "Cannot convert a summary task to a milestone.\n"
                              "Summary tasks have subtasks and must remain as summaries.")
            return
        
        # Check current state
        is_milestone = getattr(task, 'is_milestone', False)
        
        if is_milestone:
            # Convert milestone to regular task
            reply = QMessageBox.question(
                self, 
                "Convert to Task",
                f"Convert milestone '{task.name}' to a regular task?\n\n"
                "You'll need to set the end date.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                task.is_milestone = False
                # Set default end date (7 days after start)
                task.end_date = task.start_date + timedelta(days=6)
                
                self._update_all_views()
                self.status_label.setText(f"✓ Converted '{task.name}' to regular task")
        else:
            # Convert regular task to milestone
            reply = QMessageBox.question(
                self, 
                "Convert to Milestone",
                f"Convert task '{task.name}' to a milestone?\n\n"
                "The end date will be set to the start date (0 duration).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                task.is_milestone = True
                task.end_date = task.start_date
                
                self._update_all_views()
                self.status_label.setText(f"✓ Converted '{task.name}' to milestone")
                
                
class TaskDialog(QDialog):
    """Dialog for adding/editing tasks with dependency types and milestones"""
    
    def __init__(self, parent, data_manager: DataManager, task: Task = None, 
                 parent_task: Task = None, is_milestone: bool = False):
        """
        Initialize task dialog
        
        Args:
            parent: Parent widget
            data_manager: DataManager instance
            task: Task to edit (None for new task)
            parent_task: Parent task (for subtasks)
            is_milestone: True if creating a milestone
        """
        super().__init__(parent)
        self.data_manager = data_manager
        self.task = task
        self.parent_task = parent_task
        self.is_edit = task is not None
        self.task_data = None
        
        # Determine if this is a milestone
        if task:
            # When editing, check if the task is a milestone
            self.is_milestone = getattr(task, 'is_milestone', False)
        else:
            # When creating new, use the parameter
            self.is_milestone = is_milestone
        
        # Set dialog title
        title = "Edit Task" if self.is_edit else "Add Task"
        if self.is_milestone:
            title = "Edit Milestone" if self.is_edit else "Add Milestone"
        elif parent_task:
            title = f"Add Subtask to '{parent_task.name}'"
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(600)
        
        self._create_ui()
        
        if self.is_edit:
            self._populate_fields()
        elif parent_task:
            # Set default dates from parent
            self.start_date_edit.setDate(QDate(parent_task.start_date.year, 
                                               parent_task.start_date.month, 
                                               parent_task.start_date.day))
        else:
            # For new tasks, use project_start_date from settings if available, otherwise current date
            if self.data_manager.settings.project_start_date:
                default_start_date = self.data_manager.settings.project_start_date
                self.start_date_edit.setDate(QDate(default_start_date.year,
                                                   default_start_date.month,
                                                   default_start_date.day))
            else:
                self.start_date_edit.setDate(QDate.currentDate())
        
    def _create_ui(self):
        """Create the UI elements for the task dialog"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Task Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Task Name:", self.name_edit)

        # Start Date
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        
        if self.is_milestone:
            self.start_date_edit.dateChanged.connect(self._on_milestone_date_changed)
            form_layout.addRow("Date:", self.start_date_edit)
        else:
            self.start_date_edit.dateChanged.connect(self._on_date_changed)
            form_layout.addRow("Start Date:", self.start_date_edit)
        
        # End Date (hidden for milestones)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(7))
        self.end_date_edit.dateChanged.connect(self._on_date_changed)
        
        if not self.is_milestone:
            form_layout.addRow("End Date:", self.end_date_edit)
        
        # Duration (hidden for milestones)
        if not self.is_milestone:
            duration_layout = QHBoxLayout()
            self.duration_spin = QDoubleSpinBox()
            self.duration_spin.setRange(0.1, 10000)
            self.duration_spin.setDecimals(1 if self.data_manager.settings.duration_unit == DurationUnit.HOURS else 0)
            self.duration_spin.setValue(1)
            self.duration_spin.valueChanged.connect(self._on_duration_changed)
            duration_layout.addWidget(self.duration_spin)
            
            self.duration_unit_label = QLabel(self.data_manager.settings.duration_unit.value)
            duration_layout.addWidget(self.duration_unit_label)
            duration_layout.addStretch()
            
            form_layout.addRow("Duration:", duration_layout)
            
            # Update mode selection
            update_layout = QHBoxLayout()
            update_label = QLabel("When duration changes, update:")
            self.update_end_radio = QCheckBox("End Date")
            self.update_end_radio.setChecked(True)
            self.update_start_radio = QCheckBox("Start Date")
            
            self.update_end_radio.toggled.connect(lambda checked: self.update_start_radio.setChecked(not checked) if checked else None)
            self.update_start_radio.toggled.connect(lambda checked: self.update_end_radio.setChecked(not checked) if checked else None)
            
            update_layout.addWidget(self.update_end_radio)
            update_layout.addWidget(self.update_start_radio)
            update_layout.addStretch()
            
            form_layout.addRow(update_label, update_layout)
        
        # % Complete
        self.percent_spin = QSpinBox()
        self.percent_spin.setRange(0, 100)
        self.percent_spin.setSuffix("%")
        form_layout.addRow("% Complete:", self.percent_spin)
        
        # Predecessors
        form_layout.addRow(QLabel("Predecessors:"))
        
        self.predecessors_widget = QWidget()
        pred_layout = QVBoxLayout(self.predecessors_widget)
        pred_layout.setContentsMargins(0, 0, 0, 0)
        
        self.predecessor_rows = []
        
        add_pred_btn = QPushButton("+ Add Predecessor")
        add_pred_btn.clicked.connect(self._add_predecessor_row)
        pred_layout.addWidget(add_pred_btn)
        
        self.pred_container = QWidget()
        self.pred_container_layout = QVBoxLayout(self.pred_container)
        self.pred_container_layout.setContentsMargins(0, 0, 0, 0)
        pred_layout.addWidget(self.pred_container)
        
        form_layout.addRow(self.predecessors_widget)
        
        # Resources
        self.resources_table = QTableWidget()
        self.resources_table.setColumnCount(2)
        self.resources_table.setHorizontalHeaderLabels(["Resource", "Allocation (%)"])
        self.resources_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.resources_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.resources_table.setMaximumHeight(150)
        form_layout.addRow("Assigned Resources:", self.resources_table)

        add_resource_btn = QPushButton("+ Add Resource Assignment")
        add_resource_btn.clicked.connect(self._add_resource_row)
        form_layout.addRow(add_resource_btn)

        remove_resource_btn = QPushButton("- Remove Selected Resource")
        remove_resource_btn.clicked.connect(self._remove_selected_resource_row)
        form_layout.addRow(remove_resource_btn)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: blue; padding: 5px;")
        layout.addWidget(self.info_label)
        
        # Show info for summary tasks
        if self.task and getattr(self.task, 'is_summary', False):
            self.info_label.setText("ℹ️ This is a summary task. Dates are auto-calculated from subtasks.")
            self.start_date_edit.setEnabled(False)
            self.end_date_edit.setEnabled(False)
            if hasattr(self, 'duration_spin'):
                self.duration_spin.setEnabled(False)
    
    def _add_resource_row(self, resource_name="", allocation=100):
        """Add a resource assignment row to the table"""
        row_position = self.resources_table.rowCount()
        self.resources_table.insertRow(row_position)

        # Resource ComboBox
        resource_combo = QComboBox()
        resource_names = [r.name for r in self.data_manager.get_all_resources()]
        resource_combo.addItems(resource_names)
        if resource_name in resource_names:
            resource_combo.setCurrentText(resource_name)
        self.resources_table.setCellWidget(row_position, 0, resource_combo)

        # Allocation SpinBox
        alloc_spin = QSpinBox()
        alloc_spin.setRange(0, 1000) # No upper limit
        alloc_spin.setSuffix(" %")
        alloc_spin.setValue(allocation)
        self.resources_table.setCellWidget(row_position, 1, alloc_spin)

    def _remove_selected_resource_row(self):
        """Remove the selected resource assignment row from the table"""
        selected_rows = self.resources_table.selectionModel().selectedRows()
        if selected_rows:
            # QModelIndex objects are sorted, so delete from last to first
            for index in sorted(selected_rows, key=lambda i: i.row(), reverse=True):
                self.resources_table.removeRow(index.row())
        else:
            QMessageBox.information(self, "No Selection", "Please select a resource assignment to remove.")

    def _on_milestone_date_changed(self):
        """Handle milestone date change - sync end date to start date"""
        if self.is_milestone:
            self.end_date_edit.setDate(self.start_date_edit.date())
    
    def _on_date_changed(self):
        """Handle date change - update duration"""
        if not hasattr(self, 'duration_spin'):
            return
        
        start = self.start_date_edit.date()
        end = self.end_date_edit.date()
        
        start_dt = datetime(start.year(), start.month(), start.day())
        end_dt = datetime(end.year(), end.month(), end.day())
        
        # Calculate duration in selected unit
        if self.data_manager.settings.duration_unit == DurationUnit.DAYS:
            if self.data_manager.calendar_manager:
                duration = self.data_manager.calendar_manager.calculate_working_days(start_dt, end_dt)
            else:
                duration = (end_dt - start_dt).days + 1
        else:
            if self.data_manager.calendar_manager:
                duration = self.data_manager.calendar_manager.calculate_working_hours(start_dt, end_dt)
            else:
                duration = ((end_dt - start_dt).days + 1) * 8.0
        
        # Block signals to avoid recursion
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(duration)
        self.duration_spin.blockSignals(False)
    
    def _on_duration_changed(self):
        """Handle duration change - update start or end date"""
        if not hasattr(self, 'start_date_edit'):
            return
        
        duration = self.duration_spin.value()
        
        if self.update_end_radio.isChecked():
            # Update end date based on start date and duration
            start = self.start_date_edit.date()
            start_dt = datetime(start.year(), start.month(), start.day())
            
            if self.data_manager.settings.duration_unit == DurationUnit.DAYS:
                if self.data_manager.calendar_manager:
                    end_dt = self.data_manager.calendar_manager.add_working_days(start_dt, int(duration) - 1)
                else:
                    end_dt = start_dt + timedelta(days=int(duration) - 1)
            else:
                if self.data_manager.calendar_manager:
                    days = duration / self.data_manager.calendar_manager.hours_per_day
                    end_dt = self.data_manager.calendar_manager.add_working_days(start_dt, int(days))
                else:
                    end_dt = start_dt + timedelta(days=int(duration / 8.0))
            
            self.end_date_edit.blockSignals(True)
            self.end_date_edit.setDate(QDate(end_dt.year, end_dt.month, end_dt.day))
            self.end_date_edit.blockSignals(False)
        else:
            # Update start date based on end date and duration
            end = self.end_date_edit.date()
            end_dt = datetime(end.year(), end.month(), end.day())
            
            if self.data_manager.settings.duration_unit == DurationUnit.DAYS:
                if self.data_manager.calendar_manager:
                    # Calculate backwards
                    start_dt = end_dt
                    for _ in range(int(duration) - 1):
                        start_dt -= timedelta(days=1)
                        while not self.data_manager.calendar_manager.is_working_day(start_dt):
                            start_dt -= timedelta(days=1)
                else:
                    start_dt = end_dt - timedelta(days=int(duration) - 1)
            else:
                if self.data_manager.calendar_manager:
                    days = duration / self.data_manager.calendar_manager.hours_per_day
                    start_dt = end_dt
                    for _ in range(int(days)):
                        start_dt -= timedelta(days=1)
                        while not self.data_manager.calendar_manager.is_working_day(start_dt):
                            start_dt -= timedelta(days=1)
                else:
                    start_dt = end_dt - timedelta(days=int(duration / 8.0))
            
            self.start_date_edit.blockSignals(True)
            self.start_date_edit.setDate(QDate(start_dt.year, start_dt.month, start_dt.day))
            self.start_date_edit.blockSignals(False)
    
    def _add_predecessor_row(self):
        """Add a predecessor selection row"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Task selection
        task_combo = QComboBox()
        available_tasks = sorted([t for t in self.data_manager.get_all_tasks() 
                                 if (not self.is_edit or t.id != self.task.id)], 
                                 key=lambda t: t.id)
        
        for task in available_tasks:
            indent = ""
            task_combo.addItem(f"{indent}{task.id}: {task.name}", task.id)
        
        row_layout.addWidget(task_combo, 3)
        
        # Dependency type selection
        dep_type_combo = QComboBox()
        for dep_type in DependencyType:
            dep_type_combo.addItem(f"{dep_type.name}", dep_type.name)
        
        row_layout.addWidget(dep_type_combo, 2)

        # Lag/Lead time
        lag_spin = QSpinBox()
        lag_spin.setRange(-365, 365)
        lag_spin.setSuffix(" d")
        row_layout.addWidget(lag_spin)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self._remove_predecessor_row(row_widget))
        row_layout.addWidget(remove_btn, 1)
        
        self.pred_container_layout.addWidget(row_widget)
        self.predecessor_rows.append((task_combo, dep_type_combo, lag_spin, row_widget))
    
    def _remove_predecessor_row(self, row_widget: QWidget):
        """Remove a predecessor row"""
        self.predecessor_rows = [r for r in self.predecessor_rows if r[3] != row_widget]
        row_widget.deleteLater()
    
    def _populate_fields(self):
        """Populate fields when editing"""
        self.name_edit.setText(self.task.name)
        self.start_date_edit.setDate(QDate(self.task.start_date.year, 
                                           self.task.start_date.month, 
                                           self.task.start_date.day))
        self.end_date_edit.setDate(QDate(self.task.end_date.year, 
                                         self.task.end_date.month, 
                                         self.task.end_date.day))
        self.percent_spin.setValue(self.task.percent_complete)
        self.notes_edit.setText(self.task.notes)
        
        # Populate predecessors
        for pred_id, dep_type, lag_days in self.task.predecessors:
            self._add_predecessor_row()
            task_combo, dep_type_combo, lag_spin, _ = self.predecessor_rows[-1]
            
            # Find and select the task
            for i in range(task_combo.count()):
                if task_combo.itemData(i) == pred_id:
                    task_combo.setCurrentIndex(i)
                    break
            
            # Select dependency type
            for i in range(dep_type_combo.count()):
                if dep_type_combo.itemData(i) == dep_type:
                    dep_type_combo.setCurrentIndex(i)
                    break
            
            lag_spin.setValue(lag_days)
        
        # Populate assigned resources
        for resource_name, allocation in self.task.assigned_resources:
            self._add_resource_row(resource_name, allocation)
    
    def accept(self):
        """Store data and accept the dialog"""
        self._store_task_data()
        super().accept()

    def _store_task_data(self):
        """Store task data from form into an instance variable"""
        # Get predecessors
        predecessors = []
        for task_combo, dep_type_combo, lag_spin, _ in self.predecessor_rows:
            task_id = task_combo.currentData()
            dep_type = dep_type_combo.currentData()
            lag_days = lag_spin.value()
            if task_id is not None:
                predecessors.append((task_id, dep_type, lag_days))
        
        # Get resources
        resources = []
        for row in range(self.resources_table.rowCount()):
            resource_combo = self.resources_table.cellWidget(row, 0)
            alloc_spin = self.resources_table.cellWidget(row, 1)
            if resource_combo and alloc_spin:
                resources.append((resource_combo.currentText(), alloc_spin.value()))
        
        # Get dates
        start_date = self.start_date_edit.date()
        
        # For milestones, end date = start date
        if self.is_milestone:
            end_date = start_date
        else:
            end_date = self.end_date_edit.date()
        
        self.task_data = {
            'name': self.name_edit.text(),
            'start_date': datetime(start_date.year(), start_date.month(), start_date.day()),
            'end_date': datetime(end_date.year(), end_date.month(), end_date.day()),
            'percent_complete': self.percent_spin.value(),
            'predecessors': predecessors,
            'assigned_resources': resources,
            'notes': self.notes_edit.toPlainText()
        }

    def get_task_data(self):
        """Get task data from the stored attribute"""
        return self.task_data


class ResourceDialog(QDialog):
    """Dialog for adding/editing resources"""
    
    def __init__(self, parent, resource: Resource = None):
        super().__init__(parent)
        self.resource = resource
        self.is_edit = resource is not None
        
        self.setWindowTitle("Edit Resource" if self.is_edit else "Add Resource")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._create_ui()
        
        if self.is_edit:
            self._populate_fields()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Resource Name:", self.name_edit)
        
        # Max Hours per Day
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0, 24)
        self.hours_spin.setValue(8.0)
        self.hours_spin.setSuffix(" hours")
        form_layout.addRow("Max Hours/Day:", self.hours_spin)

        # Billing Rate
        self.billing_rate_spin = QDoubleSpinBox()
        self.billing_rate_spin.setRange(0.0, 10000.0) # Assuming a reasonable range for billing rates
        self.billing_rate_spin.setValue(0.0)
        self.billing_rate_spin.setPrefix("$")
        self.billing_rate_spin.setSuffix("/hr")
        self.billing_rate_spin.setDecimals(2)
        form_layout.addRow("Billing Rate:", self.billing_rate_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields when editing"""
        self.name_edit.setText(self.resource.name)
        self.hours_spin.setValue(self.resource.max_hours_per_day)
        self.billing_rate_spin.setValue(self.resource.billing_rate)
    
    def get_resource_data(self):
        """Get resource data from form"""
        return {
            'name': self.name_edit.text(),
            'max_hours_per_day': self.hours_spin.value(),
            'exceptions': [], # Exceptions are not handled in this dialog currently
            'billing_rate': self.billing_rate_spin.value()
        }


class CalendarSettingsDialog(QDialog):
    """Dialog for calendar settings"""
    
    def __init__(self, parent, calendar_manager: CalendarManager):
        super().__init__(parent)
        self.calendar_manager = calendar_manager
        
        self.setWindowTitle("Calendar Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        # Hours per day
        hours_layout = QHBoxLayout()
        hours_layout.addWidget(QLabel("Working Hours per Day:"))
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(1, 24)
        self.hours_spin.setValue(self.calendar_manager.hours_per_day)
        self.hours_spin.setSuffix(" hours")
        hours_layout.addWidget(self.hours_spin)
        hours_layout.addStretch()
        layout.addLayout(hours_layout)
        
        # Working days
        layout.addWidget(QLabel("Working Days:"))
        
        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(i in self.calendar_manager.working_days)
            self.day_checkboxes[i] = checkbox
            layout.addWidget(checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._save_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _save_settings(self):
        """Save calendar settings"""
        self.calendar_manager.set_hours_per_day(self.hours_spin.value())
        
        working_days = [day for day, checkbox in self.day_checkboxes.items() 
                       if checkbox.isChecked()]
        self.calendar_manager.set_working_days(working_days)
        
        self.accept()

        
class DurationUnitDialog(QDialog):
    """Dialog for selecting duration unit"""
    
    def __init__(self, parent, settings: ProjectSettings):
        super().__init__(parent)
        self.settings = settings
        
        self.setWindowTitle("Duration Unit Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel(
            "Select the unit for task duration calculations.\n\n"
            "• Days: Duration calculated in working days\n"
            "• Hours: Duration calculated in working hours\n\n"
            "Changing this setting will update how durations are\n"
            "displayed and calculated throughout the project."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Radio buttons
        group_box = QGroupBox("Duration Unit")
        group_layout = QVBoxLayout(group_box)
        
        self.days_radio = QCheckBox("Days (working days)")
        self.days_radio.setChecked(self.settings.duration_unit == DurationUnit.DAYS)
        group_layout.addWidget(self.days_radio)
        
        self.hours_radio = QCheckBox("Hours (working hours)")
        self.hours_radio.setChecked(self.settings.duration_unit == DurationUnit.HOURS)
        group_layout.addWidget(self.hours_radio)
        
        # Make them mutually exclusive
        self.days_radio.toggled.connect(lambda checked: self.hours_radio.setChecked(not checked) if checked else None)
        self.hours_radio.toggled.connect(lambda checked: self.days_radio.setChecked(not checked) if checked else None)
        
        layout.addWidget(group_box)
        
        # Example
        example_label = QLabel(
            "<b>Example:</b><br>"
            "Task from Monday to Friday (5 calendar days):<br>"
            "• In Days: Duration = 5 days<br>"
            "• In Hours: Duration = 40 hours (5 days × 8 hours/day)"
        )
        example_label.setWordWrap(True)
        layout.addWidget(example_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_selected_unit(self) -> DurationUnit:
        """Get selected duration unit"""
        if self.hours_radio.isChecked():
            return DurationUnit.HOURS
        else:
            return DurationUnit.DAYS

            
class ExpandCollapseDelegate(QStyledItemDelegate):
    """Custom delegate to show expand/collapse buttons"""
    
    def __init__(self, tree_widget):
        super().__init__()
        self.tree_widget = tree_widget
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Paint expand/collapse icon"""
        super().paint(painter, option, index)
        
        # Get the tree widget item
        item = self.tree_widget.itemFromIndex(index)
        
        # Only draw icon if item has children
        if item and item.childCount() > 0:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw expand/collapse icon
            rect = option.rect
            icon_size = 14
            x = rect.x() + (rect.width() - icon_size) // 2
            y = rect.y() + (rect.height() - icon_size) // 2
            
            # Determine if expanded
            is_expanded = item.isExpanded()
            
            # Draw circular button
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(180, 180, 180, 150)))
            painter.drawEllipse(x, y, icon_size, icon_size)
            
            # Draw border
            painter.setPen(QColor(100, 100, 100))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(x, y, icon_size, icon_size)
            
            # Draw +/- symbol
            painter.setPen(QColor(50, 50, 50))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            symbol = "−" if is_expanded else "+"
            painter.drawText(x, y, icon_size, icon_size, 
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