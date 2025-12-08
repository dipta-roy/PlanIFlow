
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QTextEdit, QTableWidget, QHeaderView, QTableWidgetItem, QScrollArea
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from settings_manager.settings_manager import DurationUnit
from data_manager.models import TaskStatus

# Matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def create_dashboard(main_window):
    """Create project dashboard"""
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # Project name display
    main_window.dashboard_project_name = QLabel(f"<h2>{main_window.data_manager.project_name}</h2>")
    main_window.dashboard_project_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(main_window.dashboard_project_name)

    # Summary cards
    cards_layout = QHBoxLayout()

    main_window.start_date_label = QLabel("Start: N/A")
    main_window.end_date_label = QLabel("End: N/A")
    main_window.total_tasks_label = QLabel("Tasks: 0")
    main_window.completion_label = QLabel("Complete: 0%")
    main_window.total_resources_label = QLabel("Resources: 0")
    main_window.total_effort_label = QLabel("Effort: 0h")

    main_window.total_cost_label = QLabel("Cost: $0.00")
    
    # New status tiles
    main_window.upcoming_tasks_label = QLabel("Upcoming: 0/0")
    main_window.in_progress_tasks_label = QLabel("In Progress: 0/0")
    main_window.completed_tasks_label = QLabel("Completed: 0/0")
    main_window.overdue_tasks_label = QLabel("Overdue: 0/0")

    # Define specific colors for status cards
    status_card_colors = {
        "Upcoming": "#B0BEC5",    # Grey
        "In Progress": "#B3E5FF", # Light Blue
        "Completed": "#C8E6C9",   # Light Green
        "Overdue": "#FFCDD2"     # Light Red
    }

    all_labels = [
        main_window.start_date_label, main_window.end_date_label, 
        main_window.total_tasks_label, main_window.completion_label, 
        main_window.total_resources_label,
        main_window.total_effort_label, main_window.total_cost_label,
        main_window.upcoming_tasks_label, main_window.in_progress_tasks_label,
        main_window.completed_tasks_label, main_window.overdue_tasks_label
    ]

    for i, label in enumerate(all_labels):
        card = QGroupBox()
        card_layout = QVBoxLayout(card)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        label.setMinimumHeight(40)
        card_layout.addWidget(label)

        # Apply background color to the QGroupBox only for status tiles
        if label == main_window.upcoming_tasks_label:
            card.setStyleSheet(f"QGroupBox {{ background-color: {status_card_colors['Upcoming']}; border-radius: 5px; }}")
        elif label == main_window.in_progress_tasks_label:
            card.setStyleSheet(f"QGroupBox {{ background-color: {status_card_colors['In Progress']}; border-radius: 5px; }}")
        elif label == main_window.completed_tasks_label:
            card.setStyleSheet(f"QGroupBox {{ background-color: {status_card_colors['Completed']}; border-radius: 5px; }}")
        elif label == main_window.overdue_tasks_label:
            card.setStyleSheet(f"QGroupBox {{ background-color: {status_card_colors['Overdue']}; border-radius: 5px; }}")

        cards_layout.addWidget(card)

    layout.addLayout(cards_layout)

    # Charts Layout
    charts_layout = QHBoxLayout()
    layout.addLayout(charts_layout)

    # Task Status Pie Chart
    main_window.task_status_figure = Figure(figsize=(4, 4))
    main_window.task_status_canvas = FigureCanvas(main_window.task_status_figure)
    charts_layout.addWidget(main_window.task_status_canvas)

    # Resource Allocation Bar Chart
    main_window.resource_allocation_figure = Figure(figsize=(4, 4))
    main_window.resource_allocation_canvas = FigureCanvas(main_window.resource_allocation_figure)
    charts_layout.addWidget(main_window.resource_allocation_canvas)

    # Cost Trend Line Chart
    main_window.cost_trend_figure = Figure(figsize=(4, 4))
    main_window.cost_trend_canvas = FigureCanvas(main_window.cost_trend_figure)
    charts_layout.addWidget(main_window.cost_trend_canvas)




    # Monthly/Daily Cost Breakdown
    layout.addWidget(QLabel("<h3>💰 Monthly/Daily Cost Breakdown</h3>"))
    cost_breakdown_group = QGroupBox()
    main_window.cost_breakdown_layout = QVBoxLayout(cost_breakdown_group)
    main_window.cost_breakdown_table = QTableWidget()
    main_window.cost_breakdown_table.setMinimumHeight(200) # Increased height
    main_window.cost_breakdown_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    main_window.cost_breakdown_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    main_window.cost_breakdown_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Set stretch mode here
    main_window.cost_breakdown_layout.addWidget(main_window.cost_breakdown_table)
    layout.addWidget(cost_breakdown_group)

    scroll_area.setWidget(widget)
    return scroll_area

