
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTableWidget,
    QHeaderView, QScrollArea, QTableWidgetItem, QProgressBar, QPushButton,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from settings_manager.settings_manager import DurationUnit
from data_manager.models import TaskStatus

# Matplotlib imports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np


# ---------------------------------------------------------------------------
# Theme Palette
# ---------------------------------------------------------------------------

def _get_dashboard_palette(dark_mode: bool) -> dict:
    """Return a colour palette dict for the current theme."""
    if dark_mode:
        return {
            "bg":           "#232323",
            "card_bg":      "#2d2d2d",
            "card_border":  "#3d3d3d",
            "text":         "#E0E0E0",
            "text_muted":   "#9E9E9E",
            "header_text":  "#FFFFFF",
            "accent":       "#42A5F5",
            "chart_bg":     "#2d2d2d",
            "chart_text":   "#CCCCCC",
            "chart_grid":   "#444444",
            "status_upcoming_bg":    "#37474F",
            "status_upcoming_border":"#78909C",
            "status_inprog_bg":      "#1A3A4A",
            "status_inprog_border":  "#29B6F6",
            "status_complete_bg":    "#1B3A1B",
            "status_complete_border":"#66BB6A",
            "status_overdue_bg":     "#3E2020",
            "status_overdue_border": "#EF5350",
            "table_bg":      "#2d2d2d",
            "table_alt_bg":  "#353535",
            "table_header":  "#3d3d3d",
            "table_grid":    "#555555",
        }
    else:
        return {
            "bg":           "#F5F7FA",
            "card_bg":      "#FFFFFF",
            "card_border":  "#E0E4E8",
            "text":         "#37474F",
            "text_muted":   "#78909C",
            "header_text":  "#263238",
            "accent":       "#1E88E5",
            "chart_bg":     "#FFFFFF",
            "chart_text":   "#455A64",
            "chart_grid":   "#ECEFF1",
            "status_upcoming_bg":    "#ECEFF1",
            "status_upcoming_border":"#90A4AE",
            "status_inprog_bg":      "#E3F2FD",
            "status_inprog_border":  "#42A5F5",
            "status_complete_bg":    "#E8F5E9",
            "status_complete_border":"#66BB6A",
            "status_overdue_bg":     "#FFEBEE",
            "status_overdue_border": "#EF5350",
            "table_bg":      "#FFFFFF",
            "table_alt_bg":  "#F5F5F5",
            "table_header":  "#E0E0E0",
            "table_grid":    "#D0D0D0",
        }


# ---------------------------------------------------------------------------
# Card Builders
# ---------------------------------------------------------------------------

def _create_metric_card(title: str, value_label: QLabel, accent_color: str,
                        palette: dict) -> QFrame:
    """Build a hero KPI card with a large value and small title."""
    card = QFrame()
    card.setObjectName("metricCard")
    card.setStyleSheet(f"""
        QFrame#metricCard {{
            background-color: {palette['card_bg']};
            border: 1px solid {palette['card_border']};
            border-left: 4px solid {accent_color};
            border-radius: 8px;
            padding: 2px;
        }}
    """)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    card.setMinimumHeight(85)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(4)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color: {palette['text_muted']}; font-size: 11px; font-weight: 500; border: none;")
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(title_lbl)

    value_label.setStyleSheet(f"color: {palette['header_text']}; font-size: 18px; font-weight: bold; border: none;")
    value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(value_label)

    return card


def _create_status_card(title: str, value_label: QLabel,
                        border_color: str,
                        palette: dict) -> QFrame:
    """Build a compact status tile with coloured accent top border."""
    card = QFrame()
    card.setObjectName("statusCard")
    card.setStyleSheet(f"""
        QFrame#statusCard {{
            background-color: {palette['card_bg']};
            border: 1px solid {palette['card_border']};
            border-top: 3px solid {border_color};
            border-radius: 8px;
            padding: 2px;
        }}
    """)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    card.setMinimumHeight(85)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(4)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color: {palette['text_muted']}; font-size: 11px; font-weight: 500; border: none;")
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(title_lbl)

    value_label.setStyleSheet(f"color: {palette['header_text']}; font-size: 18px; font-weight: bold; border: none;")
    value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(value_label)

    return card



