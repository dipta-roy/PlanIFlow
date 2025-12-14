"""
Main UI - PyQt6 Application Interface
Enhanced with hierarchical tasks, dependency types, and status indicators
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTabWidget, QLabel, QLineEdit, QCheckBox, 
                             QComboBox, QScrollArea, QStatusBar)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtCore import Qt, QTimer, QEvent
from data_manager.manager import DataManager
from calendar_manager.calendar_manager import CalendarManager
from command_manager.command_manager import CommandManager # Import CommandManager
from ui.gantt_chart import GanttChart
from ui.themes import ThemeManager
from ui.ui_helpers import set_application_icon
from ui.ui_menu_toolbar import create_menu_bar, create_toolbar
from ui.ui_dashboard import create_dashboard
from ui.ui_resources import ResourceSheet
from ui.ui_tasks import create_task_tree
from ui.ui_baseline_comparison import BaselineComparisonTab
from ui.ui_monte_carlo import MonteCarloTab

# Mixins
from ui.ui_file_manager import FileOperationsMixin
from ui.ui_task_manager import TaskOperationsMixin
from ui.ui_view_manager import GeneralViewOperationsMixin
from ui.ui_tree_view_manager import TreeViewOperationsMixin
from ui.ui_formatting import FormattingMixin
from ui.ui_baseline_manager import BaselineOperationsMixin

# Constants for ColorDelegate
from constants.constants import STATUS_ALL, STATUS_OVERDUE, STATUS_IN_PROGRESS, STATUS_UPCOMING, STATUS_COMPLETED, APP_NAME

class MainWindow(QMainWindow, FileOperationsMixin, TaskOperationsMixin, GeneralViewOperationsMixin, TreeViewOperationsMixin, FormattingMixin, BaselineOperationsMixin):
    """Main application window with enhanced features"""
    
    def __init__(self):
        super().__init__()
        
        set_application_icon(self)
        
        # Initialize managers
        self.calendar_manager = CalendarManager()
        self.data_manager = DataManager(self.calendar_manager)
        self.command_manager = CommandManager() # Initialize CommandManager
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
        self._setup_shortcuts() # Setup keyboard shortcuts
        
        # Apply initial theme
        ThemeManager.apply_light_mode()
        self._apply_stylesheet()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(10000)  
       
        # Try to load last project
        self._try_load_last_project()
    

            

    
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
        self.dashboard_tab = create_dashboard(self)
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")

        # Baseline Comparison Tab
        self.baseline_comparison = BaselineComparisonTab(self.data_manager, self)
        self.tabs.addTab(self.baseline_comparison, "📐 Baseline Comparison")

        # Monte Carlo Tab
        self.monte_carlo_tab = MonteCarloTab(self.data_manager)
        self.tabs.addTab(self.monte_carlo_tab, "🎲 Risk Analysis")
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
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
    
    def _create_baseline_comparison(self):
        self.baseline_comparison = BaselineComparisonTab(self.data_manager, self)
        return self.baseline_comparison

    def _create_monte_carlo_tab(self):
        self.monte_carlo_tab = MonteCarloTab(self.data_manager)
        return self.monte_carlo_tab

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Zoom Controls
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(5)
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedWidth(30)
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        # Override padding from global theme because 15px side padding hides text on small buttons
        self.zoom_out_btn.setStyleSheet("padding: 0px; font-weight: bold;")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(40)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedWidth(30)
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_btn.setStyleSheet("padding: 0px; font-weight: bold;")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.status_bar.addPermanentWidget(zoom_widget)
        
        self.save_time_label = QLabel("")
        self.save_time_label.setContentsMargins(20, 0, 0, 0)
        self.status_bar.addPermanentWidget(self.save_time_label)

    def _zoom_in(self):
        """Zoom in (move to next font size step)"""
        current_size = getattr(self.data_manager.settings, 'app_font_size', 9)
        # Scale: 8, 9, 10, 11, 12, 14, 16, 18, 20, 24
        # Or just increment by 1
        new_size = min(current_size + 1, 24)
        if new_size != current_size:
            self.data_manager.settings.set_app_font_size(new_size)
            self._apply_stylesheet()
            self._update_zoom_label()
            self.status_label.setText(f"Zoom level set to {new_size}pt")

    def _zoom_out(self):
        """Zoom out (move to previous font size step)"""
        current_size = getattr(self.data_manager.settings, 'app_font_size', 9)
        new_size = max(current_size - 1, 8)
        if new_size != current_size:
            self.data_manager.settings.set_app_font_size(new_size)
            self._apply_stylesheet()
            self._update_zoom_label()
            self.status_label.setText(f"Zoom level set to {new_size}pt")

    def _update_zoom_label(self):
        """Update zoom label display"""
        current_size = getattr(self.data_manager.settings, 'app_font_size', 9)
        # Base size 9 is 100%? Or 10?
        # Let's say 10 is 100%. 9 is 90%.
        percentage = int((current_size / 9.0) * 100) # Using 9 as base since we just changed default to 9
        self.zoom_label.setText(f"{percentage}%")

    def _show_monte_carlo_help(self):
        """Show Monte Carlo help dialog"""
        if hasattr(self, 'monte_carlo_tab'):
            self.monte_carlo_tab.show_help()
    
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

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        self.undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        self.undo_shortcut.activated.connect(self.undo)
        
        self.redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        self.redo_shortcut.activated.connect(self.redo)
        
        # Zoom shortcuts
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self) # Ctrl+= usually works as Ctrl++ on most keyboard layouts
        self.zoom_in_shortcut.activated.connect(self._zoom_in)
        
        self.zoom_in_shortcut_2 = QShortcut(QKeySequence("Ctrl++"), self) # Numpad plus
        self.zoom_in_shortcut_2.activated.connect(self._zoom_in)

        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoom_out_shortcut.activated.connect(self._zoom_out)

    def undo(self):
        """Undo last action"""
        if self.command_manager.undo():
            self._update_all_views()
            self.status_label.setText("✓ Undo successful")
        else:
            self.status_label.setText("⚠️ Nothing to undo")

    def redo(self):
        """Redo last action"""
        if self.command_manager.redo():
            self._update_all_views()
            self.status_label.setText("✓ Redo successful")
        else:
            self.status_label.setText("⚠️ Nothing to redo")