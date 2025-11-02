"""ui_dashboard.py
Contains dashboard creation and update logic.
Exports create_dashboard(main_window) -> QWidget
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QTextEdit, QTableWidget, QHeaderView, QTableWidgetItem
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from settings_manager import DurationUnit
from data_manager import TaskStatus # Import TaskStatus

def create_dashboard(main_window):
    """Create project dashboard"""
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

    # Resource Details
    
    layout.addWidget(QLabel("<h3>👥 Resource Details</h3>"))
    resource_group = QGroupBox()
    main_window.resource_layout = QVBoxLayout(resource_group)
    main_window.resource_table = QTableWidget()
    main_window.resource_table.setColumnCount(3)  # Name, Cost/Hour, Availability
    main_window.resource_table.setHorizontalHeaderLabels(["Resource Name", "Cost/Hour", "Availability"])
    main_window.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    main_window.resource_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    main_window.resource_layout.addWidget(main_window.resource_table)
    layout.addWidget(resource_group)


    # Monthly/Daily Cost Breakdown
    layout.addWidget(QLabel("<h3>💰 Monthly/Daily Cost Breakdown</h3>"))
    cost_breakdown_group = QGroupBox()
    main_window.cost_breakdown_layout = QVBoxLayout(cost_breakdown_group)
    main_window.cost_breakdown_table = QTableWidget()
    main_window.cost_breakdown_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    main_window.cost_breakdown_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    main_window.cost_breakdown_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    main_window.cost_breakdown_table.setColumnWidth(0, 100) # Set fixed width for 'Period' column
    main_window.cost_breakdown_table.setColumnWidth(1, 100) # Set fixed width for 'Total' column
    # Set resize mode for all columns after headers are set in update_dashboard
    # For now, set default to Interactive, then update in update_dashboard
    main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    main_window.cost_breakdown_layout.addWidget(main_window.cost_breakdown_table)
    layout.addWidget(cost_breakdown_group)

    return widget

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

    total_effort = 0
    total_project_cost = 0
    for task in data_manager.tasks:
        if not task.is_summary:
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

    # Update resource table
    main_window.resource_table.setRowCount(len(data_manager.resources))
    for i, resource in enumerate(data_manager.resources):
        main_window.resource_table.setItem(i, 0, QTableWidgetItem(resource.name))
        main_window.resource_table.setItem(i, 1, QTableWidgetItem(f"${resource.billing_rate:.2f}"))
        main_window.resource_table.setItem(i, 2, QTableWidgetItem(f"{resource.max_hours_per_day:.0f}h/day"))    # Update monthly/daily cost breakdown table
    main_window.cost_breakdown_table.clear()
    if data_manager.get_project_start_date() and data_manager.get_project_end_date():
        start_date = data_manager.get_project_start_date()
        end_date = data_manager.get_project_end_date()
        
        # Determine if duration is less than a month
        if (end_date - start_date).days < 30:
            # Display by day
            delta = timedelta(days=1)
            current_date = start_date
            headers = []
            while current_date <= end_date:
                headers.append(current_date.strftime("%d-%b"))
                current_date += delta
        else:
            # Display by month
            current_date = start_date.replace(day=1)
            headers = []
            while current_date <= end_date:
                headers.append(current_date.strftime("%b-%Y"))
                current_date = (current_date + timedelta(days=32)).replace(day=1)
        
        # Add resource names to headers
        column_headers = ["Period", "Total"] + [resource.name for resource in data_manager.resources]
        main_window.cost_breakdown_table.setColumnCount(len(column_headers))
        main_window.cost_breakdown_table.setHorizontalHeaderLabels(column_headers)
        
        # Set resize mode for columns
        main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        for col_idx in range(2, len(column_headers)):
            main_window.cost_breakdown_table.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Fixed)
            main_window.cost_breakdown_table.setColumnWidth(col_idx, 120) # Constant width for resource columns

        # Populate table with costs
        main_window.cost_breakdown_table.setRowCount(len(headers))
        for i, period_str in enumerate(headers):
            main_window.cost_breakdown_table.setItem(i, 0, QTableWidgetItem(period_str))
            
            period_start_dt = None
            period_end_dt = None

            if (end_date - start_date).days < 30: # Daily breakdown
                period_start_dt = start_date + timedelta(days=i)
                period_end_dt = period_start_dt
            else: # Monthly breakdown
                period_start_dt = datetime.strptime(period_str, "%b-%Y")
                period_end_dt = (period_start_dt + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                # Ensure period_end_dt does not exceed project_end_date
                if period_end_dt > end_date:
                    period_end_dt = end_date

            period_total_cost = 0
            resource_costs_in_period = {res.name: 0.0 for res in data_manager.resources}

            for task in data_manager.tasks:
                if task.is_summary: # Skip summary tasks
                    continue

                # Determine overlap between task and current period
                overlap_start = max(task.start_date, period_start_dt)
                overlap_end = min(task.end_date, period_end_dt)

                if overlap_start <= overlap_end:
                    for resource_name, allocation_percent in task.assigned_resources:
                        resource = data_manager.get_resource(resource_name)
                        if resource:
                            # Calculate working hours in the overlap period for this specific resource
                            overlap_working_hours = data_manager.calendar_manager.calculate_working_hours(overlap_start, overlap_end, resource_exceptions=resource.exceptions)
                            # Calculate resource's allocated hours for this overlap
                            allocated_hours_in_overlap = overlap_working_hours * (allocation_percent / 100.0)
                            cost_for_resource_in_overlap = allocated_hours_in_overlap * resource.billing_rate
                            resource_costs_in_period[resource_name] += cost_for_resource_in_overlap            
            
            # Populate Total column (index 1)
            for resource_name, cost in resource_costs_in_period.items():
                period_total_cost += cost
            main_window.cost_breakdown_table.setItem(i, 1, QTableWidgetItem(f"${period_total_cost:.2f}"))

            # Populate individual resource columns (starting from index 2)
            for j, resource in enumerate(data_manager.resources):
                cost = resource_costs_in_period[resource.name]
                main_window.cost_breakdown_table.setItem(i, j + 2, QTableWidgetItem(f"${cost:.2f}"))