def update_dashboard(main_window):
    """Update project dashboard with current data"""
    data_manager = main_window.data_manager

    # Update project name
    main_window.dashboard_project_name.setText(f"<h2>{data_manager.project_name}</h2>")

    # Update summary cards
    main_window.start_date_label.setText(f"Start: {data_manager.get_project_start_date().strftime('%Y-%m-%d') if data_manager.get_project_start_date() else 'N/A'}")
    main_window.end_date_label.setText(f"End: {data_manager.get_project_end_date().strftime('%Y-%m-%d') if data_manager.get_project_end_date() else 'N/A'}")
    main_window.total_tasks_label.setText(f"Tasks: {len(data_manager.tasks)}")
    
    completed_tasks = [task for task in data_manager.tasks if task.percent_complete == 100]
    completion_percentage = (len(completed_tasks) / len(data_manager.tasks) * 100) if data_manager.tasks else 0
    main_window.completion_label.setText(f"Complete: {completion_percentage:.0f}%")
    main_window.total_resources_label.setText(f"Resources: {len(data_manager.resources)}")

    total_effort = 0
    total_project_cost = 0
    for task in data_manager.tasks:
        if not task.is_summary and not task.is_milestone:
            task_duration_hours = task.get_duration(data_manager.settings.duration_unit, data_manager.calendar_manager)
            
            for resource_name, allocation_percent in task.assigned_resources:
                resource = data_manager.get_resource(resource_name)
                if resource:
                    # Assuming task_duration_hours is already in hours or converted to hours
                    # If duration unit is days, convert to hours using resource's max_hours_per_day
                    if data_manager.settings.duration_unit == DurationUnit.DAYS:
                        # This is a simplification. A more accurate calculation would consider working days within the task duration.
                        # For now, let's assume 8 hours per day if duration is in days.
                        # Or, better, use calendar_manager.calculate_working_hours for the task duration.
                        task_hours_for_resource = data_manager.calendar_manager.calculate_working_hours(task.start_date, task.end_date, resource_exceptions=resource.exceptions) * (allocation_percent / 100.0)
                    else: # DurationUnit.HOURS
                        task_hours_for_resource = task_duration_hours * (allocation_percent / 100.0)

                    total_effort += task_hours_for_resource
                    total_project_cost += task_hours_for_resource * resource.billing_rate

    main_window.total_effort_label.setText(f"Effort: {total_effort:.0f}h")
    main_window.total_cost_label.setText(f"Cost: ${total_project_cost:.2f}")

    # Calculate task status counts
    upcoming_count = 0
    in_progress_count = 0
    completed_count = 0
    overdue_count = 0
    total_work_tasks = 0

    for task in data_manager.tasks:
        if not task.is_summary: # Only count non-summary tasks for status breakdown
            total_work_tasks += 1
            status = task.get_status()
            if status == TaskStatus.UPCOMING:
                upcoming_count += 1
            elif status == TaskStatus.IN_PROGRESS:
                in_progress_count += 1
            elif status == TaskStatus.COMPLETED:
                completed_count += 1
            elif status == TaskStatus.OVERDUE:
                overdue_count += 1

    main_window.upcoming_tasks_label.setText(f"Upcoming: {upcoming_count}/{total_work_tasks}")
    main_window.in_progress_tasks_label.setText(f"In Progress: {in_progress_count}/{total_work_tasks}")
    main_window.completed_tasks_label.setText(f"Completed: {completed_count}/{total_work_tasks}")
    main_window.overdue_tasks_label.setText(f"Overdue: {overdue_count}/{total_work_tasks}")

    # Update charts
    update_task_status_pie_chart(main_window, upcoming_count, in_progress_count, completed_count, overdue_count, total_work_tasks)
    update_resource_allocation_bar_chart(main_window, data_manager)
    update_cost_trend_line_chart(main_window, data_manager)

    # Update monthly/daily cost breakdown table
    main_window.cost_breakdown_table.clear()
    
    breakdown_data = data_manager.get_cost_breakdown_data()
    headers = breakdown_data['headers']
    rows = breakdown_data['rows']

    if not rows:
        main_window.cost_breakdown_table.setRowCount(0)
        main_window.cost_breakdown_table.setColumnCount(0)
        main_window.cost_breakdown_table.setHorizontalHeaderLabels([])
        return

    main_window.cost_breakdown_table.setColumnCount(len(headers))
    main_window.cost_breakdown_table.setHorizontalHeaderLabels(headers)
    
    # Set resize mode for columns to Fixed and set a default width
    for col_idx in range(len(headers)):
        main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Fixed)
        main_window.cost_breakdown_table.setColumnWidth(col_idx, 120) # Default fixed width, adjust as needed

    main_window.cost_breakdown_table.setRowCount(len(rows))
    for i, row_data in enumerate(rows):
        for j, item in enumerate(row_data):
            main_window.cost_breakdown_table.setItem(i, j, QTableWidgetItem(item))


