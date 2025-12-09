from constants.app_images import LOGO_BASE64
from constants.constants import APP_NAME, VERSION, AUTHOR, ABOUT_TEXT
from PyQt6.QtWidgets import QMessageBox, QDialog, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QImage
from ui.themes import ThemeManager
from ui.ui_dashboard import update_dashboard
from ui.ui_dashboard import update_dashboard
from ui.ui_settings_dialog import SettingsDialog
from settings_manager.settings_manager import DurationUnit

class GeneralViewOperationsMixin:
    """Mixin for general view operations in MainWindow"""

    def _update_all_views(self):
        """Update all UI views"""
        self._update_task_tree()
        self._update_gantt_chart()
        
        # Update the data_manager reference in resource_summary
        self.resource_summary.data_manager = self.data_manager
        
        self.resource_summary._update_resource_delegates()
        self._update_resource_summary()
        self._update_dashboard()
        self._update_resource_filter()
        self._update_window_title()
        self.project_name_label.setText(self.data_manager.project_name)
        if hasattr(self, 'dashboard_project_name'):
            self.dashboard_project_name.setText(f"<h2>{self.data_manager.project_name}</h2>")
        
        # Refresh baseline comparison if it exists
        if hasattr(self, 'baseline_comparison'):
            self.baseline_comparison.refresh_baselines()
    
    def _update_gantt_chart(self):
        """Update Gantt chart"""
        tasks = self.data_manager.get_all_tasks()
        self.gantt_chart.update_chart(tasks, self.data_manager)
    
    def _update_resource_summary(self):
        """Update resource summary"""
        self.resource_summary.update_summary()

    def _update_dashboard(self):
        """Update dashboard"""
        update_dashboard(self)
    
    def _update_resource_filter(self):
        """Update resource filter dropdown"""
        current = self.resource_filter.currentText()
        self.resource_filter.clear()
        self.resource_filter.addItem("All Resources")
        
        for resource in self.data_manager.get_all_resources():
            self.resource_filter.addItem(resource.name)
        
        index = self.resource_filter.findText(current)
        if index >= 0:
            self.resource_filter.setCurrentIndex(index)

    def _update_window_title(self):
        """Update window title with project name"""
        self.setWindowTitle(f"PlanIFlow - {self.data_manager.project_name}")

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        if self.auto_refresh_action.isChecked():
            self.refresh_timer.start(10000)
            self.status_label.setText("✓ Auto-refresh enabled")
        else:
            self.refresh_timer.stop()
            self.status_label.setText("✓ Auto-refresh disabled")
    
    def _auto_refresh(self):
        """Auto-refresh with smarter logic to preserve tree state"""
        # Only refresh if user is not actively interacting
        if not self.task_tree.hasFocus():
            # Only update charts and dashboard, skip tree to preserve expansion
            # self._update_gantt_chart() # Temporarily disable auto-refresh for Gantt chart to prevent resize
            self._update_dashboard()
            self._update_resource_summary()

    def _toggle_dark_mode(self):
        """Toggle dark/light mode"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            ThemeManager.apply_dark_mode()
        else:
            ThemeManager.apply_light_mode()
        
        self._apply_stylesheet()
        self.gantt_chart.set_dark_mode(self.dark_mode)
        self._update_task_tree()  # Refresh colors

    def _toggle_gantt_summary_tasks(self, state):
        """Toggle visibility of summary tasks in Gantt chart"""
        show = state == Qt.CheckState.Checked.value
        self.gantt_chart.set_show_summary_tasks(show)
        self.status_label.setText(f"✓ Summary tasks visibility: {'Shown' if show else 'Hidden'}")

    def _toggle_gantt_critical_path(self, state):
        """Toggle visibility of critical path in Gantt chart"""
        show = state == Qt.CheckState.Checked.value
        self.gantt_chart.set_show_critical_path(show)
        self.status_label.setText(f"✓ Critical path visibility: {'Shown' if show else 'Hidden'}")

    def _set_gantt_axis_scale(self, scale: str):
        """Set the X-axis scale for the Gantt chart"""
        self.gantt_chart.set_axis_scale(scale)
        self.status_label.setText(f"✓ Gantt chart axis scale set to: {scale}")
        self._update_gantt_chart()

    def _apply_stylesheet(self):
        """Apply custom stylesheet"""
        stylesheet = ThemeManager.get_stylesheet(self.dark_mode)
        self.setStyleSheet(stylesheet)

    def _show_status_legend(self):
        """Show status indicator legend"""
        # Use QDialog instead of QMessageBox for custom sizing
        legend = QDialog(self)
        legend.setWindowTitle("Legends")
        legend.setMinimumWidth(500)
        
        layout = QHBoxLayout(legend)
        label = QLabel()
        label.setText(
            "<h3>Task Status Indicators</h3>"
            "<p><b style='color: red;'>🔴 Overdue:</b> End date passed and not 100% complete</p>"
            "<p><b style='color: green;'>🟢 In Progress:</b> Started but not yet finished</p>"
            "<p style='color: grey;'><b>⚫ Upcoming:</b> Not yet started</p>"
            "<p><b style='color: blue;'>🔵 Completed:</b> 100% complete</p>"
            "<h3>Dependency Types</h3>"
            "<p><b>FS (Finish-to-Start):</b> Task B starts after Task A finishes</p>"
            "<p><b>SS (Start-to-Start):</b> Task B starts when Task A starts</p>"
            "<p><b>FF (Finish-to-Finish):</b> Task B finishes when Task A finishes</p>"
            "<p><b>SF (Start-to-Finish):</b> Task B finishes when Task A starts</p>"
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        
        legend.exec()
    
    def _show_about(self):
        """Show about dialog"""
        about_box = QMessageBox(self)
        about_box.setWindowTitle(f"About {APP_NAME} - Project Planner")

        # Decode the base64 logo
        byte_array = QByteArray.fromBase64(LOGO_BASE64.encode('utf-8'))
        image = QImage()
        image.loadFromData(byte_array, "PNG")
        
        # Scale the image down to a reasonable size for the about dialog (e.g., 64x64)
        pixmap = QPixmap.fromImage(image).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Create a QLabel for the logo
        logo_label = QLabel()
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Create a QLabel for the app name
        app_name_label = QLabel(f"<h2>{APP_NAME} - Project Planner</h2>")
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Create a widget to hold the logo and app name
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.addWidget(logo_label)
        header_layout.addWidget(app_name_label)
        header_layout.addStretch(1) # Add a stretch to push content to left
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        about_box.setMinimumWidth(600) # Set a minimum width
        
        # Set the custom widget as the message box's layout
        # This requires a bit of a workaround since QMessageBox doesn't directly support custom widgets in its layout
        # We can set the icon and then manipulate the text to align it.
        # Alternatively, for more complex layouts, a custom QDialog would be better.
        # For this task, setting the icon and adjusting text is sufficient.
        
        about_box.setIconPixmap(pixmap)
        
        # Reconstruct the text to include the app name next to the icon
        # The previous app_name_label is not directly used in the QMessageBox text,
        # but the pixmap is set as the icon.
        about_box.setText(
            f"<h2>{APP_NAME}</h2>"
            f"<p>App Version: {VERSION}</p>"
            f"<p>Developed by: <b>{AUTHOR}</b></p>" 
            f"<p>{ABOUT_TEXT}</p>"
        )
        
        about_box.exec()

    def _show_settings_dialog(self, tab_index=0):
        """Show unified settings dialog"""
        dialog = SettingsDialog(self, self.data_manager)
        dialog.tabs.setCurrentIndex(tab_index)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._update_all_views()
            self.status_label.setText("Settings updated")

    def _show_duration_unit_settings(self):
        """Show duration unit settings (now via unified dialog)"""
        self._show_settings_dialog(2)

    def _show_date_format_settings(self):
        """Show date format settings dialog"""
        self._show_settings_dialog(2)
                    
    def _show_project_settings_dialog(self):
        """Show project settings dialog"""
        self._show_settings_dialog(0)
    
    def _show_calendar_settings(self):
        """Show calendar settings dialog"""
        self._show_settings_dialog(1)

    def _on_settings_changed(self, old_unit: DurationUnit, new_unit: DurationUnit):
        """Handle settings changes"""
        # Update task tree header
        header_labels = [
            "Schedule Type", "Status", "ID", "WBS", "Task Name", "Start Date", "End Date", 
            self.data_manager.settings.get_duration_label(),
            "% Complete", "Dependencies", "Resources", "Notes"
        ]
        self.task_tree.setHeaderLabels(header_labels)
        
        # Ensure WBS column visibility is respected after header update
        self.task_tree.setColumnHidden(3, not self.toggle_wbs_action.isChecked())
        
        # Convert tasks
        self.data_manager.convert_all_tasks_to_unit(new_unit)
        
        # Refresh all views
        self._update_all_views()
