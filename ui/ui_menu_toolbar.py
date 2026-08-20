"""ui_menu_toolbar.py - functions to build menu bar and toolbar for MainWindow"""

from PyQt6.QtGui import QAction, QPixmap
import base64
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QToolBar, QLabel
from constants.app_images import LOGO_ICO_BASE64

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

    # Bulk Add Tasks
    bulk_add_task_action = QAction("Bulk Add &Tasks...", window)
    bulk_add_task_action.setShortcut("Ctrl+Shift+D")
    bulk_add_task_action.triggered.connect(window._bulk_add_tasks_dialog)
    edit_menu.addAction(bulk_add_task_action)

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
    
    # Format Menu
    format_menu = menubar.addMenu("F&ormat")
    
    bold_action = QAction("&Bold", window)
    bold_action.setShortcut("Ctrl+B")
    bold_action.setCheckable(True)
    bold_action.triggered.connect(window._toggle_bold)
    format_menu.addAction(bold_action)
    window.bold_action = bold_action
    
    italic_action = QAction("&Italic", window)
    italic_action.setShortcut("Ctrl+I")
    italic_action.setCheckable(True)
    italic_action.triggered.connect(window._toggle_italic)
    format_menu.addAction(italic_action)
    window.italic_action = italic_action
    
    underline_action = QAction("&Underline", window)
    underline_action.setShortcut("Ctrl+U")
    underline_action.setCheckable(True)
    underline_action.triggered.connect(window._toggle_underline)
    format_menu.addAction(underline_action)
    window.underline_action = underline_action
    
    format_menu.addSeparator()
    
    font_color_action = QAction("Font &Color...", window)
    font_color_action.triggered.connect(window._change_font_color)
    format_menu.addAction(font_color_action)
    
    bg_color_action = QAction("&Background Color...", window)
    bg_color_action.triggered.connect(window._change_background_color)
    format_menu.addAction(bg_color_action)
    
    format_menu.addSeparator()
    
    font_size_menu = format_menu.addMenu("Font &Size")
    for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24]:
        size_action = QAction(f"{size} pt", window)
        size_action.triggered.connect(lambda checked, s=size: window._change_font_size(s))
        font_size_menu.addAction(size_action)
    
    font_family_menu = format_menu.addMenu("Font &Family")
    fonts = ["Arial", "Times New Roman", "Calibri", "Verdana", "Tahoma", 
             "Georgia", "Courier New", "Comic Sans MS", "Impact", "Trebuchet MS"]
    for font in fonts:
        font_action = QAction(font, window)
        font_action.triggered.connect(lambda checked, f=font: window._change_font_family(f))
        font_family_menu.addAction(font_action)
    
    format_menu.addSeparator()
    
    clear_format_action = QAction("&Clear Formatting", window)
    clear_format_action.setShortcut("Ctrl+Shift+X")
    clear_format_action.triggered.connect(window._clear_formatting)
    format_menu.addAction(clear_format_action)

    # View Menu
    view_menu = menubar.addMenu("&View")

    refresh_action = QAction("&Refresh All", window)
    refresh_action.setShortcut("F5")
    refresh_action.triggered.connect(window._update_all_views)
    view_menu.addAction(refresh_action)

    view_menu.addSeparator()

    window.auto_refresh_action = QAction("&Auto-Refresh", window)
    window.auto_refresh_action.setCheckable(True)
    window.auto_refresh_action.setChecked(True)
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
    window.toggle_wbs_action.setChecked(True)
    window.toggle_wbs_action.triggered.connect(window._toggle_wbs_column_visibility)
    view_menu.addAction(window.toggle_wbs_action)

    view_menu.addSeparator()

    sort_menu = view_menu.addMenu("&Sort By")
    window.sort_menu = sort_menu

    window.sort_wbs_action = QAction("&WBS", window)
    window.sort_wbs_action.setVisible(window.toggle_wbs_action.isChecked())
    window.sort_wbs_action.triggered.connect(lambda: window._sort_by_column(3))
    sort_menu.addAction(window.sort_wbs_action)


    sort_id_action = QAction("Task &ID", window)
    sort_id_action.triggered.connect(lambda: window._sort_by_column(2))
    sort_menu.addAction(sort_id_action)

    sort_name_action = QAction("Task &Name", window)
    sort_name_action.triggered.connect(lambda: window._sort_by_column(4))
    sort_menu.addAction(sort_name_action)

    sort_start_action = QAction("&Start Date", window)
    sort_start_action.triggered.connect(lambda: window._sort_by_column(5))
    sort_menu.addAction(sort_start_action)

    sort_end_action = QAction("&End Date", window)
    sort_end_action.triggered.connect(lambda: window._sort_by_column(6))
    sort_menu.addAction(sort_end_action)

    sort_duration_action = QAction("&Duration", window)
    sort_duration_action.triggered.connect(lambda: window._sort_by_column(7))
    sort_menu.addAction(sort_duration_action)

    sort_complete_action = QAction("% &Complete", window)
    sort_complete_action.triggered.connect(lambda: window._sort_by_column(8))
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

    project_settings_action = QAction("&Project Settings...", window)
    project_settings_action.triggered.connect(window._show_project_settings_dialog)
    settings_menu.addAction(project_settings_action)
    
    settings_menu.addSeparator()
    
    # Baseline Management
    baseline_menu = settings_menu.addMenu("&Baselines")
    
    set_baseline_action = QAction("&Set Baseline...", window)
    set_baseline_action.triggered.connect(window._manage_baselines)
    baseline_menu.addAction(set_baseline_action)
    
    view_baseline_action = QAction("&View Baseline Comparison", window)
    view_baseline_action.triggered.connect(window._show_baseline_comparison)
    baseline_menu.addAction(view_baseline_action)

    view_menu.addSeparator()

    # Help Menu
    help_menu = menubar.addMenu("&Help")

    legend_action = QAction("Quick &Reference Guide", window)
    legend_action.triggered.connect(window._show_reference_guide)
    help_menu.addAction(legend_action)

    mc_help_action = QAction("Monte Carlo &Analysis Help", window)
    mc_help_action.triggered.connect(window._show_monte_carlo_help)
    help_menu.addAction(mc_help_action)

    evm_help_action = QAction("&EVM Analysis Help", window)
    evm_help_action.triggered.connect(window._show_evm_help)
    help_menu.addAction(evm_help_action)

    about_action = QAction("&About", window)
    about_action.triggered.connect(window._show_about)
    help_menu.addAction(about_action)

    help_menu.addSeparator()

    check_update_action = QAction("Check for &Updates...", window)
    check_update_action.triggered.connect(window._check_for_updates)
    help_menu.addAction(check_update_action)