def _create_chart_card(title: str, canvas: FigureCanvas, palette: dict) -> QFrame:
    """Wrap a Matplotlib canvas inside a styled card panel with a section title."""
    card = QFrame()
    card.setObjectName("chartCard")
    card.setStyleSheet(f"""
        QFrame#chartCard {{
            background-color: {palette['card_bg']};
            border: 1px solid {palette['card_border']};
            border-radius: 8px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(4)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color: {palette['text']}; font-size: 12px; font-weight: bold; border: none;")
    layout.addWidget(title_lbl)

    canvas.setStyleSheet("border: none;")
    layout.addWidget(canvas)

    return card


# ---------------------------------------------------------------------------
# Dashboard Creation
# ---------------------------------------------------------------------------

def create_dashboard(main_window):
    """Create project dashboard."""
    dark_mode = getattr(main_window, 'dark_mode', False)
    pal = _get_dashboard_palette(dark_mode)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background-color: {pal['bg']}; }}")

    widget = QWidget()
    widget.setStyleSheet(f"background-color: {pal['bg']};")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(16)

    # ── Project Header ────────────────────────────────────────────────
    header_frame = QFrame()
    header_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {pal['card_bg']};
            border: 1px solid {pal['card_border']};
            border-radius: 10px;
            padding: 12px;
        }}
    """)
    header_layout = QVBoxLayout(header_frame)
    header_layout.setContentsMargins(20, 14, 20, 14)

    main_window.dashboard_project_name = QLabel(main_window.data_manager.project_name)
    main_window.dashboard_project_name.setStyleSheet(
        f"color: {pal['header_text']}; font-size: 22px; font-weight: bold; border: none;"
    )
    main_window.dashboard_project_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
    header_layout.addWidget(main_window.dashboard_project_name)

    # Quick stats row
    stats_row = QHBoxLayout()
    stats_row.setSpacing(24)

    main_window.start_date_label = QLabel("Start: N/A")
    main_window.end_date_label = QLabel("End: N/A")
    stat_style = f"color: {pal['text_muted']}; font-size: 12px; border: none;"
    for lbl in [main_window.start_date_label, main_window.end_date_label]:
        lbl.setStyleSheet(stat_style)
        stats_row.addWidget(lbl)
    stats_row.addStretch()
    header_layout.addLayout(stats_row)

    layout.addWidget(header_frame)

    # ── KPI & Status Cards (Single Row) ─────────────────────────────
    cards_row = QHBoxLayout()
    cards_row.setSpacing(8)

    main_window.total_tasks_label = QLabel("0")
    main_window.completion_label = QLabel("0%")
    main_window.total_effort_label = QLabel("0h")
    symbol = main_window.data_manager.settings.currency.symbol
    main_window.total_cost_label = QLabel(f"{symbol}0.00")
    main_window.total_resources_label = QLabel("0")

    main_window.upcoming_tasks_label = QLabel("0 / 0")
    main_window.in_progress_tasks_label = QLabel("0 / 0")
    main_window.completed_tasks_label = QLabel("0 / 0")
    main_window.overdue_tasks_label = QLabel("0 / 0")

    kpi_cards = [
        ("Total Tasks",   main_window.total_tasks_label,     "#42A5F5"),
        ("Completion",    main_window.completion_label,       "#66BB6A"),
        ("Total Effort",  main_window.total_effort_label,    "#FFA726"),
        ("Total Cost",    main_window.total_cost_label,      "#AB47BC"),
        ("Resources",     main_window.total_resources_label, "#26C6DA"),
    ]
    for title, lbl, accent in kpi_cards:
        cards_row.addWidget(_create_metric_card(title, lbl, accent, pal))

    status_cards = [
        ("Upcoming",    main_window.upcoming_tasks_label,     pal["status_upcoming_border"]),
        ("In Progress", main_window.in_progress_tasks_label,   pal["status_inprog_border"]),
        ("Completed",   main_window.completed_tasks_label,     pal["status_complete_border"]),
        ("Overdue",     main_window.overdue_tasks_label,       pal["status_overdue_border"]),
    ]
    for title, lbl, border in status_cards:
        cards_row.addWidget(_create_status_card(title, lbl, border, pal))


    layout.addLayout(cards_row)

    # ── Smart Project Diagnosis ───────────────────────────────────────
    intel_group = QFrame()
    intel_group.setObjectName("intelCard")
    intel_group.setStyleSheet(f"""
        QFrame#intelCard {{
            background-color: {pal['card_bg']};
            border: 1px solid {pal['card_border']};
            border-radius: 8px;
        }}
    """)
    intel_layout = QVBoxLayout(intel_group)
    intel_layout.setContentsMargins(16, 14, 16, 14)

    intel_header = QHBoxLayout()

    title_label = QLabel("🧠 Smart Project Diagnosis")
    title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {pal['text']}; border: none;")

    main_window.refresh_intel_btn = QPushButton("🚀 Run Diagnosis")
    main_window.refresh_intel_btn.setFixedWidth(150)
    main_window.refresh_intel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    main_window.refresh_intel_btn.setStyleSheet("""
        QPushButton {
            background-color: #1E88E5;
            color: white;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 4px;
            border: none;
        }
        QPushButton:hover {
            background-color: #1565C0;
        }
    """)
    main_window.refresh_intel_btn.clicked.connect(main_window._run_intelligent_diagnosis)

    intel_header.addWidget(title_label)
    intel_header.addStretch()
    intel_header.addWidget(main_window.refresh_intel_btn)
    intel_layout.addLayout(intel_header)

    main_window.intel_progress = QProgressBar()
    main_window.intel_progress.setFixedHeight(2)
    main_window.intel_progress.setTextVisible(False)
    main_window.intel_progress.setStyleSheet(
        "QProgressBar { border: none; background: transparent; } "
        "QProgressBar::chunk { background-color: #1E88E5; }"
    )
    main_window.intel_progress.setVisible(False)
    intel_layout.addWidget(main_window.intel_progress)

    main_window.intel_results_label = QLabel(
        "AI-powered analysis of your schedule, cost, and risks will appear here."
    )
    main_window.intel_results_label.setWordWrap(True)
    main_window.intel_results_label.setStyleSheet(
        f"color: {pal['text_muted']}; font-style: italic; margin-top: 6px; border: none;"
    )
    intel_layout.addWidget(main_window.intel_results_label)

    layout.addWidget(intel_group)

    # ── Chart Row ─────────────────────────────────────────────────────
    charts_layout = QHBoxLayout()
    charts_layout.setSpacing(12)

    main_window.task_status_figure = Figure(figsize=(4, 3.5), dpi=100)
    main_window.task_status_figure.patch.set_facecolor(pal['chart_bg'])
    main_window.task_status_canvas = FigureCanvas(main_window.task_status_figure)
    charts_layout.addWidget(
        _create_chart_card("📊 Task Status Breakdown", main_window.task_status_canvas, pal)
    )

    main_window.resource_allocation_figure = Figure(figsize=(4, 3.5), dpi=100)
    main_window.resource_allocation_figure.patch.set_facecolor(pal['chart_bg'])
    main_window.resource_allocation_canvas = FigureCanvas(main_window.resource_allocation_figure)
    charts_layout.addWidget(
        _create_chart_card("👥 Resource Allocation", main_window.resource_allocation_canvas, pal)
    )

    main_window.cost_trend_figure = Figure(figsize=(4, 3.5), dpi=100)
    main_window.cost_trend_figure.patch.set_facecolor(pal['chart_bg'])
    main_window.cost_trend_canvas = FigureCanvas(main_window.cost_trend_figure)
    charts_layout.addWidget(
        _create_chart_card("💰 Cost Trend", main_window.cost_trend_canvas, pal)
    )

    layout.addLayout(charts_layout)

    # ── Cost Breakdown Table ──────────────────────────────────────────
    table_card = QFrame()
    table_card.setObjectName("tableCard")
    table_card.setStyleSheet(f"""
        QFrame#tableCard {{
            background-color: {pal['card_bg']};
            border: 1px solid {pal['card_border']};
            border-radius: 8px;
        }}
    """)
    table_layout = QVBoxLayout(table_card)
    table_layout.setContentsMargins(14, 12, 14, 12)

    table_title = QLabel("📋 Monthly / Daily Cost Breakdown")
    table_title.setStyleSheet(f"color: {pal['text']}; font-size: 12px; font-weight: bold; border: none;")
    table_layout.addWidget(table_title)

    main_window.cost_breakdown_table = QTableWidget()
    main_window.cost_breakdown_table.setMinimumHeight(200)
    main_window.cost_breakdown_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    main_window.cost_breakdown_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    main_window.cost_breakdown_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    main_window.cost_breakdown_table.setAlternatingRowColors(True)
    main_window.cost_breakdown_table.setStyleSheet(f"""
        QTableWidget {{
            background-color: {pal['table_bg']};
            alternate-background-color: {pal['table_alt_bg']};
            gridline-color: {pal['table_grid']};
            border: none;
            color: {pal['text']};
        }}
        QHeaderView::section {{
            background-color: {pal['table_header']};
            color: {pal['text']};
            font-weight: bold;
            padding: 5px;
            border: 1px solid {pal['table_grid']};
        }}
    """)
    main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeMode.Stretch
    )
    table_layout.addWidget(main_window.cost_breakdown_table)
    layout.addWidget(table_card)

    # Store palette reference for chart updates
    main_window._dashboard_palette = pal

    scroll_area.setWidget(widget)
    return scroll_area


