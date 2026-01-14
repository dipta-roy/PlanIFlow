
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QMenu, QTextEdit, QLabel, QDialog)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from data_manager.models import Resource
from ui.ui_resource_dialog import ResourceDialog
from command_manager.commands import AddResourceCommand, EditResourceCommand


class ResourceSheet(QWidget):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.parent_window = parent

        layout = QVBoxLayout(self)
        
        # Resource table
        self.resource_table = QTableWidget()
        self.resource_table.setColumnCount(8) 
        symbol = self.data_manager.settings.currency.symbol
        self.resource_table.setHorizontalHeaderLabels([
            "Resource Name", "Max Hours/Day", "Total Hours", 
            "Tasks Assigned", f"Billing Rate ({symbol}/hr)", f"Total Amount ({symbol})", "Exceptions", "Status"
        ])
        # Add tooltips to headers
        header = self.resource_table.horizontalHeader()
        tooltips = [
            "The name of the resource.",
            "The maximum number of hours the resource can work per day.",
            "The total hours assigned to the resource across all tasks.",
            "The number of tasks assigned to the resource.",
            "The billing rate for the resource in currency per hour.",
            "The total cost for the resource (Total Hours * Billing Rate).",
            "Dates or date ranges when the resource is unavailable.",
            "The allocation status of the resource (e.g., OK, Over-allocated)."
        ]
        for i in range(len(tooltips)):
            self.resource_table.horizontalHeaderItem(i).setToolTip(tooltips[i])
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setStretchLastSection(True)
        self.resource_table.doubleClicked.connect(self._edit_resource_dialog)
        self.resource_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.resource_table.customContextMenuRequested.connect(self._show_resource_context_menu)

        # Column resizing logic
        header = self.resource_table.horizontalHeader()
        # First, resize all sections to their content
        for i in range(self.resource_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Then, allow interactive resizing for all columns except the last (Status)
        for i in range(self.resource_table.columnCount()):
            if i != 7:  # All columns except Status
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        # Make Status column (index 7) stretch to fill remaining space
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)

        # Set default width for Resource Name column
        self.resource_table.setColumnWidth(0, 250)
        self.resource_table.setColumnWidth(1, 100)
        self.resource_table.setColumnWidth(2, 100)
        self.resource_table.setColumnWidth(3, 100)
        self.resource_table.setColumnWidth(4, 120)
        self.resource_table.setColumnWidth(5, 120)
        self.resource_table.setColumnWidth(6, 900)
        self.resource_table.setColumnWidth(7, 100)
        
        #layout.addWidget(QLabel("<h3>Resource Allocation</h3>"))
        layout.addWidget(self.resource_table)
        
        # Warnings
        self.resource_warnings = QTextEdit()
        self.resource_warnings.setReadOnly(True)
        self.resource_warnings.setMaximumHeight(150)
        layout.addWidget(QLabel("<h3>⚠️ Over-Allocation Warnings</h3>"))
        layout.addWidget(self.resource_warnings)

    def _show_resource_context_menu(self, position):
        """Show context menu on resource table right-click"""
        item = self.resource_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        resource_name = self.resource_table.item(row, 0).text()
        menu = QMenu(self)
        edit_action = QAction("✏️ Edit Resource", self)
        edit_action.triggered.connect(self._edit_resource_dialog)
        menu.addAction(edit_action)
        delete_action = QAction("🗑️ Delete Resource", self)
        delete_action.triggered.connect(self._delete_resource)
        menu.addAction(delete_action)
        menu.exec(self.resource_table.mapToGlobal(position))

    def _edit_resource_dialog(self):
        """Show edit resource dialog"""
        selected_items = self.resource_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a resource to edit.")
            return
        
        row = selected_items[0].row()
        resource_name = self.resource_table.item(row, 0).text()
        resource = self.data_manager.get_resource(resource_name)
        
        if resource:
            dialog = ResourceDialog(self, self.data_manager, resource)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                resource_data = dialog.get_resource_data()
                resource_data['billing_rate'] = float(resource_data.get('billing_rate', 0.0))
                
                def on_success():
                    self.parent_window._update_all_views()
                    new_name = resource_data['name']
                    self.parent_window.status_label.setText(f"Resource '{new_name}' updated")
                
                command = EditResourceCommand(self.data_manager, resource_name, resource_data, on_success_callback=on_success)
                
                if not self.parent_window.command_manager.execute_command(command):
                    QMessageBox.warning(self, "Error", "Failed to update resource. Name collision?")

    def _add_resource_dialog(self):
        """Show add resource dialog"""
        dialog = ResourceDialog(self, self.data_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            resource_data = dialog.get_resource_data()
            
            # Ensure proper types for command
            resource_data['billing_rate'] = float(resource_data.get('billing_rate', 0.0))

            def on_success():
                self.parent_window._update_all_views()
                self.parent_window.status_label.setText(f"Resource '{resource_data['name']}' added successfully")

            command = AddResourceCommand(self.data_manager, resource_data, on_success_callback=on_success)
            
            if not self.parent_window.command_manager.execute_command(command):
                 QMessageBox.warning(self, "Duplicate Resource", 
                                   "A resource with this name already exists.")

    def _delete_resource(self):
        """Delete selected resource"""
        selected_items = self.resource_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a resource to delete.")
            return
        
        row = selected_items[0].row()
        resource_name = self.resource_table.item(row, 0).text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete resource '{resource_name}'?",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_resource(resource_name)
            self.parent_window._update_all_views()
            self.parent_window.status_label.setText("Resource deleted")

    def _update_resource_delegates(self):
        """Update the resource delegate with the latest list of resource names"""
        resource_names = [r.name for r in self.data_manager.get_all_resources()]
        if hasattr(self.parent_window, 'resource_delegate'):
            self.parent_window.resource_delegate.update_resource_list(resource_names)

    def update_summary(self):
        """Update resource summary"""
        # Refresh header labels to update currency symbols
        symbol = self.data_manager.settings.currency.symbol
        self.resource_table.setHorizontalHeaderLabels([
            "Resource Name", "Max Hours/Day", "Total Hours", 
            "Tasks Assigned", f"Billing Rate ({symbol}/hr)", f"Total Amount ({symbol})", "Exceptions", "Status"
        ])

        self.resource_table.setRowCount(0)
        
        allocation = self.data_manager.get_resource_allocation()
        
        for resource in self.data_manager.get_all_resources():
            row = self.resource_table.rowCount()
            self.resource_table.insertRow(row)
            
            alloc = allocation.get(resource.name, {})
            total_hours = alloc.get('total_hours', 0)
            tasks_assigned = alloc.get('tasks_assigned', 0)
            
            # Determine status
            status = "✓ OK"
            warnings = self.data_manager.check_resource_overallocation()
            if resource.name in warnings:
                status = "⚠️ Over-allocated"
            
            self.resource_table.setItem(row, 0, QTableWidgetItem(resource.name))
            self.resource_table.setItem(row, 1, QTableWidgetItem(str(resource.max_hours_per_day)))
            self.resource_table.setItem(row, 2, QTableWidgetItem(f"{total_hours:.1f}"))
            self.resource_table.setItem(row, 3, QTableWidgetItem(str(tasks_assigned)))
            self.resource_table.setItem(row, 4, QTableWidgetItem(f"{symbol}{resource.billing_rate:.2f}"))
            self.resource_table.setItem(row, 5, QTableWidgetItem(f"{symbol}{alloc.get('total_amount', 0.0):.2f}"))
            self.resource_table.setItem(row, 6, QTableWidgetItem(", ".join(resource.exceptions))) 
            self.resource_table.setItem(row, 7, QTableWidgetItem(status))
        
        # Update warnings
        warnings = self.data_manager.check_resource_overallocation()
        if warnings:
            warning_text = "<h4 style='color: orange;'>Over-Allocation Detected:</h4>"
            for resource_name, warning_list in warnings.items():
                warning_text += f"<b>{resource_name}:</b><ul>"
                for warning in warning_list[:5]:
                    warning_text += f"<li>{warning}</li>"
                if len(warning_list) > 5:
                    warning_text += f"<li><i>...and {len(warning_list) - 5} more</i></li>"
                warning_text += "</ul>"
            self.resource_warnings.setHtml(warning_text)
        else:
            self.resource_warnings.setHtml("<p style='color: green;'>✓ No over-allocation issues detected.</p>")
