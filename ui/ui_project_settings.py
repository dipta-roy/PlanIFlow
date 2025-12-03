from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit)
from PyQt6.QtCore import QDate, Qt
from datetime import datetime
from settings_manager.settings_manager import DateFormat # Import DateFormat

class ProjectSettingsDialog(QDialog):
    """Dialog to edit project settings like name and start date."""
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Project Settings")
        self.data_manager = data_manager
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        # Project Name
        self.project_name_input = QLineEdit(self.data_manager.project_name)
        self.form_layout.addRow("Project Name:", self.project_name_input)
        
        # Project Start Date
        self.project_start_date_input = QDateEdit()
        self.project_start_date_input.setCalendarPopup(True)
        self.project_start_date_input.setDisplayFormat("yyyy-MM-dd")
        
        # Set initial date from settings, or current date if not set
        initial_date = QDate.currentDate()
        if self.data_manager.settings.project_start_date:
            initial_date = QDate(self.data_manager.settings.project_start_date.year,
                                 self.data_manager.settings.project_start_date.month,
                                 self.data_manager.settings.project_start_date.day)
        self.project_start_date_input.setDate(initial_date)
        self.form_layout.addRow("Project Start Date:", self.project_start_date_input)
        
        self.layout.addLayout(self.form_layout)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(self.button_layout)

    def get_project_name(self):
        return self.project_name_input.text()

    def get_project_start_date(self):
        qdate = self.project_start_date_input.date()
        return datetime(qdate.year(), qdate.month(), qdate.day())

class DateFormatDialog(QDialog):
    """Dialog to select date format."""
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Date Format Settings")
        self.settings = settings
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        # Date Format
        self.date_format_combo = QComboBox()
        for df in DateFormat:
            self.date_format_combo.addItem(df.value, df)
        
        # Set current format
        current_index = self.date_format_combo.findData(self.settings.default_date_format)
        if current_index != -1:
            self.date_format_combo.setCurrentIndex(current_index)
        
        self.form_layout.addRow("Date Format:", self.date_format_combo)
        
        self.layout.addLayout(self.form_layout)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._apply_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(self.button_layout)

    def _apply_settings(self):
        selected_format = self.date_format_combo.currentData()
        self.settings.default_date_format = selected_format
        self.accept()