# ---------------------------------------------------------------------------
# Dashboard Update
# ---------------------------------------------------------------------------

def update_dashboard(main_window):
    """Update project dashboard with current data."""
    data_manager = main_window.data_manager
    dark_mode = getattr(main_window, 'dark_mode', False)
    pal = _get_dashboard_palette(dark_mode)
    main_window._dashboard_palette = pal

    # Update project name
    main_window.dashboard_project_name.setText(data_manager.project_name)

    # Dates
    start = data_manager.get_project_start_date()
    end = data_manager.get_project_end_date()
    main_window.start_date_label.setText(
        f"📅 Start: {start.strftime('%d %b %Y') if start else 'N/A'}"
    )
    main_window.end_date_label.setText(
        f"📅 End: {end.strftime('%d %b %Y') if end else 'N/A'}"
    )

    # KPI Calculations
    total_tasks = len(data_manager.tasks)
    main_window.total_tasks_label.setText(str(total_tasks))

    completed_tasks = [t for t in data_manager.tasks if t.percent_complete == 100]
    completion_pct = (len(completed_tasks) / total_tasks * 100) if total_tasks else 0
    main_window.completion_label.setText(f"{completion_pct:.0f}%")

    main_window.total_resources_label.setText(str(len(data_manager.resources)))

    total_effort = 0
    total_project_cost = 0
    for task in data_manager.tasks:
        if not task.is_summary and not task.is_milestone:
            task_duration_hours = task.get_duration(
                data_manager.settings.duration_unit, data_manager.calendar_manager
            )
            for resource_name, allocation_percent in task.assigned_resources:
                resource = data_manager.get_resource(resource_name)
                if resource:
                    if data_manager.settings.duration_unit == DurationUnit.DAYS:
                        hours = data_manager.calendar_manager.calculate_working_hours(
                            task.start_date, task.end_date,
                            resource_exceptions=resource.exceptions
                        ) * (allocation_percent / 100.0)
                    else:
                        hours = task_duration_hours * (allocation_percent / 100.0)
                    total_effort += hours
                    total_project_cost += hours * resource.billing_rate

    symbol = data_manager.settings.currency.symbol
    main_window.total_effort_label.setText(f"{total_effort:.0f}h")
    main_window.total_cost_label.setText(f"{symbol}{total_project_cost:,.2f}")

    # Status counts
    upcoming_count = in_progress_count = completed_count = overdue_count = 0
    total_work = 0
    for task in data_manager.tasks:
        if not task.is_summary:
            total_work += 1
            status = task.get_status()
            if status == TaskStatus.UPCOMING:
                upcoming_count += 1
            elif status == TaskStatus.IN_PROGRESS:
                in_progress_count += 1
            elif status == TaskStatus.COMPLETED:
                completed_count += 1
            elif status == TaskStatus.OVERDUE:
                overdue_count += 1

    main_window.upcoming_tasks_label.setText(f"{upcoming_count} / {total_work}")
    main_window.in_progress_tasks_label.setText(f"{in_progress_count} / {total_work}")
    main_window.completed_tasks_label.setText(f"{completed_count} / {total_work}")
    main_window.overdue_tasks_label.setText(f"{overdue_count} / {total_work}")

    # Charts
    update_task_status_donut(main_window, upcoming_count, in_progress_count,
                            completed_count, overdue_count, total_work, pal)
    update_resource_allocation_chart(main_window, data_manager, pal)
    update_cost_trend_chart(main_window, data_manager, pal)

    # Cost breakdown table
    _update_cost_breakdown_table(main_window, data_manager)


