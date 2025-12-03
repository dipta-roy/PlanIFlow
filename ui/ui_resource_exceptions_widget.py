"""
Resource Exceptions Widget - Manages resource holidays/leaves
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QListWidget, QDateEdit, QLabel, QMessageBox,
                              QDialog, QRadioButton, QButtonGroup)
from PyQt6.QtCore import QDate
from datetime import datetime

class ExceptionDialog(QDialog):
    """Dialog for adding a single day or date range exception"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Exception Day(s)")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        # Radio buttons for single day vs range
        self.single_day_radio = QRadioButton("Single Day")
        self.date_range_radio = QRadioButton("Date Range")
        self.single_day_radio.setChecked(True)
        
        radio_group = QButtonGroup(self)
        radio_group.addButton(self.single_day_radio)
        radio_group.addButton(self.date_range_radio)
        
        layout.addWidget(QLabel("Exception Type:"))
        layout.addWidget(self.single_day_radio)
        layout.addWidget(self.date_range_radio)
        
        # Single day picker
        single_day_layout = QHBoxLayout()
        single_day_layout.addWidget(QLabel("Date:"))
        self.single_date_edit = QDateEdit()
        self.single_date_edit.setCalendarPopup(True)
        self.single_date_edit.setDate(QDate.currentDate())
        self.single_date_edit.setDisplayFormat("yyyy-MM-dd")
        single_day_layout.addWidget(self.single_date_edit)
        layout.addLayout(single_day_layout)
        
        # Date range pickers
        range_layout = QVBoxLayout()
        
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        start_layout.addWidget(self.start_date_edit)
        range_layout.addLayout(start_layout)
        
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        end_layout.addWidget(self.end_date_edit)
        range_layout.addLayout(end_layout)
        
        layout.addLayout(range_layout)
        
        # Connect radio buttons to enable/disable date pickers
        self.single_day_radio.toggled.connect(self._update_date_pickers)
        self.date_range_radio.toggled.connect(self._update_date_pickers)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("Add")
        ok_button.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initial state
        self._update_date_pickers()
    
    def _update_date_pickers(self):
        """Enable/disable date pickers based on selection"""
        is_single = self.single_day_radio.isChecked()
        self.single_date_edit.setEnabled(is_single)
        self.start_date_edit.setEnabled(not is_single)
        self.end_date_edit.setEnabled(not is_single)
    
    def _validate_and_accept(self):
        """Validate dates before accepting"""
        if self.date_range_radio.isChecked():
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            
            if start_date > end_date:
                QMessageBox.warning(self, "Invalid Range", 
                                   "Start date must be before or equal to end date.")
                return
        
        self.accept()
    
    def get_exception_string(self) -> str:
        """Get the exception string in the format expected by the system"""
        if self.single_day_radio.isChecked():
            return self.single_date_edit.date().toString("yyyy-MM-dd")
        else:
            start = self.start_date_edit.date().toString("yyyy-MM-dd")
            end = self.end_date_edit.date().toString("yyyy-MM-dd")
            return f"{start} to {end}"


class ResourceExceptionsWidget(QWidget):
    """Widget for managing resource exception days (holidays/leaves)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exceptions = []
        self._create_ui()
    
    def _create_ui(self):
        """Create widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel("Exception Days (Holidays/Leaves):")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        # List widget to display exceptions
        self.exceptions_list = QListWidget()
        self.exceptions_list.setMaximumHeight(150)
        layout.addWidget(self.exceptions_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Exception")
        self.add_button.clicked.connect(self._add_exception)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self._remove_exception)
        button_layout.addWidget(self.remove_button)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._clear_exceptions)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # Info label
        info_label = QLabel("Note: Exception days will exclude the resource from work on those dates,\naffecting billing and effort calculations.")
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
    
    def _add_exception(self):
        """Add a new exception day or range"""
        dialog = ExceptionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            exception_str = dialog.get_exception_string()
            if exception_str not in self.exceptions:
                self.exceptions.append(exception_str)
                self._update_list()
            else:
                QMessageBox.information(self, "Duplicate", 
                                       "This exception already exists.")
    
    def _remove_exception(self):
        """Remove selected exception"""
        current_row = self.exceptions_list.currentRow()
        if current_row >= 0:
            del self.exceptions[current_row]
            self._update_list()
    
    def _clear_exceptions(self):
        """Clear all exceptions"""
        if self.exceptions:
            reply = QMessageBox.question(self, "Clear All", 
                                        "Are you sure you want to clear all exception days?",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.exceptions.clear()
                self._update_list()
    
    def _update_list(self):
        """Update the list widget display"""
        self.exceptions_list.clear()
        for exception in sorted(self.exceptions):
            self.exceptions_list.addItem(exception)
    
    def set_exceptions(self, exceptions: list):
        """Set exceptions from external source"""
        self.exceptions = exceptions.copy() if exceptions else []
        self._update_list()
    
    def get_exceptions(self) -> list:
        """Get current exceptions"""
        return self.exceptions.copy()
