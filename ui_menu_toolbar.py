"""ui_menu_toolbar.py - functions to build menu bar and toolbar for MainWindow"""


from PyQt6.QtWidgets import QLabel, QToolBar, QMenu, QStatusBar, QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction, QPixmap
from ui_delegates import get_resource_path
import os
from PyQt6.QtCore import Qt, QSize

LOGO_PATH = 'images/logo.ico'

def create_menu_bar(window):
    """Create menu bar"""
def create_menu_bar(window):
    """Create menu bar"""
    menubar = window.menuBar()

    # File Menu
    file_menu = menubar.addMenu("&File")
    new_action = QAction("&New Project", window)
    new_action.setShortcut("Ctrl+N")
    new_action.triggered.connect(window._new_project)
    file_menu.addAction(new_action)
    file_menu.addSeparator()
    open_action = QAction("&Open Project...", window)
    open_action.setShortcut("Ctrl+O")
    open_action.triggered.connect(window._open_project)
    file_menu.addAction(open_action)

    save_action = QAction("&Save Project", window)
    save_action.setShortcut("Ctrl+S")
    save_action.triggered.connect(window._save_project)
    file_menu.addAction(save_action)

    save_as_action = QAction("Save Project &As...", window)
    save_as_action.setShortcut("Ctrl+Shift+S")
    save_as_action.triggered.connect(window._save_project_as)
    file_menu.addAction(save_as_action)

    close_action = QAction("&Close Project", window)
    close_action.setShortcut("Ctrl+W")
    close_action.triggered.connect(window._close_project)
    file_menu.addAction(close_action)

    file_menu.addSeparator()

    import_excel_action = QAction("Import from &Excel...", window)
    import_excel_action.triggered.connect(window._import_excel)
    file_menu.addAction(import_excel_action)

    export_excel_action = QAction("Export to E&xcel...", window)
    export_excel_action.triggered.connect(window._export_excel)
    file_menu.addAction(export_excel_action)

    export_pdf_action = QAction("Export to &PDF...", window)
    export_pdf_action.triggered.connect(window._export_pdf)
    file_menu.addAction(export_pdf_action)

    file_menu.addSeparator()

    exit_action = QAction("E&xit", window)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)


    edit_menu = menubar.addMenu("&Edit")
    # Add Task
    add_task_action = QAction("Add &Task", window)
    add_task_action.setShortcut("Ctrl+T")
    add_task_action.triggered.connect(window._add_task_dialog)
    edit_menu.addAction(add_task_action)

    add_milestone_action = QAction("Add &Milestone", window)
    add_milestone_action.setShortcut("Ctrl+M")
    add_milestone_action.triggered.connect(window._add_milestone_dialog)
    edit_menu.addAction(add_milestone_action)

    # Add Subtask
    add_subtask_action = QAction("Add &Subtask", window)
    add_subtask_action.setShortcut("Ctrl+Shift+T")
    add_subtask_action.triggered.connect(window._add_subtask_dialog)
    edit_menu.addAction(add_subtask_action)

    indent_action = QAction("&Indent Task", window)
    indent_action.setShortcut("Tab")
    indent_action.triggered.connect(window._indent_task)
    edit_menu.addAction(indent_action)

    outdent_action = QAction("&Outdent Task", window)
    outdent_action.setShortcut("Shift+Tab")
    outdent_action.triggered.connect(window._outdent_task)
    edit_menu.addAction(outdent_action)

    edit_menu.addSeparator()

    insert_above_action = QAction("Insert Task &Above", window)
    insert_above_action.setShortcut("Ctrl+Shift+A")
    insert_above_action.triggered.connect(window._insert_task_above)
    edit_menu.addAction(insert_above_action)

    insert_below_action = QAction("Insert Task &Below", window)
    insert_below_action.setShortcut("Ctrl+Shift+B")
    insert_below_action.triggered.connect(window._insert_task_below)
    edit_menu.addAction(insert_below_action)

    edit_menu.addSeparator()

    convert_action = QAction("&Convert Task/Milestone", window)
    convert_action.setShortcut("Ctrl+Shift+M")
    convert_action.triggered.connect(window._convert_to_milestone)
    edit_menu.addAction(convert_action)

    # View Menu
    view_menu = menubar.addMenu("&View")

    refresh_action = QAction("&Refresh All", window)
    refresh_action.setShortcut("F5")
    refresh_action.triggered.connect(window._update_all_views)
    view_menu.addAction(refresh_action)

    view_menu.addSeparator()

    window.auto_refresh_action = QAction("&Auto-Refresh", window)
    window.auto_refresh_action.setCheckable(True)
    window.auto_refresh_action.setChecked(True)  # Default ON
    window.auto_refresh_action.triggered.connect(window._toggle_auto_refresh)
    view_menu.addAction(window.auto_refresh_action)

    view_menu.addSeparator()

    expand_all_action = QAction("&Expand All Tasks", window)
    expand_all_action.triggered.connect(window._expand_all_tasks)
    view_menu.addAction(expand_all_action)

    collapse_all_action = QAction("&Collapse All Tasks", window)
    collapse_all_action.triggered.connect(window._collapse_all_tasks)
    view_menu.addAction(collapse_all_action)

    view_menu.addSeparator()

    dark_mode_action = QAction("&Dark Mode", window)
    dark_mode_action.setCheckable(True)
    dark_mode_action.triggered.connect(window._toggle_dark_mode)
    view_menu.addAction(dark_mode_action)

    view_menu.addSeparator()

    window.toggle_wbs_action = QAction("&Show WBS Column", window)
    window.toggle_wbs_action.setCheckable(True)
    window.toggle_wbs_action.setChecked(True) # Default to visible
    window.toggle_wbs_action.triggered.connect(window._toggle_wbs_column_visibility)
    view_menu.addAction(window.toggle_wbs_action)

    view_menu.addSeparator()

    sort_menu = view_menu.addMenu("&Sort By")

    sort_id_action = QAction("Task &ID", window)
    sort_id_action.triggered.connect(lambda: window._sort_by_column(1))
    sort_menu.addAction(sort_id_action)

    sort_name_action = QAction("Task &Name", window)
    sort_name_action.triggered.connect(lambda: window._sort_by_column(2))
    sort_menu.addAction(sort_name_action)

    sort_start_action = QAction("&Start Date", window)
    sort_start_action.triggered.connect(lambda: window._sort_by_column(3))
    sort_menu.addAction(sort_start_action)

    sort_end_action = QAction("&End Date", window)
    sort_end_action.triggered.connect(lambda: window._sort_by_column(4))
    sort_menu.addAction(sort_end_action)

    sort_duration_action = QAction("&Duration", window)
    sort_duration_action.triggered.connect(lambda: window._sort_by_column(5))
    sort_menu.addAction(sort_duration_action)

    sort_complete_action = QAction("% &Complete", window)
    sort_complete_action.triggered.connect(lambda: window._sort_by_column(6))
    sort_menu.addAction(sort_complete_action)

    view_menu.addSeparator()

    gantt_axis_menu = view_menu.addMenu("Gantt Chart Axis View")

    hours_action = QAction("Hours", window)
    hours_action.triggered.connect(lambda: window._set_gantt_axis_scale("Hours"))
    gantt_axis_menu.addAction(hours_action)

    days_action = QAction("Days", window)
    days_action.triggered.connect(lambda: window._set_gantt_axis_scale("Days"))
    gantt_axis_menu.addAction(days_action)

    week_action = QAction("Week", window)
    week_action.triggered.connect(lambda: window._set_gantt_axis_scale("Week"))
    gantt_axis_menu.addAction(week_action)

    month_action = QAction("Month", window)
    month_action.triggered.connect(lambda: window._set_gantt_axis_scale("Month"))
    gantt_axis_menu.addAction(month_action)

    year_action = QAction("Year", window)
    year_action.triggered.connect(lambda: window._set_gantt_axis_scale("Year"))
    gantt_axis_menu.addAction(year_action)

    # Settings Menu
    settings_menu = menubar.addMenu("&Settings")



    calendar_action = QAction("&Calendar Settings...", window)
    calendar_action.triggered.connect(window._show_calendar_settings)
    settings_menu.addAction(calendar_action)

    date_format_action = QAction("&Date Format...", window)
    date_format_action.triggered.connect(window._show_date_format_settings)
    settings_menu.addAction(date_format_action)

    view_menu.addSeparator()

    # Help Menu
    help_menu = menubar.addMenu("&Help")

    legend_action = QAction("Status &Legend", window)
    legend_action.triggered.connect(window._show_status_legend)
    help_menu.addAction(legend_action)

    about_action = QAction("&About", window)
    about_action.triggered.connect(window._show_about)
    help_menu.addAction(about_action)