def update_task_status_pie_chart(main_window, upcoming_count, in_progress_count, completed_count, overdue_count, total_work_tasks):
    main_window.task_status_figure.clear()
    ax = main_window.task_status_figure.add_subplot(111)

    labels = []
    sizes = []
    colors = []
    explode = []

    if upcoming_count > 0:
        labels.append(f'Upcoming ({upcoming_count})')
        sizes.append(upcoming_count)
        colors.append('#B0BEC5')
        explode.append(0)
    if in_progress_count > 0:
        labels.append(f'In Progress ({in_progress_count})')
        sizes.append(in_progress_count)
        colors.append('#B3E5FF')
        explode.append(0)
    if completed_count > 0:
        labels.append(f'Completed ({completed_count})')
        sizes.append(completed_count)
        colors.append('#C8E6C9')
        explode.append(0.1) # Slightly explode completed for emphasis
    if overdue_count > 0:
        labels.append(f'Overdue ({overdue_count})')
        sizes.append(overdue_count)
        colors.append('#FFCDD2')
        explode.append(0)

    if not sizes: # Handle case with no tasks
        labels = ['No Tasks']
        sizes = [1]
        colors = ['#E0E0E0'] # Light grey
        explode = [0]

    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=140, textprops={'fontsize': 8})
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title('Task Status Breakdown', fontsize=10)

    main_window.task_status_canvas.draw()

