from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QDoubleSpinBox,
                             QPushButton, QCheckBox, QLabel, QGroupBox, QLineEdit)
from PyQt6.QtCore import QTime
from calendar_manager.calendar_manager import CalendarManager
from ui.ui_time_picker import TimePickerWidget

class CalendarSettingsDialog(QDialog):
    """Dialog for calendar settings"""
    
    def __init__(self, parent, calendar_manager: CalendarManager):
        super().__init__(parent)
        self.calendar_manager = calendar_manager
        
        self.setWindowTitle("Calendar Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Disclaimer
        disclaimer_label = QLabel("ℹ️ Note: Please setup calendar time and working hours at the start of project creation for best results.")
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setStyleSheet("color: blue; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(disclaimer_label)

        # Working Hours Section
        hours_group = QGroupBox("Working Hours")
        hours_layout = QVBoxLayout()
        
        # Working hours display (calculated automatically)
        hours_display_layout = QHBoxLayout()
        hours_display_layout.addWidget(QLabel("Total Hours per Day:"))
        self.hours_display = QLineEdit()
        self.hours_display.setReadOnly(True)
        self.hours_display.setMaximumWidth(100)
        self.hours_display.setText(f"{self.calendar_manager.hours_per_day:.2f} hours")
        hours_display_layout.addWidget(self.hours_display)
        hours_display_layout.addStretch()
        hours_layout.addLayout(hours_display_layout)
        
        # Start Time Picker
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(QLabel("Work Start Time:"))
        
        # Parse start time
        start_parts = self.calendar_manager.working_hours_start.split(':')
        start_qtime = QTime(int(start_parts[0]), int(start_parts[1]))
        
        self.start_time_picker = TimePickerWidget(start_qtime)
        self.start_time_picker.timeChanged.connect(self._update_hours_display)
        start_time_layout.addWidget(self.start_time_picker)
        
        hours_layout.addLayout(start_time_layout)
        
        # End Time Picker
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(QLabel("Work End Time:"))
        
        # Parse end time
        end_parts = self.calendar_manager.working_hours_end.split(':')
        end_qtime = QTime(int(end_parts[0]), int(end_parts[1]))
        
        self.end_time_picker = TimePickerWidget(end_qtime)
        self.end_time_picker.timeChanged.connect(self._update_hours_display)
        end_time_layout.addWidget(self.end_time_picker)
        
        hours_layout.addLayout(end_time_layout)
        
        hours_group.setLayout(hours_layout)
        layout.addWidget(hours_group)
        
        # Working Days Section
        days_group = QGroupBox("Working Days")
        days_layout = QVBoxLayout()
        
        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(i in self.calendar_manager.working_days)
            self.day_checkboxes[i] = checkbox
            days_layout.addWidget(checkbox)
        
        days_group.setLayout(days_layout)
        layout.addWidget(days_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._save_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initial hours display update
        self._update_hours_display()
    
    def _update_hours_display(self):
        """Update the hours per day display based on start and end times"""
        start_time = self.start_time_picker.get_time()
        end_time = self.end_time_picker.get_time()
        
        # Calculate hours
        start_hours = start_time.hour() + start_time.minute() / 60.0
        end_hours = end_time.hour() + end_time.minute() / 60.0
        
        hours_diff = end_hours - start_hours
        
        # Handle crossing midnight
        if hours_diff < 0:
            hours_diff += 24
        
        self.hours_display.setText(f"{hours_diff:.2f} hours")
    
    def _save_settings(self):
        """Save calendar settings"""
        # Get times from pickers
        start_time = self.start_time_picker.get_time()
        end_time = self.end_time_picker.get_time()
        
        # Format as HH:MM
        start_str = start_time.toString("HH:mm")
        end_str = end_time.toString("HH:mm")
        
        # Save working hours
        self.calendar_manager.set_working_hours(start_str, end_str)
        
        # Save working days
        working_days = [day for day, checkbox in self.day_checkboxes.items() 
                       if checkbox.isChecked()]
        self.calendar_manager.set_working_days(working_days)
        
        self.accept()