# ---------------------------------------------------------------------------
# Modernised Charts
# ---------------------------------------------------------------------------

def _apply_chart_theme(ax, fig, pal):
    """Apply theme colors to axes and figure."""
    fig.patch.set_facecolor(pal['chart_bg'])
    ax.set_facecolor(pal['chart_bg'])
    ax.tick_params(colors=pal['chart_text'], labelsize=8)
    ax.xaxis.label.set_color(pal['chart_text'])
    ax.yaxis.label.set_color(pal['chart_text'])
    ax.title.set_color(pal['chart_text'])
    for spine in ax.spines.values():
        spine.set_color(pal['chart_grid'])


def update_task_status_donut(main_window, upcoming, in_progress, completed,
                             overdue, total, pal):
    """Donut chart with centre label for task status."""
    fig = main_window.task_status_figure
    fig.clear()
    ax = fig.add_subplot(111)

    labels, sizes, colors = [], [], []
    color_map = {
        'Upcoming':    '#90A4AE',
        'In Progress': '#42A5F5',
        'Completed':   '#66BB6A',
        'Overdue':     '#EF5350',
    }
    for name, count in [('Upcoming', upcoming), ('In Progress', in_progress),
                        ('Completed', completed), ('Overdue', overdue)]:
        if count > 0:
            labels.append(f"{name} ({count})")
            sizes.append(count)
            colors.append(color_map[name])

    if not sizes:
        labels, sizes, colors = ['No Tasks'], [1], ['#BDBDBD']

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.0f%%',
        startangle=140, pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor=pal['chart_bg'], linewidth=2),
        textprops={'fontsize': 8, 'color': pal['chart_text']}
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color(pal['chart_text'])

    # Centre label
    pct_text = f"{(completed / total * 100):.0f}%" if total else "0%"
    ax.text(0, 0, pct_text, ha='center', va='center',
            fontsize=18, fontweight='bold', color=pal['chart_text'])
    ax.text(0, -0.14, "done", ha='center', va='center',
            fontsize=8, color=pal['text_muted'])

    ax.set_title('Task Status', fontsize=10, color=pal['chart_text'], pad=12)
    fig.patch.set_facecolor(pal['chart_bg'])
    fig.tight_layout()
    main_window.task_status_canvas.draw()


