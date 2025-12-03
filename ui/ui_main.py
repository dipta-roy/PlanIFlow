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
from PyQt6.QtCore import Qt, QDate, QTimer, QModelIndex, QEvent, QAbstractItemModel, QSize
from PyQt6.QtGui import QAction, QIcon, QColor, QBrush, QPainter, QFont, QPixmap
from datetime import datetime, timedelta
import os
import sys
import json
import logging
import re
from data_manager.manager import DataManager
from data_manager.models import Task, Resource, DependencyType, TaskStatus, ScheduleType
from calendar_manager.calendar_manager import CalendarManager
from ui.gantt_chart import GanttChart
from exporter.exporter import Exporter
from ui.themes import ThemeManager
from settings_manager.settings_manager import ProjectSettings, DurationUnit, DateFormat
from ui.ui_project_settings import ProjectSettingsDialog, DateFormatDialog
from ui.ui_delegates import SortableTreeWidgetItem, ColorDelegate, DateDelegate, ResourceDelegate
from ui.ui_helpers import get_resource_path, set_application_icon
from ui.ui_menu_toolbar import create_menu_bar, create_toolbar
from ui.ui_dashboard import update_dashboard, create_dashboard
from ui.ui_resources import ResourceSheet
from exporter.pdf_exporter import PDFExporter
from ui.ui_task_dialog import TaskDialog
from ui.ui_resource_dialog import ResourceDialog
from ui.ui_calendar_settings_dialog import CalendarSettingsDialog
from ui.ui_duration_unit_dialog import DurationUnitDialog
from ui.ui_tasks import create_task_tree

# Mixins
from ui.ui_file_manager import FileOperationsMixin
from ui.ui_task_manager import TaskOperationsMixin
from ui.ui_view_manager import GeneralViewOperationsMixin
from ui.ui_tree_view_manager import TreeViewOperationsMixin

# Constants for ColorDelegate
from constants.constants import CIRCLE_SIZE, LEFT_PADDING, TEXT_SHIFT, STATUS_ALL, STATUS_OVERDUE, STATUS_IN_PROGRESS, STATUS_UPCOMING, STATUS_COMPLETED, APP_NAME

class MainWindow(QMainWindow, FileOperationsMixin, TaskOperationsMixin, GeneralViewOperationsMixin, TreeViewOperationsMixin):
    """Main application window with enhanced features"""
    
    def __init__(self):
        super().__init__()
        
        set_application_icon(self)
        
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
    

            
    def _update_window_title(self):
        """Update window title with project name"""
        self.setWindowTitle(f"{APP_NAME} - {self.data_manager.project_name}")
    
    def _create_central_widget(self):
        """Create central widget with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Search/Filter bar
        filter_layout = QHBoxLayout()
        
        # Quick Add Task field
        filter_layout.addWidget(QLabel("Quick Add Task:"))
        self.quick_add_task_input = QLineEdit()
        self.quick_add_task_input.setPlaceholderText("Enter task name and press Enter...")
        self.quick_add_task_input.setMaximumWidth(250)
        self.quick_add_task_input.returnPressed.connect(self._quick_add_task)
        filter_layout.addWidget(self.quick_add_task_input)
        
        # Add a vertical separator
        separator = QWidget()
        self.quick_add_task_input.setFixedWidth(250)
        separator.setFixedWidth(2)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setFixedHeight(30)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(separator)
        filter_layout.addSpacing(20)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search tasks by name...")
        self.search_box.setMaximumWidth(250)
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
        self.task_tree = create_task_tree(self)
        return self.task_tree

    def _create_resource_summary(self):
        self.resource_summary = ResourceSheet(self, self.data_manager)
        return self.resource_summary

    def _create_dashboard(self):
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