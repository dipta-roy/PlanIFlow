from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLineEdit, QDoubleSpinBox, QPushButton)
from data_manager.models import Resource
from ui.ui_resource_exceptions_widget import ResourceExceptionsWidget

class ResourceDialog(QDialog):
    """Dialog for adding/editing resources"""
    
    def __init__(self, parent, data_manager, resource: Resource = None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.resource = resource
        self.is_edit = resource is not None
        
        self.setWindowTitle("Edit Resource" if self.is_edit else "Add Resource")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        
        self._create_ui()
        
        if self.is_edit:
            self._populate_fields()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Resource Name:", self.name_edit)
        
        # Max Hours per Day
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0, 24)
        self.hours_spin.setValue(8.0)
        self.hours_spin.setSuffix(" hours")
        form_layout.addRow("Max Hours/Day:", self.hours_spin)

        # Billing Rate
        self.billing_rate_spin = QDoubleSpinBox()
        self.billing_rate_spin.setRange(0.0, 10000.0)
        self.billing_rate_spin.setDecimals(2)
        
        symbol = self.data_manager.settings.currency.symbol
        self.billing_rate_spin.setPrefix(f"{symbol} ")
        self.billing_rate_spin.setSuffix("/hr")
        self.billing_rate_spin.setValue(100.0)
        form_layout.addRow("Billing Rate:", self.billing_rate_spin)
        
        layout.addLayout(form_layout)
        
        # Exception Days Widget
        self.exceptions_widget = ResourceExceptionsWidget(self)
        layout.addWidget(self.exceptions_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields when editing"""
        self.name_edit.setText(self.resource.name)
        self.hours_spin.setValue(self.resource.max_hours_per_day)
        self.billing_rate_spin.setValue(self.resource.billing_rate)
        self.exceptions_widget.set_exceptions(self.resource.exceptions)
    
    def get_resource_data(self):
        """Get resource data from form"""
        billing_rate_value = self.billing_rate_spin.value()

        return {
            'name': self.name_edit.text(),
            'max_hours_per_day': self.hours_spin.value(),
            'exceptions': self.exceptions_widget.get_exceptions(),
            'billing_rate': billing_rate_value
        }