def update_resource_allocation_chart(main_window, data_manager, pal):
    """Grouped bar chart with clean modern styling."""
    fig = main_window.resource_allocation_figure
    fig.clear()
    ax = fig.add_subplot(111)
    _apply_chart_theme(ax, fig, pal)

    allocation = data_manager.get_resource_allocation()
    names, alloc_hrs, avail_hrs = [], [], []

    for name, data in allocation.items():
        names.append(name)
        alloc_hrs.append(data['total_hours'])
        start = data_manager.get_project_start_date()
        end = data_manager.get_project_end_date()
        if start and end:
            working_days = data_manager.calendar_manager.calculate_working_days(start, end)
            avail_hrs.append(data['max_hours_per_day'] * working_days)
        else:
            avail_hrs.append(0)

    if not names:
        ax.text(0.5, 0.5, "No Resources", ha='center', va='center',
                transform=ax.transAxes, color=pal['text_muted'], fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        x = np.arange(len(names))
        w = 0.32

        bars1 = ax.bar(x - w / 2, alloc_hrs, w, label='Allocated', color='#42A5F5',
                        edgecolor='none', zorder=3)
        bars2 = ax.bar(x + w / 2, avail_hrs, w, label='Available', color='#A5D6A7',
                        edgecolor='none', zorder=3)

        ax.set_ylabel('Hours', fontsize=9)
        ax.set_title('Resource Workload', fontsize=10, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=35, ha='right', fontsize=8)
        ax.legend(fontsize=8, framealpha=0.6)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4, color=pal['chart_grid'])
        ax.set_axisbelow(True)

    fig.tight_layout()
    main_window.resource_allocation_canvas.draw()


