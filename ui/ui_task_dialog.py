from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QDateEdit, QSpinBox, QTextEdit, QPushButton,
                             QMessageBox, QLabel, QComboBox, QCompleter, QWidget, QDoubleSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
import re
import logging
import math

from data_manager.manager import DataManager
from data_manager.models import Task, Resource, DependencyType, ScheduleType
from settings_manager.settings_manager import DurationUnit, DateFormat, ProjectSettings
from calendar_manager.calendar_manager import CalendarManager

class TaskDialog(QDialog):
    def __init__(self, parent=None, data_manager: DataManager = None, task: Task = None, parent_task: Task = None, is_milestone: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Edit Task" if task else "Add Task")
        self.data_manager = data_manager
        self.original_task = task
        self.setup_ui()
        self.parent_task = parent_task
        self.is_milestone = is_milestone

        self.task_data = {} # To store data for editing
        self.predecessor_rows = [] # Initialize here

        self.main_window = parent # Assuming parent is MainWindow

        self._init_ui()
        if task:
            self._load_task_data(task)
        elif parent_task:
            self._load_parent_task_defaults(parent_task)
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        form_layout.addRow("Task Name:", self.name_input)

        self.schedule_type_combo = QComboBox()
        self.schedule_type_combo.addItems([st.value for st in ScheduleType])
        self.schedule_type_combo.currentIndexChanged.connect(self._update_ui_for_schedule_type)
        form_layout.addRow("Schedule Type:", self.schedule_type_combo)

        # Start Date
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        
        if self.is_milestone:
            self.start_date_input.dateChanged.connect(self._on_milestone_date_changed)
            form_layout.addRow("Date:", self.start_date_input)
        else:
            self.start_date_input.dateChanged.connect(self._on_date_changed)
            form_layout.addRow("Start Date:", self.start_date_input)
        
        # End Date (hidden for milestones)
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate().addDays(7))
        self.end_date_input.dateChanged.connect(self._on_date_changed)
        
        if not self.is_milestone:
            form_layout.addRow("End Date:", self.end_date_input)
        
        # Duration
        duration_layout = QHBoxLayout()
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0.1, 10000)
        self.duration_input.setDecimals(1 if self.data_manager.settings.duration_unit == DurationUnit.HOURS else 0)
        self.duration_input.setValue(1)
        self.duration_input.valueChanged.connect(self._on_duration_changed)
        
        # Make sure keyboard editing is allowed and behaved
        self.duration_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # keyboard tracking controls whether valueChanged fires while typing; keep it on for immediate feedback
        self.duration_input.setKeyboardTracking(True)
        try:
            self.duration_input.setReadOnly(False)
        except Exception:
            # Older/odd PyQt bindings might not expose setReadOnly; ignore safely
            pass

        self.duration_input.valueChanged.connect(self._on_duration_changed)
        duration_layout.addWidget(self.duration_input)
        self.duration_unit_label = QLabel(self.data_manager.settings.duration_unit.value)
        duration_layout.addWidget(self.duration_unit_label)
        duration_layout.addStretch()
        
        self.duration_row_widget = QWidget() # Create a widget to hold the duration row
        self.duration_row_widget.setLayout(duration_layout)
        form_layout.addRow("Duration:", self.duration_row_widget) # Add the widget to the form layout

        # Initially hide the duration row if it's a milestone
        if self.is_milestone:
            self.duration_row_widget.setVisible(False)
            
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

        self.percent_complete_input = QSpinBox()
        self.percent_complete_input.setRange(0, 100)
        self.percent_complete_input.setSuffix("%")
        form_layout.addRow("% Complete:", self.percent_complete_input)
        
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
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)
        form_layout.addRow("Notes:", self.notes_input)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: blue; padding: 5px;")
        main_layout.addWidget(self.info_label)
        



        self._update_date_format()
        self.data_manager.settings.add_listener(self._on_settings_changed)
        self._update_ui_for_schedule_type() # Set initial UI state based on schedule type
    
    def setup_ui(self):
        # This is a placeholder since the original file includes full UI setup.
        # Keeping structure minimal for clarity.
        pass
        
    def _on_settings_changed(self, old_unit: DurationUnit, new_unit: DurationUnit):
        """Handle settings changes, specifically duration unit and date format."""
        # Update duration label
        self.duration_input.setWhatsThis(f"Duration ({self.data_manager.settings.duration_unit.value}):")
        # Update date format
        self._update_date_format()

    def _update_date_format(self):
        """Update the display format of date edits based on current settings."""
        qdate_format = self._get_qdate_format_string()
        self.start_date_input.setDisplayFormat(qdate_format)
        self.end_date_input.setDisplayFormat(qdate_format)

    def _get_qdate_format_string(self) -> str:
        """Converts the DateFormat enum to a QDateEdit compatible format string."""
        date_format_enum = self.data_manager.settings.default_date_format
        if date_format_enum == DateFormat.DD_MM_YYYY:
            return "dd-MM-yyyy"
        elif date_format_enum == DateFormat.DD_MMM_YYYY:
            return "dd-MMM-yyyy"
        else: # DateFormat.YYYY_MM_DD
            return "yyyy-MM-dd" # Default fallback

    def _get_strftime_format_string(self) -> str:
        """Converts the DateFormat enum to a strftime compatible format string."""
        date_format_enum = self.data_manager.settings.default_date_format
        if date_format_enum == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y'
        elif date_format_enum == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y'
        else: # DateFormat.YYYY_MM_DD
            return '%Y-%m-%d' # Default fallback

    def _add_predecessor_row(self, pred_id=None, dep_type=None, lag_days=0):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        task_combo = QComboBox()
        # Filter out the current task from the predecessor list
        available_tasks = sorted([t for t in self.data_manager.get_all_tasks() 
                                 if (not self.original_task or t.id != self.original_task.id)], 
                                 key=lambda t: t.id)
        
        for task in available_tasks:
            indent = ""
            # Add indentation for subtasks
            if task.parent_id is not None:
                # Determine depth for indentation
                current_task = task
                depth = 0
                while current_task and current_task.parent_id:
                    current_task = self.data_manager.get_task(current_task.parent_id)
                    depth += 1
                indent = "    " * depth
            task_combo.addItem(f"{indent}{task.id}: {task.name}", task.id)
        
        if pred_id:
            for i in range(task_combo.count()):
                if task_combo.itemData(i) == pred_id:
                    task_combo.setCurrentIndex(i)
                    break

        dep_type_combo = QComboBox()
        dep_type_combo.addItems([dt.name for dt in DependencyType])
        if dep_type:
            dep_type_combo.setCurrentText(dep_type)

        lag_spin = QSpinBox()
        lag_spin.setRange(-999, 999)
        lag_spin.setSuffix("d")
        lag_spin.setValue(lag_days)

        remove_btn = QPushButton("X")
        remove_btn.setFixedSize(20, 20)
        remove_btn.clicked.connect(lambda: self._remove_predecessor_row(row_widget))

        row_layout.addWidget(task_combo)
        row_layout.addWidget(dep_type_combo)
        row_layout.addWidget(lag_spin)
        row_layout.addWidget(remove_btn)

        self.pred_container_layout.addWidget(row_widget)
        self.predecessor_rows.append((task_combo, dep_type_combo, lag_spin, row_widget))

    def _remove_predecessor_row(self, row_widget):
        for i, (task_combo, dep_type_combo, lag_spin, widget) in enumerate(self.predecessor_rows):
            if widget == row_widget:
                self.pred_container_layout.removeWidget(row_widget)
                row_widget.deleteLater()
                self.predecessor_rows.pop(i)
                break

    def _add_resource_row(self, resource_name="", allocation=100):
        row_count = self.resources_table.rowCount()
        self.resources_table.insertRow(row_count)

        resource_combo = QComboBox()
        resource_combo.setEditable(True)
        if self.data_manager:
            all_resource_names = sorted([r.name for r in self.data_manager.get_all_resources()])
            resource_combo.addItems(all_resource_names)
            
            # Add completer for the resource combo box
            completer = QCompleter(all_resource_names, resource_combo)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            resource_combo.setCompleter(completer)

        if resource_name:
            resource_combo.setCurrentText(resource_name)
        
        allocation_spin = QSpinBox()
        allocation_spin.setRange(0, 100)
        allocation_spin.setSuffix("%")
        allocation_spin.setValue(allocation)

        self.resources_table.setCellWidget(row_count, 0, resource_combo)
        self.resources_table.setCellWidget(row_count, 1, allocation_spin)

    def _remove_selected_resource_row(self):
        selected_rows = sorted(set(index.row() for index in self.resources_table.selectedIndexes()), reverse=True)
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a resource assignment to remove.")
            return
        for row in selected_rows:
            self.resources_table.removeRow(row)

    def _on_milestone_date_changed(self, date: QDate):
        """When milestone date changes, set end date to be the same."""
        self.end_date_input.setDate(date)

    def _on_date_changed(self):
        """Recalculate duration when start or end date changes."""
        if self.is_milestone:
            return # Milestones have 0 duration, handled by _on_milestone_date_changed

        start = self.start_date_input.date()
        end = self.end_date_input.date()

        if start > end:
            # If start date becomes after end date, adjust end date
            self.end_date_input.setDate(start)
            end = start
        
        # Calculate duration based on working days
        start_dt = datetime(start.year(), start.month(), start.day())
        end_dt = datetime(end.year(), end.month(), end.day())
        
        if self.data_manager.settings.duration_unit == DurationUnit.DAYS:
            duration = self.data_manager.calendar_manager.calculate_working_days(start_dt, end_dt)
        else:
            duration = self.data_manager.calendar_manager.calculate_working_hours(start_dt, end_dt)
            
        self.duration_input.blockSignals(True)
        self.duration_input.setValue(duration)
        self.duration_input.blockSignals(False)

    def _on_duration_changed(self, value: float):
        """Recalculate end date or start date when duration changes."""
        # Update is_milestone based on duration
        self.is_milestone = (value == 0)
        #self._update_ui_for_schedule_type() # Update UI based on new milestone status

        if self.is_milestone:
            # For milestones, ensure start and end dates are the same
            self.end_date_input.setDate(self.start_date_input.date())
            return

        current_schedule_type = ScheduleType(self.schedule_type_combo.currentText())
        
        # Calculate days to add/subtract based on duration unit
        days_to_shift = 0
        if self.data_manager.settings.duration_unit == DurationUnit.DAYS:
            days_to_shift = int(value) - 1
        else: # HOURS
            hours_per_day = self.data_manager.calendar_manager.hours_per_day
            days_to_shift = math.ceil(value / hours_per_day) - 1
            
        if days_to_shift < 0:
            days_to_shift = 0

        if current_schedule_type == ScheduleType.AUTO_SCHEDULED:
            # For auto-scheduled tasks, the start date is fixed by predecessors.
            # Update the end date based on the new duration.
            start = self.start_date_input.date()
            start_dt = datetime(start.year(), start.month(), start.day())
            
            new_end_dt = self.data_manager.calendar_manager.add_working_days(start_dt, days_to_shift)
            
            self.end_date_input.blockSignals(True)
            self.end_date_input.setDate(QDate(new_end_dt.year, new_end_dt.month, new_end_dt.day))
            self.end_date_input.blockSignals(False)
        elif current_schedule_type == ScheduleType.MANUALLY_SCHEDULED:
            start = self.start_date_input.date()
            end = self.end_date_input.date()
            
            start_dt = datetime(start.year(), start.month(), start.day())
            end_dt = datetime(end.year(), end.month(), end.day())

            if self.update_end_radio.isChecked():
                # Calculate new end date
                new_end_dt = self.data_manager.calendar_manager.add_working_days(start_dt, days_to_shift)
                self.end_date_input.blockSignals(True)
                self.end_date_input.setDate(QDate(new_end_dt.year, new_end_dt.month, new_end_dt.day))
                self.end_date_input.blockSignals(False)
            elif self.update_start_radio.isChecked():
                # Calculate new start date
                new_start_dt = self.data_manager.calendar_manager.subtract_working_days(end_dt, days_to_shift)
                self.start_date_input.blockSignals(True)
                self.start_date_input.setDate(QDate(new_start_dt.year, new_start_dt.month, new_start_dt.day))
                self.start_date_input.blockSignals(False)

    def _update_ui_for_schedule_type(self):
        current_schedule_type = ScheduleType(self.schedule_type_combo.currentText())

        is_summary = self.original_task and getattr(self.original_task, 'is_summary', False)

        # Default states
        duration_enabled = True
        start_date_enabled = True
        end_date_enabled = True
        self.duration_row_widget.setVisible(True)
        self.info_label.setText("")

        if is_summary:
            # Summary tasks calculate dates from children; user should not edit duration.
            self.info_label.setText("ℹ️ This is a summary task. Dates are auto-calculated from subtasks.")
            duration_enabled = False
            start_date_enabled = False
            end_date_enabled = False
        else:
            # Behavior by schedule type
            if current_schedule_type == ScheduleType.AUTO_SCHEDULED:
                # For auto-scheduled tasks, start is determined by predecessors.
                # Allow editing duration for individual (non-summary) tasks so users can shorten/lengthen them.
                # Keep start and end date fields locked because they are computed from duration + calendar.
                duration_enabled = True
                start_date_enabled = False
                end_date_enabled = False
                self.info_label.setText("ℹ️ Auto Scheduled: change duration to automatically update dates based on predecessors.")
            elif current_schedule_type == ScheduleType.MANUALLY_SCHEDULED:
                # All fields are editable for manually scheduled tasks
                duration_enabled = True
                start_date_enabled = True
                end_date_enabled = True
                self.info_label.setText("")
            else:
                # default fallback: be conservative
                duration_enabled = True
                start_date_enabled = True
                end_date_enabled = True

        self.start_date_input.setEnabled(start_date_enabled)
        self.end_date_input.setEnabled(end_date_enabled)
        self.duration_input.setEnabled(duration_enabled)
        self.duration_row_widget.setEnabled(duration_enabled)

        if hasattr(self, 'update_end_radio'):
            # Update radio controls are only meaningful for manually scheduled tasks
            radios_enabled = duration_enabled and (current_schedule_type == ScheduleType.MANUALLY_SCHEDULED)
            self.update_end_radio.setEnabled(radios_enabled)
            self.update_start_radio.setEnabled(radios_enabled)

    def _load_task_data(self, task: Task):

        self.name_input.setText(task.name)
        self.schedule_type_combo.setCurrentText(task.schedule_type.value)
        self.start_date_input.setDate(task.start_date.date())
        self.end_date_input.setDate(task.end_date.date())
        
        if not self.is_milestone:
            duration = task.get_duration(self.data_manager.settings.duration_unit, self.data_manager.calendar_manager)
            self.duration_input.setValue(duration)

        self.percent_complete_input.setValue(task.percent_complete)
        
        # Populate predecessors
        for pred_id, dep_type, lag_days in task.predecessors:
            self._add_predecessor_row(pred_id, dep_type, lag_days)
        
        # Populate assigned resources
        self.resources_table.setRowCount(0) # Clear existing rows
        for resource_name, allocation in task.assigned_resources:
            self._add_resource_row(resource_name, allocation)
        
        self.notes_input.setText(task.notes)
        self._update_ui_for_schedule_type() # Update UI state after loading task data
        # Ensure duration spinbox can get keyboard focus (helps in some Qt versions)
        self.duration_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # If you want it focused automatically so the user can immediately type:
        # self.duration_input.setFocus()

    def _load_parent_task_defaults(self, parent_task: Task):
        """Set default values based on parent task for subtasks."""
        self.start_date_input.setDate(parent_task.start_date.date())
        self.end_date_input.setDate(parent_task.end_date.date())
        self.schedule_type_combo.setCurrentText(parent_task.schedule_type.value)
        if self.is_milestone:
            self.duration_input.setValue(0)

    def get_task_data(self) -> dict:
        """Returns a dictionary of task data from the form fields."""
        return self.task_data

    def accept(self):
        """Validate input and store data before closing the dialog."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Task Name cannot be empty.")
            return

        schedule_type = ScheduleType(self.schedule_type_combo.currentText())
        start_date_q = self.start_date_input.date()
        end_date_q = self.end_date_input.date()
        duration = self.duration_input.value() if not self.is_milestone else 0
        percent_complete = self.percent_complete_input.value()
        notes = self.notes_input.toPlainText().strip()

        start_date = datetime(start_date_q.year(), start_date_q.month(), start_date_q.day())
        end_date = datetime(end_date_q.year(), end_date_q.month(), end_date_q.day())

        if start_date > end_date:
            QMessageBox.warning(self, "Input Error", "Start Date cannot be after End Date.")
            return
        
        if self.is_milestone and start_date != end_date:
            QMessageBox.warning(self, "Input Error", "Milestones must have Start Date equal to End Date.")
            return
        
        if not self.is_milestone and duration == 0 and start_date != end_date:
            QMessageBox.warning(self, "Input Error", "Tasks with 0 duration must have Start Date equal to End Date.")
            return
        
        if not self.is_milestone and duration > 0 and start_date == end_date:
            QMessageBox.warning(self, "Input Error", "Tasks with duration must have Start Date before End Date.")
            return

        # Parse predecessors from table
        parsed_predecessors = []
        for task_combo, dep_type_combo, lag_spin, _ in self.predecessor_rows:
            pred_id = task_combo.currentData()
            dep_type = dep_type_combo.currentText()
            lag_days = lag_spin.value()
            parsed_predecessors.append((pred_id, dep_type, lag_days))

        # Parse resources from table
        parsed_resources = []
        for row in range(self.resources_table.rowCount()):
            resource_combo = self.resources_table.cellWidget(row, 0)
            allocation_spin = self.resources_table.cellWidget(row, 1)
            
            resource_name = resource_combo.currentText()
            allocation = allocation_spin.value()
            
            if not resource_name:
                QMessageBox.warning(self, "Input Error", f"Resource name cannot be empty in row {row + 1}.")
                return
            
            parsed_resources.append((resource_name, allocation))
        
        # If editing an existing task, check for summary task constraints
        if self.original_task and getattr(self.original_task, 'is_summary', False):
            if schedule_type == ScheduleType.MANUALLY_SCHEDULED:
                QMessageBox.warning(self, "Validation Error",
                                    "Summary tasks must always be 'Auto Scheduled'. Please change the schedule type.")
                return
            # For summary tasks, duration is calculated, so we don't use the input duration
            duration = self.original_task.get_duration(self.data_manager.settings.duration_unit, self.data_manager.calendar_manager)


        self.task_data = {
            'name': name,
            'schedule_type': schedule_type,
            'start_date': start_date,
            'end_date': end_date,
            'duration': duration, # This will be used to calculate end_date if schedule_type is auto
            'percent_complete': percent_complete,
            'predecessors': parsed_predecessors,
            'assigned_resources': parsed_resources,
            'notes': notes
        }
        super().accept()

    def reject(self):
        """Handle cancel button click."""
        super().reject()