def create_toolbar(window):
    """Create toolbar"""
def create_toolbar(window):
    """Create toolbar"""
    toolbar = QToolBar("Main Toolbar")
    toolbar.setMovable(False)
    window.addToolBar(toolbar)
    toolbar.setIconSize(QSize(32, 32))
    toolbar.setStyleSheet("QToolButton { padding: 5px; }")

    logo_path = get_resource_path(LOGO_PATH)
    if os.path.exists(logo_path):
        logo_label = QLabel()
        logo_pixmap = QPixmap(logo_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, 
                                                 Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setStyleSheet("padding: 5px;")
        toolbar.addWidget(logo_label)
        
        # Add separator after logo
        toolbar.addSeparator()
    # Project Name Display
    toolbar.addWidget(QLabel("Project: "))
    window.project_name_label = QLabel(window.data_manager.project_name)
    window.project_name_label.setStyleSheet("font-weight: bold; padding: 5px;")
    toolbar.addWidget(window.project_name_label)

    # Project Management
    project_settings_btn = QAction("⚙️", window)
    project_settings_btn.setToolTip("Project Settings")
    project_settings_btn.triggered.connect(window._show_project_settings_dialog)
    toolbar.addAction(project_settings_btn)

    save_btn = QAction("💾", window)
    save_btn.setToolTip("Save Project")
    save_btn.triggered.connect(window._save_project)
    toolbar.addAction(save_btn)

    export_btn = QAction("📊", window)
    export_btn.setToolTip("Export to Excel")
    export_btn.triggered.connect(window._export_excel)
    toolbar.addAction(export_btn)

    export_pdf_btn = QAction("📄", window)
    export_pdf_btn.setToolTip("Export to PDF")
    export_pdf_btn.triggered.connect(window._export_pdf)
    toolbar.addAction(export_pdf_btn)

    toolbar.addSeparator()

    # Task Management
    add_task_btn = QAction("➕", window)
    add_task_btn.setToolTip("Add Task")
    add_task_btn.triggered.connect(window._add_task_dialog)
    toolbar.addAction(add_task_btn)

    add_subtask_btn = QAction("⨁", window)
    add_subtask_btn.setToolTip("Add Subtask")
    add_subtask_btn.triggered.connect(window._add_subtask_dialog)
    toolbar.addAction(add_subtask_btn)

    add_milestone_btn = QAction("◆", window)
    add_milestone_btn.setToolTip("Add Milestone (0 duration task)")
    add_milestone_btn.triggered.connect(window._add_milestone_dialog)
    toolbar.addAction(add_milestone_btn)

    edit_task_btn = QAction("✏️", window)
    edit_task_btn.setToolTip("Edit Task")
    edit_task_btn.triggered.connect(window._edit_task_dialog)
    toolbar.addAction(edit_task_btn)

    delete_task_btn = QAction("🗑️", window)
    delete_task_btn.setToolTip("Delete Task")
    delete_task_btn.triggered.connect(window._delete_task)
    toolbar.addAction(delete_task_btn)

    insert_task_btn = QAction("⬇", window)
    insert_task_btn.setToolTip("Insert Task Below Selected")
    insert_task_btn.triggered.connect(window._insert_task_below)
    toolbar.addAction(insert_task_btn)

    toolbar.addSeparator()

    # Hierarchy Management
    indent_btn = QAction("→", window)
    indent_btn.setToolTip("Indent Task")
    indent_btn.triggered.connect(window._indent_task)
    toolbar.addAction(indent_btn)

    outdent_btn = QAction("←", window)
    outdent_btn.setToolTip("Outdent Task")
    outdent_btn.triggered.connect(window._outdent_task)
    toolbar.addAction(outdent_btn)

    bulk_indent_btn = QAction("⇥", window)
    bulk_indent_btn.setToolTip("Bulk Indent Selected Tasks")
    bulk_indent_btn.triggered.connect(window._bulk_indent_tasks)
    toolbar.addAction(bulk_indent_btn)

    bulk_outdent_btn = QAction("⇤", window)
    bulk_outdent_btn.setToolTip("Bulk Outdent Selected Tasks")
    bulk_outdent_btn.triggered.connect(window._bulk_outdent_tasks)
    toolbar.addAction(bulk_outdent_btn)

    toolbar.addSeparator()

    # Resource Management
    add_resource_btn = QAction("👤", window)
    add_resource_btn.setToolTip("Add Resource")
    add_resource_btn.triggered.connect(window._add_resource_dialog)
    toolbar.addAction(add_resource_btn)


