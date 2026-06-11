import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QPushButton, QDoubleSpinBox, QSpinBox,
                             QLineEdit, QTextEdit, QFormLayout, QWidget, QMessageBox)
from PyQt6.QtCore import Qt
from ui.ui_tasks import CheckableComboBox
from settings_manager.settings_manager import DurationUnit
from data_manager.models import DependencyType

class BulkEditDialog(QDialog):
    """Dialog for bulk editing properties of multiple selected tasks"""
    
    def __init__(self, parent, data_manager, task_count: int):
        super().__init__(parent)
        self.data_manager = data_manager
        self.task_count = task_count
        
        self.setWindowTitle("Bulk Edit Tasks")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # Info Header
        info_label = QLabel(f"Modifying <b>{self.task_count}</b> selected tasks.<br>"
                            "Check the box next to each field you want to bulk update.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addSpacing(10)
        
        form_layout = QFormLayout()
        
        # Duration
        self.duration_cb = QCheckBox("Duration:")
        duration_unit_str = self.data_manager.settings.duration_unit.value
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0.0, 10000.0)
        self.duration_input.setDecimals(1 if self.data_manager.settings.duration_unit == DurationUnit.HOURS else 0)
        self.duration_input.setValue(1.0)
        self.duration_input.setSuffix(f" {duration_unit_str}")
        self.duration_input.setEnabled(False)
        self.duration_cb.toggled.connect(self.duration_input.setEnabled)
        form_layout.addRow(self.duration_cb, self.duration_input)
        
        # % Complete
        self.percent_cb = QCheckBox("% Complete:")
        self.percent_input = QSpinBox()
        self.percent_input.setRange(0, 100)
        self.percent_input.setValue(0)
        self.percent_input.setSuffix("%")
        self.percent_input.setEnabled(False)
        self.percent_cb.toggled.connect(self.percent_input.setEnabled)
        form_layout.addRow(self.percent_cb, self.percent_input)
        
        # Dependencies (Predecessors)
        self.dep_cb = QCheckBox("Predecessors:")
        self.dep_input = QLineEdit()
        self.dep_input.setPlaceholderText("e.g. 1, 2FS+3d")
        self.dep_input.setEnabled(False)
        self.dep_cb.toggled.connect(self.dep_input.setEnabled)
        form_layout.addRow(self.dep_cb, self.dep_input)
        
        # Resources
        self.res_cb = QCheckBox("Resources:")
        self.res_input = CheckableComboBox()
        # Get all resource names and add to checkable combobox
        resource_names = sorted([r.name for r in self.data_manager.get_all_resources()])
        self.res_input.addItems(resource_names)
        self.res_input.setEnabled(False)
        self.res_cb.toggled.connect(self.res_input.setEnabled)
        form_layout.addRow(self.res_cb, self.res_input)
        
        # Notes
        self.notes_cb = QCheckBox("Notes:")
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setEnabled(False)
        self.notes_cb.toggled.connect(self.notes_input.setEnabled)
        form_layout.addRow(self.notes_cb, self.notes_input)
        
        layout.addLayout(form_layout)
        layout.addSpacing(15)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def get_updates(self) -> dict:
        """Returns the dictionary of enabled updates"""
        updates = {}
        if self.duration_cb.isChecked():
            updates['duration'] = self.duration_input.value()
        if self.percent_cb.isChecked():
            updates['percent_complete'] = self.percent_input.value()
        if self.dep_cb.isChecked():
            updates['predecessors'] = self._parse_predecessors(self.dep_input.text())
        if self.res_cb.isChecked():
            updates['assigned_resources'] = [(name, 100) for name in self.res_input.get_checked_items()]
        if self.notes_cb.isChecked():
            updates['notes'] = self.notes_input.toPlainText().strip()
        return updates

    def _parse_predecessors(self, text: str) -> list:
        new_predecessors = []
        if text.strip():
            for pred_str in text.split(','):
                pred_str = pred_str.strip()
                if not pred_str:
                    continue

                lag_days = 0
                dep_type = DependencyType.FS.name

                match = re.match(r'(\d+)\s*([A-Z]{2})?\s*(?:([+-])\s*(\d+)\s*(d)?)?', pred_str)
                if match:
                    pred_id = int(match.group(1))
                    if match.group(2):
                        dep_type = match.group(2)
                    
                    if match.group(3) and match.group(4):
                        lag_days = int(match.group(4))
                        if match.group(3) == '-':
                            lag_days = -lag_days
                    
                    new_predecessors.append((pred_id, dep_type, lag_days))
        return new_predecessors