def update_resource_allocation_bar_chart(main_window, data_manager):
    main_window.resource_allocation_figure.clear()
    ax = main_window.resource_allocation_figure.add_subplot(111)

    resource_allocation = data_manager.get_resource_allocation()
    resource_names = []
    total_hours = []
    max_hours = []

    for name, data in resource_allocation.items():
        resource_names.append(name)
        total_hours.append(data['total_hours'])
        max_hours.append(data['max_hours_per_day'] * data_manager.calendar_manager.calculate_working_days(
            data_manager.get_project_start_date(), data_manager.get_project_end_date()
        ) if data_manager.get_project_start_date() and data_manager.get_project_end_date() else 0)

    if not resource_names:
        ax.text(0.5, 0.5, "No Resources", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        x = range(len(resource_names))
        width = 0.35

        rects1 = ax.bar(x, total_hours, width, label='Allocated Hours', color='#64B5F6')
        rects2 = ax.bar([p + width for p in x], max_hours, width, label='Max Available Hours', color='#AED581')

        ax.set_ylabel('Hours')
        ax.set_title('Resource Allocation')
        ax.set_xticks([p + width / 2 for p in x])
        ax.set_xticklabels(resource_names, rotation=45, ha="right", fontsize=8)
        ax.legend(fontsize=8)
        ax.tick_params(axis='y', labelsize=8)
        main_window.resource_allocation_figure.tight_layout()

    main_window.resource_allocation_canvas.draw()

def update_cost_trend_line_chart(main_window, data_manager):
    main_window.cost_trend_figure.clear()
    ax = main_window.cost_trend_figure.add_subplot(111)

    if not data_manager.get_project_start_date() or not data_manager.get_project_end_date():
        ax.text(0.5, 0.5, "No Project Dates", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        main_window.cost_trend_canvas.draw()
        return

    start_date = data_manager.get_project_start_date()
    end_date = data_manager.get_project_end_date()

    if (end_date - start_date).days >= 30:
        # Monthly breakdown
        period_type = "Monthly"
        current_period_start = start_date.replace(day=1)
        period_costs = {}

        while current_period_start <= end_date:
            period_end = (current_period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            if period_end > end_date:
                period_end = end_date

            period_key = current_period_start.strftime("%Y-%m")
            period_costs[period_key] = 0.0

            temp_date = current_period_start
            while temp_date <= period_end:
                daily_cost = 0.0
                for task in data_manager.tasks:
                    if task.is_summary or task.is_milestone:
                        continue

                    overlap_start = max(task.start_date, temp_date)
                    overlap_end = min(task.end_date, temp_date)

                    if overlap_start <= overlap_end:
                        for resource_name, allocation_percent in task.assigned_resources:
                            resource = data_manager.get_resource(resource_name)
                            if resource:
                                if data_manager.calendar_manager.is_working_day(temp_date, resource.exceptions):
                                    hours_per_day = data_manager.calendar_manager.hours_per_day
                                    allocated_hours = hours_per_day * (allocation_percent / 100.0)
                                    daily_cost += allocated_hours * resource.billing_rate
                period_costs[period_key] += daily_cost
                temp_date += timedelta(days=1)
            
            current_period_start = (current_period_start + timedelta(days=32)).replace(day=1)
        
        dates = [datetime.strptime(k, "%Y-%m") for k in period_costs.keys()]
        costs = list(period_costs.values())
        title = 'Monthly Cost Trend'
        x_label_format = '%b-%Y'

    else:
        # Daily breakdown
        period_type = "Daily"
        dates = []
        costs = []

        current_date = start_date
        while current_date <= end_date:
            daily_cost = 0.0
            for task in data_manager.tasks:
                if task.is_summary or task.is_milestone:
                    continue

                overlap_start = max(task.start_date, current_date)
                overlap_end = min(task.end_date, current_date)

                if overlap_start <= overlap_end:
                    for resource_name, allocation_percent in task.assigned_resources:
                        resource = data_manager.get_resource(resource_name)
                        if resource:
                            if data_manager.calendar_manager.is_working_day(current_date, resource.exceptions):
                                hours_per_day = data_manager.calendar_manager.hours_per_day
                                allocated_hours = hours_per_day * (allocation_percent / 100.0)
                                daily_cost += allocated_hours * resource.billing_rate
            dates.append(current_date)
            costs.append(daily_cost)
            current_date += timedelta(days=1)
        title = 'Daily Cost Trend'
        x_label_format = '%Y-%m-%d'

    if not dates:
        ax.text(0.5, 0.5, "No Cost Data", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.plot(dates, costs, marker='o', linestyle='-', markersize=2)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('Date', fontsize=8)
        ax.set_ylabel('Cost ($)', fontsize=8)
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(True)
        main_window.cost_trend_figure.tight_layout()

    main_window.cost_trend_canvas.draw()