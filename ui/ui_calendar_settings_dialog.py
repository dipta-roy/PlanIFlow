from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QDoubleSpinBox,
                             QPushButton, QCheckBox, QLabel)
from calendar_manager.calendar_manager import CalendarManager

class CalendarSettingsDialog(QDialog):
    """Dialog for calendar settings"""
    
    def __init__(self, parent, calendar_manager: CalendarManager):
        super().__init__(parent)
        self.calendar_manager = calendar_manager
        
        self.setWindowTitle("Calendar Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        # Hours per day
        hours_layout = QHBoxLayout()
        hours_layout.addWidget(QLabel("Working Hours per Day:"))
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(1, 24)
        self.hours_spin.setValue(self.calendar_manager.hours_per_day)
        self.hours_spin.setSuffix(" hours")
        hours_layout.addWidget(self.hours_spin)
        hours_layout.addStretch()
        layout.addLayout(hours_layout)
        
        # Working days
        layout.addWidget(QLabel("Working Days:"))
        
        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(i in self.calendar_manager.working_days)
            self.day_checkboxes[i] = checkbox
            layout.addWidget(checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._save_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _save_settings(self):
        """Save calendar settings"""
        self.calendar_manager.set_hours_per_day(self.hours_spin.value())
        
        working_days = [day for day, checkbox in self.day_checkboxes.items() 
                       if checkbox.isChecked()]
        self.calendar_manager.set_working_days(working_days)
        
        self.accept()