def create_toolbar(window):
    """Create toolbar"""
    from ui.toolbar_icons import (
        gear_icon, save_icon, export_excel_icon, export_pdf_icon,
        add_task_icon, bulk_add_icon, add_subtask_icon, milestone_icon,
        edit_icon, delete_icon, insert_below_icon, expand_icon,
        move_up_icon, move_down_icon,
        indent_icon, outdent_icon, bulk_indent_icon, bulk_outdent_icon,
        bold_icon, italic_icon, underline_icon, font_color_icon, bg_color_icon,
        resource_icon, evm_icon,
    )

    ICON_SIZE = 24

    toolbar = QToolBar("Main Toolbar")
    toolbar.setMovable(False)
    window.addToolBar(toolbar)
    toolbar.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
    toolbar.setStyleSheet("QToolButton { padding: 5px; }")

    # Load logo from base64
    try:
        logo_bytes = base64.b64decode(LOGO_ICO_BASE64)
        logo_pixmap = QPixmap()
        logo_pixmap.loadFromData(logo_bytes)
        
        if not logo_pixmap.isNull():
            logo_label = QLabel()
            logo_pixmap = logo_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, 
                                             Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setStyleSheet("padding: 5px;")
            toolbar.addWidget(logo_label)
            
            toolbar.addSeparator()
    except Exception as e:
        print(f"Error loading logo: {e}")
        
    # Project Name Display
    toolbar.addWidget(QLabel("Project: "))
    window.project_name_label = QLabel(window.data_manager.project_name)
    window.project_name_label.setStyleSheet("font-weight: bold; padding: 5px;")
    toolbar.addWidget(window.project_name_label)

    dark_mode = getattr(window, 'dark_mode', False)
    window._toolbar_actions = []

    def _add_action(icon_func, tooltip, slot, checkable=False):
        if dark_mode:
            icon = icon_func(ICON_SIZE, color="#FFFFFF")
        else:
            icon = icon_func(ICON_SIZE)
        act = QAction(icon, "", window)
        act.setToolTip(tooltip)
        if checkable:
            act.setCheckable(True)
        if slot:
            act.triggered.connect(slot)
        toolbar.addAction(act)
        window._toolbar_actions.append((act, icon_func))
        return act

    # Project Management
    _add_action(gear_icon, "Project Settings", window._show_project_settings_dialog)
    _add_action(save_icon, "Save Project", window._save_project)
    _add_action(export_excel_icon, "Export to Excel", window._export_excel)
    _add_action(export_pdf_icon, "Export to PDF", window._export_pdf)

    toolbar.addSeparator()

    # Task Management
    _add_action(add_task_icon, "Add Task", window._add_task_dialog)
    _add_action(bulk_add_icon, "Bulk Add Tasks (Ctrl+Shift+D)", window._bulk_add_tasks_dialog)
    _add_action(add_subtask_icon, "Add Subtask", window._add_subtask_dialog)
    _add_action(milestone_icon, "Add Milestone (0 duration task)", window._add_milestone_dialog)
    _add_action(edit_icon, "Edit Task", window._edit_task_dialog)
    _add_action(delete_icon, "Delete Task", window._delete_task)
    _add_action(insert_below_icon, "Insert Task Below Selected", window._insert_task_below)
    _add_action(expand_icon, "Expand selected summary task and all subtasks", window._expand_selected)

    toolbar.addSeparator()

    # Move Options
    _add_action(move_up_icon, "Move Task Up", window._move_task_up)
    _add_action(move_down_icon, "Move Task Down", window._move_task_down)

    toolbar.addSeparator()

    # Hierarchy Management
    _add_action(indent_icon, "Indent Task", window._indent_task)
    _add_action(outdent_icon, "Outdent Task", window._outdent_task)
    _add_action(bulk_indent_icon, "Bulk Indent Selected Tasks", window._bulk_indent_tasks)
    _add_action(bulk_outdent_icon, "Bulk Outdent Selected Tasks", window._bulk_outdent_tasks)

    toolbar.addSeparator()
    
    # Formatting Tools
    window.toolbar_bold_btn = _add_action(bold_icon, "Bold (Ctrl+B)", window._toggle_bold, checkable=True)
    window.toolbar_italic_btn = _add_action(italic_icon, "Italic (Ctrl+I)", window._toggle_italic, checkable=True)
    window.toolbar_underline_btn = _add_action(underline_icon, "Underline (Ctrl+U)", window._toggle_underline, checkable=True)
    _add_action(font_color_icon, "Font Color", window._change_font_color)
    _add_action(bg_color_icon, "Background Color", window._change_background_color)

    toolbar.addSeparator()

    # Resource Management
    _add_action(resource_icon, "Add Resource", window._add_resource_dialog)

    toolbar.addSeparator()

    # EVM Analysis
    _add_action(evm_icon, "Refresh EVM Analysis", lambda: window.tabs.setCurrentIndex(5) or window.evm_tab.refresh_data())


def update_toolbar_icons(window, dark_mode: bool):
    """Dynamically update main toolbar icon colors for high contrast across themes."""
    ICON_SIZE = 24
    if hasattr(window, '_toolbar_actions'):
        for action, icon_func in window._toolbar_actions:
            if dark_mode:
                action.setIcon(icon_func(ICON_SIZE, color="#FFFFFF"))
            else:
                action.setIcon(icon_func(ICON_SIZE))