def update_cost_trend_chart(main_window, data_manager, pal):
    """Area chart with gradient fill for cost trend."""
    fig = main_window.cost_trend_figure
    fig.clear()
    ax = fig.add_subplot(111)
    _apply_chart_theme(ax, fig, pal)

    start_date = data_manager.get_project_start_date()
    end_date = data_manager.get_project_end_date()

    if not start_date or not end_date:
        ax.text(0.5, 0.5, "No Project Dates", ha='center', va='center',
                transform=ax.transAxes, color=pal['text_muted'], fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
        main_window.cost_trend_canvas.draw()
        return

    is_monthly = (end_date - start_date).days >= 30

    if is_monthly:
        current = start_date.replace(day=1)
        period_costs = {}
        while current <= end_date:
            period_end = (current + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            if period_end > end_date:
                period_end = end_date

            key = current.strftime("%Y-%m")
            period_costs[key] = 0.0

            day = current
            while day <= period_end:
                daily = 0.0
                for task in data_manager.tasks:
                    if task.is_summary or task.is_milestone:
                        continue
                    if max(task.start_date, day) <= min(task.end_date, day):
                        for rn, ap in task.assigned_resources:
                            res = data_manager.get_resource(rn)
                            if res and data_manager.calendar_manager.is_working_day(day, res.exceptions):
                                hpd = data_manager.calendar_manager.hours_per_day
                                daily += hpd * (ap / 100.0) * res.billing_rate
                period_costs[key] += daily
                day += timedelta(days=1)
            current = (current + timedelta(days=32)).replace(day=1)

        dates = [datetime.strptime(k, "%Y-%m") for k in period_costs]
        costs = list(period_costs.values())
        title = 'Monthly Cost Trend'
        fmt = '%b %Y'
    else:
        dates, costs = [], []
        current = start_date
        while current <= end_date:
            daily = 0.0
            for task in data_manager.tasks:
                if task.is_summary or task.is_milestone:
                    continue
                if max(task.start_date, current) <= min(task.end_date, current):
                    for rn, ap in task.assigned_resources:
                        res = data_manager.get_resource(rn)
                        if res and data_manager.calendar_manager.is_working_day(current, res.exceptions):
                            hpd = data_manager.calendar_manager.hours_per_day
                            daily += hpd * (ap / 100.0) * res.billing_rate
            dates.append(current)
            costs.append(daily)
            current += timedelta(days=1)
        title = 'Daily Cost Trend'
        fmt = '%d %b'

    if not dates:
        ax.text(0.5, 0.5, "No Cost Data", ha='center', va='center',
                transform=ax.transAxes, color=pal['text_muted'], fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.plot(dates, costs, color='#42A5F5', linewidth=2, zorder=3)
        ax.fill_between(dates, costs, alpha=0.15, color='#42A5F5', zorder=2)
        ax.scatter(dates, costs, color='#1E88E5', s=18, zorder=4, edgecolors='white', linewidths=0.5)

        ax.set_title(title, fontsize=10, pad=10)
        ax.set_xlabel('Date', fontsize=8)
        symbol = data_manager.settings.currency.symbol
        ax.set_ylabel(f'Cost ({symbol})', fontsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
        ax.tick_params(axis='x', rotation=40, labelsize=7)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4, color=pal['chart_grid'])
        ax.set_axisbelow(True)

    fig.tight_layout()
    main_window.cost_trend_canvas.draw()


# ---------------------------------------------------------------------------
# Cost Breakdown Table
# ---------------------------------------------------------------------------

def _update_cost_breakdown_table(main_window, data_manager):
    """Populate the cost breakdown table."""
    table = main_window.cost_breakdown_table
    table.clear()

    breakdown = data_manager.get_cost_breakdown_data()
    headers = breakdown['headers']
    rows = breakdown['rows']

    if not rows:
        table.setRowCount(0)
        table.setColumnCount(0)
        return

    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)

    # Use Stretch for first column, Fixed for the rest
    for col in range(len(headers)):
        if col == 0:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        else:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(col, 120)

    table.setRowCount(len(rows))
    for i, row_data in enumerate(rows):
        for j, item in enumerate(row_data):
            cell = QTableWidgetItem(item)
            # Right-align numeric/currency columns
            if j > 0:
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
            table.setItem(i, j, cell)


# ---------------------------------------------------------------------------
# Clear Dashboard
# ---------------------------------------------------------------------------

def clear_dashboard(main_window):
    """Reset dashboard Smart Diagnosis section."""
    if hasattr(main_window, 'intel_results_label'):
        main_window.intel_results_label.setText(
            "AI-powered analysis of your schedule, cost, and risks will appear here."
        )
        main_window.intel_results_label.setStyleSheet(
            "color: #78909C; font-style: italic; margin-top: 8px; border: none;"
        )

    if hasattr(main_window, 'intel_progress'):
        main_window.intel_progress.setVisible(False)