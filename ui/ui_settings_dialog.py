from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QLabel, QLineEdit, QDateEdit, QGroupBox, 
                             QCheckBox, QPushButton, QComboBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import QDate, QTime, Qt
from datetime import datetime
from settings_manager.settings_manager import DateFormat, DurationUnit
from calendar_manager.calendar_manager import CalendarManager
from ui.ui_time_picker import TimePickerWidget

class SettingsDialog(QDialog):
    """Unified settings dialog for Project, Calendar, and Interface settings"""
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.calendar_manager = data_manager.calendar_manager
        self.settings = data_manager.settings
        
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(650)
        self.setMinimumHeight(450)
        
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # Initialize tabs
        self.general_tab = self._create_general_tab()
        self.calendar_tab = self._create_calendar_tab()
        self.interface_tab = self._create_interface_tab()
        
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.calendar_tab, "Calendar")
        self.tabs.addTab(self.interface_tab, "Interface")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._save_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def _create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        
        # Project Name
        self.project_name_input = QLineEdit(self.data_manager.project_name)
        form_layout.addRow("Project Name:", self.project_name_input)
        
        # Project Start Date
        self.project_start_date_input = QDateEdit()
        self.project_start_date_input.setCalendarPopup(True)
        self.project_start_date_input.setDisplayFormat("yyyy-MM-dd")
        
        initial_date = QDate.currentDate()
        if self.settings.project_start_date:
            initial_date = QDate(self.settings.project_start_date.year,
                                 self.settings.project_start_date.month,
                                 self.settings.project_start_date.day)
        self.project_start_date_input.setDate(initial_date)
        form_layout.addRow("Project Start Date:", self.project_start_date_input)
        
        layout.addLayout(form_layout)
        
        # Disclaimer
        note_label = QLabel("ℹ️ Note: For new projects, please ensure you also configure the Calendar (working hours) and Date Format settings.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: blue; font-style: italic; margin-top: 10px;")
        layout.addWidget(note_label)
        
        layout.addStretch()
        return widget
        
    def _create_calendar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Disclaimer
        disclaimer_label = QLabel("ℹ️ Note: Please setup calendar time and working hours at the start of project creation for best results.")
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setStyleSheet("color: blue; font-style: italic;")
        layout.addWidget(disclaimer_label)
        
        # Working Hours Group
        hours_group = QGroupBox("Working Hours")
        hours_layout = QVBoxLayout()
        
        # Display Total Hours
        hours_display_layout = QHBoxLayout()
        hours_display_layout.addWidget(QLabel("Total Hours per Day:"))
        self.hours_display = QLineEdit()
        self.hours_display.setReadOnly(True)
        self.hours_display.setMaximumWidth(100)
        self.hours_display.setText(f"{self.calendar_manager.hours_per_day:.2f} hours")
        hours_display_layout.addWidget(self.hours_display)
        hours_display_layout.addStretch()
        hours_layout.addLayout(hours_display_layout)
        
        # Start Time
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(QLabel("Work Start Time:"))
        
        start_parts = self.calendar_manager.working_hours_start.split(':')
        start_qtime = QTime(int(start_parts[0]), int(start_parts[1]))
        self.start_time_picker = TimePickerWidget(start_qtime)
        self.start_time_picker.timeChanged.connect(self._update_hours_display)
        start_time_layout.addWidget(self.start_time_picker)
        hours_layout.addLayout(start_time_layout)
        
        # End Time
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(QLabel("Work End Time:"))
        
        end_parts = self.calendar_manager.working_hours_end.split(':')
        end_qtime = QTime(int(end_parts[0]), int(end_parts[1]))
        self.end_time_picker = TimePickerWidget(end_qtime)
        self.end_time_picker.timeChanged.connect(self._update_hours_display)
        end_time_layout.addWidget(self.end_time_picker)
        hours_layout.addLayout(end_time_layout)
        
        hours_group.setLayout(hours_layout)
        layout.addWidget(hours_group)
        
        # Working Days Group
        days_group = QGroupBox("Working Days")
        days_layout = QVBoxLayout()
        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        grid_layout = QHBoxLayout() # Use HBox for cleaner look if space allows, or flow
        
        # Split into two columns
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(i in self.calendar_manager.working_days)
            self.day_checkboxes[i] = checkbox
            if i < 4:
                col1.addWidget(checkbox)
            else:
                col2.addWidget(checkbox)
                
        grid_layout.addLayout(col1)
        grid_layout.addLayout(col2)
        days_layout.addLayout(grid_layout)
        
        days_group.setLayout(days_layout)
        layout.addWidget(days_group)
        
        return widget

    def _create_interface_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_layout = QFormLayout()
        
        # Date Format
        self.date_format_combo = QComboBox()
        for df in DateFormat:
            self.date_format_combo.addItem(df.value, df)
        
        current_index = self.date_format_combo.findData(self.settings.default_date_format)
        if current_index != -1:
            self.date_format_combo.setCurrentIndex(current_index)
            
        form_layout.addRow("Date Format:", self.date_format_combo)
        
        # Duration Unit
        self.duration_unit_combo = QComboBox()
        for du in DurationUnit:
            self.duration_unit_combo.addItem(du.value, du)
            
        current_dur_index = self.duration_unit_combo.findData(self.settings.duration_unit)
        if current_dur_index != -1:
            self.duration_unit_combo.setCurrentIndex(current_dur_index)
            
        form_layout.addRow("Duration Unit:", self.duration_unit_combo)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        return widget
        
    def _update_hours_display(self):
        start_time = self.start_time_picker.get_time()
        end_time = self.end_time_picker.get_time()
        
        start_hours = start_time.hour() + start_time.minute() / 60.0
        end_hours = end_time.hour() + end_time.minute() / 60.0
        
        hours_diff = end_hours - start_hours
        if hours_diff < 0:
            hours_diff += 24
            
        self.hours_display.setText(f"{hours_diff:.2f} hours")

    def _save_settings(self):
        # 1. Save General Settings
        self.data_manager.project_name = self.project_name_input.text()
        
        qdate = self.project_start_date_input.date()
        new_start_date = datetime(qdate.year(), qdate.month(), qdate.day())
        self.settings.project_start_date = new_start_date
        
        # 2. Save Calendar Settings
        start_time = self.start_time_picker.get_time()
        end_time = self.end_time_picker.get_time()
        start_str = start_time.toString("HH:mm")
        end_str = end_time.toString("HH:mm")
        
        self.calendar_manager.set_working_hours(start_str, end_str)
        
        working_days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
        self.calendar_manager.set_working_days(working_days)
        
        # 3. Save Interface Settings
        self.settings.default_date_format = self.date_format_combo.currentData()
        self.settings.duration_unit = self.duration_unit_combo.currentData()
        
        self.accept()
