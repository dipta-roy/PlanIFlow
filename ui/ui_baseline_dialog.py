"""
Baseline Management Dialog - Create, delete, and manage project baselines
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QLabel, QMessageBox,
                             QInputDialog, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt



class BaselineDialog(QDialog):
    """Dialog for managing project baselines"""
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setWindowTitle("Baseline Management")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self._create_ui()
        self._refresh_baseline_list()
    
    def _create_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("<h2>Project Baselines</h2>")
        layout.addWidget(header_label)
        
        # Info label
        info_label = QLabel("Baselines capture a snapshot of your project at a specific point in time.\n"
                           "You can create up to 3 baselines and compare them against the current project state.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Baseline list
        list_group = QGroupBox("Existing Baselines")
        list_layout = QVBoxLayout(list_group)
        
        self.baseline_list = QListWidget()
        self.baseline_list.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.baseline_list)
        
        layout.addWidget(list_group)
        
        # Baseline details
        self.details_group = QGroupBox("Baseline Details")
        details_layout = QFormLayout(self.details_group)
        
        self.name_label = QLabel("-")
        self.date_label = QLabel("-")
        self.task_count_label = QLabel("-")
        
        details_layout.addRow("Name:", self.name_label)
        details_layout.addRow("Created:", self.date_label)
        details_layout.addRow("Tasks Captured:", self.task_count_label)
        
        layout.addWidget(self.details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("Create New Baseline")
        self.create_btn.clicked.connect(self._create_baseline)
        button_layout.addWidget(self.create_btn)
        
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename_baseline)
        self.rename_btn.setEnabled(False)
        button_layout.addWidget(self.rename_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_baseline)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _refresh_baseline_list(self):
        """Refresh the baseline list"""
        self.baseline_list.clear()
        
        baselines = self.data_manager.get_all_baselines()
        
        for baseline in baselines:
            item_text = f"{baseline.name} - Created: {baseline.created_date.strftime('%Y-%m-%d %H:%M')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, baseline.name)
            self.baseline_list.addItem(item)
        
        # Update create button state
        self.create_btn.setEnabled(len(baselines) < 3)
        
        if len(baselines) >= 3:
            self.create_btn.setText("Maximum Baselines Reached (3/3)")
        else:
            self.create_btn.setText(f"Create New Baseline ({len(baselines)}/3)")
    
    def _on_selection_changed(self):
        """Handle baseline selection change"""
        selected_items = self.baseline_list.selectedItems()
        
        if selected_items:
            baseline_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
            baseline = self.data_manager.get_baseline(baseline_name)
            
            if baseline:
                self.name_label.setText(baseline.name)
                self.date_label.setText(baseline.created_date.strftime('%Y-%m-%d %H:%M:%S'))
                self.task_count_label.setText(str(len(baseline.snapshots)))
                
                self.rename_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
        else:
            self.name_label.setText("-")
            self.date_label.setText("-")
            self.task_count_label.setText("-")
            
            self.rename_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def _create_baseline(self):
        """Create a new baseline"""
        # Check if there are tasks
        if not self.data_manager.tasks:
            QMessageBox.warning(self, "No Tasks", 
                              "Cannot create a baseline because there are no tasks in the project.")
            return
        
        # Get baseline name from user
        baselines = self.data_manager.get_all_baselines()
        default_name = f"Baseline {len(baselines) + 1}"
        
        name, ok = QInputDialog.getText(self, "Create Baseline", 
                                       "Enter baseline name:",
                                       text=default_name)
        
        if ok and name:
            # Create the baseline
            if self.data_manager.create_baseline(name):
                QMessageBox.information(self, "Success", 
                                      f"Baseline '{name}' created successfully!\n"
                                      f"Captured {len(self.data_manager.tasks)} tasks.")
                self._refresh_baseline_list()
            else:
                QMessageBox.warning(self, "Error", 
                                  "Failed to create baseline. The name may already exist or "
                                  "the maximum number of baselines (3) has been reached.")
    
    def _rename_baseline(self):
        """Rename the selected baseline"""
        selected_items = self.baseline_list.selectedItems()
        
        if not selected_items:
            return
        
        old_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        new_name, ok = QInputDialog.getText(self, "Rename Baseline", 
                                           "Enter new baseline name:",
                                           text=old_name)
        
        if ok and new_name and new_name != old_name:
            if self.data_manager.rename_baseline(old_name, new_name):
                QMessageBox.information(self, "Success", 
                                      f"Baseline renamed to '{new_name}'.")
                self._refresh_baseline_list()
            else:
                QMessageBox.warning(self, "Error", 
                                  "Failed to rename baseline. The new name may already exist.")
    
    def _delete_baseline(self):
        """Delete the selected baseline"""
        selected_items = self.baseline_list.selectedItems()
        
        if not selected_items:
            return
        
        baseline_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion",
                                    f"Are you sure you want to delete baseline '{baseline_name}'?\n"
                                    "This action cannot be undone.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.data_manager.delete_baseline(baseline_name):
                QMessageBox.information(self, "Success", 
                                      f"Baseline '{baseline_name}' deleted successfully.")
                self._refresh_baseline_list()
                self._on_selection_changed()  # Clear details
            else:
                QMessageBox.warning(self, "Error", 
                                  "Failed to delete baseline.")
