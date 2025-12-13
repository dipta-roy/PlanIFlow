"""ui_formatting.py - Formatting operations for tasks"""

from PyQt6.QtWidgets import QMessageBox, QColorDialog
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class FormattingMixin:
    """Mixin for task formatting operations in MainWindow"""
    
    def _update_formatting_buttons(self):
        """Update formatting button states based on selected task"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            # Disable all formatting buttons
            if hasattr(self, 'bold_action'):
                self.bold_action.setChecked(False)
                self.italic_action.setChecked(False)
                self.underline_action.setChecked(False)
            if hasattr(self, 'toolbar_bold_btn'):
                self.toolbar_bold_btn.setChecked(False)
                self.toolbar_italic_btn.setChecked(False)
                self.toolbar_underline_btn.setChecked(False)
            return
        
        # Get first selected task
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        
        if task:
            # Update button states
            if hasattr(self, 'bold_action'):
                self.bold_action.setChecked(getattr(task, 'font_bold', False))
                self.italic_action.setChecked(getattr(task, 'font_italic', False))
                self.underline_action.setChecked(getattr(task, 'font_underline', False))
            if hasattr(self, 'toolbar_bold_btn'):
                self.toolbar_bold_btn.setChecked(getattr(task, 'font_bold', False))
                self.toolbar_italic_btn.setChecked(getattr(task, 'font_italic', False))
                self.toolbar_underline_btn.setChecked(getattr(task, 'font_underline', False))
    
    def _toggle_bold(self):
        """Toggle bold formatting for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)
            if task:
                task.font_bold = not getattr(task, 'font_bold', False)
        
        self._update_all_views()
        self._update_formatting_buttons()
        self.status_label.setText(f"✓ Bold formatting toggled for {len(selected_items)} task(s)")
    
    def _toggle_italic(self):
        """Toggle italic formatting for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)
            if task:
                task.font_italic = not getattr(task, 'font_italic', False)
        
        self._update_all_views()
        self._update_formatting_buttons()
        self.status_label.setText(f"✓ Italic formatting toggled for {len(selected_items)} task(s)")
    
    def _toggle_underline(self):
        """Toggle underline formatting for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)
            if task:
                task.font_underline = not getattr(task, 'font_underline', False)
        
        self._update_all_views()
        self._update_formatting_buttons()
        self.status_label.setText(f"✓ Underline formatting toggled for {len(selected_items)} task(s)")
    
    def _change_font_color(self):
        """Change font color for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        # Get current color from first selected task
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        current_color = getattr(task, 'font_color', '#000000') if task else '#000000'
        
        # Open color dialog
        color = QColorDialog.getColor(QColor(current_color), self, "Select Font Color")
        if color.isValid():
            color_hex = color.name()
            for item in selected_items:
                task_id = item.data(2, Qt.ItemDataRole.UserRole)
                task = self.data_manager.get_task(task_id)
                if task:
                    task.font_color = color_hex
            
            self._update_all_views()
            self.status_label.setText(f"✓ Font color changed for {len(selected_items)} task(s)")
    
    def _change_background_color(self):
        """Change background color for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        # Get current color from first selected task
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        current_color = getattr(task, 'background_color', '#FFFFFF') if task else '#FFFFFF'
        
        # Open color dialog
        color = QColorDialog.getColor(QColor(current_color), self, "Select Background Color")
        if color.isValid():
            color_hex = color.name()
            for item in selected_items:
                task_id = item.data(2, Qt.ItemDataRole.UserRole)
                task = self.data_manager.get_task(task_id)
                if task:
                    task.background_color = color_hex
            
            self._update_all_views()
            self.status_label.setText(f"✓ Background color changed for {len(selected_items)} task(s)")
    
    def _change_font_size(self, size: int):
        """Change font size for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)
            if task:
                task.font_size = size
        
        self._update_all_views()
        self.status_label.setText(f"✓ Font size changed to {size}pt for {len(selected_items)} task(s)")
    
    def _change_font_family(self, family: str):
        """Change font family for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to format.")
            return
        
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)
            if task:
                task.font_family = family
        
        self._update_all_views()
        self.status_label.setText(f"✓ Font changed to {family} for {len(selected_items)} task(s)")
    
    def _clear_formatting(self):
        """Clear all formatting for selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more tasks to clear formatting.")
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Formatting",
            f"Clear all formatting for {len(selected_items)} selected task(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                task_id = item.data(2, Qt.ItemDataRole.UserRole)
                task = self.data_manager.get_task(task_id)
                if task:
                    task.font_family = None
                    task.font_size = None
                    task.font_color = '#000000'
                    task.background_color = '#FFFFFF'
                    task.font_bold = False
                    task.font_italic = False
                    task.font_underline = False
            
            self._update_all_views()
            self._update_formatting_buttons()
            self.status_label.setText(f"✓ Formatting cleared for {len(selected_items)} task(s)")
