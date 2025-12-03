from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QCheckBox, QPushButton)
from settings_manager.settings_manager import ProjectSettings, DurationUnit

class DurationUnitDialog(QDialog):
    """Dialog for selecting duration unit"""
    
    def __init__(self, parent, settings: ProjectSettings):
        super().__init__(parent)
        self.settings = settings
        
        self.setWindowTitle("Duration Unit Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel(
            "Select the unit for task duration calculations.\n\n"
            "• Days: Duration calculated in working days\n"
            "• Hours: Duration calculated in working hours\n\n"
            "Changing this setting will update how durations are\n"
            "displayed and calculated throughout the project."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Radio buttons
        group_box = QGroupBox("Duration Unit")
        group_layout = QVBoxLayout(group_box)
        
        self.days_radio = QCheckBox("Days (working days)")
        self.days_radio.setChecked(self.settings.duration_unit == DurationUnit.DAYS)
        group_layout.addWidget(self.days_radio)
        
        self.hours_radio = QCheckBox("Hours (working hours)")
        self.hours_radio.setChecked(self.settings.duration_unit == DurationUnit.HOURS)
        group_layout.addWidget(self.hours_radio)
        
        # Make them mutually exclusive
        self.days_radio.toggled.connect(lambda checked: self.hours_radio.setChecked(not checked) if checked else None)
        self.hours_radio.toggled.connect(lambda checked: self.days_radio.setChecked(not checked) if checked else None)
        
        layout.addWidget(group_box)
        
        # Example
        example_label = QLabel(
            "<b>Example:</b><br>"
            "Task from Monday to Friday (5 calendar days):<br>"
            "• In Days: Duration = 5 days<br>"
            "• In Hours: Duration = 40 hours (5 days × 8 hours/day)"
        )
        example_label.setWordWrap(True)
        layout.addWidget(example_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_selected_unit(self) -> DurationUnit:
        """Get selected duration unit"""
        if self.hours_radio.isChecked():
            return DurationUnit.HOURS
        else:
            return DurationUnit.DAYS
