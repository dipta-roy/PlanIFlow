from constants.app_images import LOGO_BASE64
from constants.constants import APP_NAME, VERSION, AUTHOR, ABOUT_TEXT
from PyQt6.QtWidgets import (QMessageBox, QDialog, QHBoxLayout, QVBoxLayout, QLabel, 
                             QWidget, QTabWidget, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QScrollArea, QFrame, QPushButton)
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
        self._apply_stylesheet() # Ensure theme/font size is consistent
        current_index = self.tabs.currentIndex()
        
        if current_index == 0: # Task List
            self._update_task_tree()
        elif current_index == 1: # Gantt
            self._update_gantt_chart()
        elif current_index == 2: # Resources
            self._update_resource_summary()
        elif current_index == 3: # Baseline
             if hasattr(self, 'baseline_comparison'):
                self.baseline_comparison.refresh_baselines()
        elif current_index == 5: # EVM Analysis
             if hasattr(self, 'evm_tab'):
                self.evm_tab.refresh_data(silent=True)
        elif current_index == 6: # Kanban Board
             if hasattr(self, 'kanban_board'):
                self.kanban_board.refresh_board()
        elif current_index == 7: # Dashboard
             self._update_dashboard()
        
        self._update_window_title()
    
    def _on_tab_changed(self, index):
        """Handle tab switching to refresh views"""
        if index == 0:
            self._update_task_tree()
        elif index == 1:
            self._update_gantt_chart()
        elif index == 2:
            self._update_resource_summary()
        elif index == 3:
            if hasattr(self, 'baseline_comparison'):
                self.baseline_comparison.refresh_baselines()
        elif index == 5:
            if hasattr(self, 'evm_tab'):
                self.evm_tab.refresh_data(silent=True)
        elif index == 6:
            if hasattr(self, 'kanban_board'):
                self.kanban_board.refresh_board()
        elif index == 7:
            self._update_dashboard()

    def _update_gantt_chart(self):
        """Update Gantt chart"""    
        if hasattr(self, 'tabs') and self.tabs.currentIndex() != 1:
             return

        tasks = self.data_manager.get_all_tasks()
        self.gantt_chart.update_chart(tasks, self.data_manager)

    def _update_resource_summary(self):
        """Update resource summary"""
        if hasattr(self, 'tabs') and self.tabs.currentIndex() != 2:
            return
        # Ensure data manager ref is fresh
        self.resource_summary.data_manager = self.data_manager
        self.resource_summary._update_resource_delegates()
        self.resource_summary.update_summary()

    def _update_dashboard(self):
        """Update dashboard"""
        if hasattr(self, 'tabs') and self.tabs.currentIndex() != 7:
            return
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
        self.setWindowTitle(f"{APP_NAME} - {self.data_manager.project_name}")
        if hasattr(self, 'project_name_label'):
            self.project_name_label.setText(self.data_manager.project_name)

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
        font_size = getattr(self.data_manager.settings, 'app_font_size', 9)
        stylesheet = ThemeManager.get_stylesheet(self.dark_mode, font_size)
        self.setStyleSheet(stylesheet)

    def _show_reference_guide(self):
        """Show quick reference guide with shortcuts and legend"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Quick Reference Guide")
        dialog.resize(650, 400) # Set a balanced initial size
        
        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        
        # --- Legend Tab ---
        legend_tab = QWidget()
        legend_layout = QVBoxLayout(legend_tab)
        legend_layout.setContentsMargins(15, 0, 15, 15) # Consistent padding
        
        legend_text = (
            "<html><body style='margin: 0; padding: 0;'>"
            "<h3 style='margin-top: 0;'>Task Status Indicators</h3>"
            "<ul style='list-style-type: none; padding-left: 0;'>"
            "<li style='margin-bottom: 12px;'><b style='color: red; font-size: 14px;'>🔴 Overdue</b><br/>End date has passed and task is not 100% complete.</li>"
            "<li style='margin-bottom: 12px;'><b style='color: green; font-size: 14px;'>🟢 In Progress</b><br/>Task has started but is not yet finished.</li>"
            "<li style='margin-bottom: 12px;'><b style='color: grey; font-size: 14px;'>⚫ Upcoming</b><br/>Start date is in the future.</li>"
            "<li style='margin-bottom: 12px;'><b style='color: blue; font-size: 14px;'>🔵 Completed</b><br/>Task is 100% complete.</li>"
            "</ul>"
             "</body></html>"
        )
        legend_label = QLabel(legend_text)
        legend_label.setWordWrap(True)
        # Wrap in scroll area
        scroll = QScrollArea()
        scroll.setWidget(legend_label)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        legend_layout.addWidget(scroll)
        
        tabs.addTab(legend_tab, "📝 Status")

        # --- Dependencies Tab ---
        dep_tab = QWidget()
        dep_layout = QVBoxLayout(dep_tab)
        dep_layout.setContentsMargins(15, 5, 15, 15)
        
        dep_text = (
            "<html><body style='margin: 0; padding: 0;'>"
            "<h3 style='margin-top: 0;'>Dependency Types</h3>"
            "<p>Dependencies define the relationship between the start and end dates of tasks.</p>"
            "<ul style='list-style-type: none; padding-left: 0;'>"
            "<li style='margin-bottom: 15px;'><b>FS (Finish-to-Start)</b><br/>task B cannot start until task A finishes. This is the most common dependency type.</li>"
            "<li style='margin-bottom: 15px;'><b>SS (Start-to-Start)</b><br/>Task B cannot start until Task A starts. They can start simultaneously.</li>"
            "<li style='margin-bottom: 15px;'><b>FF (Finish-to-Finish)</b><br/>Task B cannot finish until Task A finishes. They can finish simultaneously.</li>"
            "<li style='margin-bottom: 15px;'><b>SF (Start-to-Finish)</b><br/>Task B cannot finish until Task A starts. This is rarely used.</li>"
            "</ul>"
            "<p><i>Note: You can add 'Lag' (delay) or 'Lead' (negative lag) to any dependency. Example:</i></p>"
            "<ul style='list-style-type: none; padding-left: 0;'>"
            "<li style='margin-bottom: 15px;'><b>1FS+5d</b> - Task B with ID : 2 uses Finish to Start (FS) dependency on task A with ID : 1 and will start 5 days after completing task A.</li>"
            "<li style='margin-bottom: 15px;'><b>1FS-3d</b> - Task B with ID : 2 uses Finish to Start (FS) dependency on task A with ID : 1 and will start 3 days before completing task A.</li>"
            "<li style='margin-bottom: 15px;'><b>1SS+5d</b> - Task B with ID : 2 uses Start to Start (FS) dependency on task A with ID : 1 and will start 5 days after starting task A.</li>"
            "<li style='margin-bottom: 15px;'><b>1SS-3d</b> - Task B with ID : 2 uses Start to Start (FS) dependency on task A with ID : 1 and will start 3 days before starting task A.</li>"
             "</ul>"
             "</body></html>"
        )
        dep_label = QLabel(dep_text)
        dep_label.setWordWrap(True)
        dep_scroll = QScrollArea()
        dep_scroll.setWidget(dep_label)
        dep_scroll.setWidgetResizable(True)
        dep_scroll.setFrameShape(QFrame.Shape.NoFrame)
        dep_layout.addWidget(dep_scroll)
        
        tabs.addTab(dep_tab, "🔗 Dependencies")

        # --- Shortcuts Tab ---
        shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_tab)
        
        shortcuts_table = QTableWidget()
        shortcuts_table.setColumnCount(2)
        shortcuts_table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        shortcuts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        shortcuts_table.verticalHeader().setVisible(False)
        shortcuts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        shortcuts_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        shortcuts_table.setAlternatingRowColors(True)

        shortcuts_data = [
            ("New Project", "Ctrl+N"),
            ("Open Project", "Ctrl+O"),
            ("Save Project", "Ctrl+S"),
            ("Close Project", "Ctrl+W"),
            ("Quit", "Ctrl+Q"),
            ("Add Task", "Ctrl+T"),
            ("Add Milestone", "Ctrl+M"),
            ("Add Subtask", "Ctrl+Shift+T"),
            ("Insert Task Above", "Ctrl+Shift+A"),
            ("Insert Task Below", "Ctrl+Shift+B"),
            ("Convert Task/Milestone", "Ctrl+Shift+M"),
            ("Undo", "Ctrl+Z"),
            ("Redo", "Ctrl+Y"),
            ("Indent Task", "Tab"),
            ("Outdent Task", "Shift+Tab"),
            ("Expand/Collapse", "Space"),
            ("Expand Selected", "+"),
            ("Collapse Selected", "-"),
            ("Formatting Bold", "Ctrl+B"),
            ("Formatting Italic", "Ctrl+I"),
            ("Formatting Underline", "Ctrl+U"),
            ("Clear Formatting", "Ctrl+Shift+X"),
            ("Refresh View", "F5"),
            ("Zoom In", "Ctrl +"),
            ("Zoom Out", "Ctrl -")
        ]
        
        shortcuts_table.setRowCount(len(shortcuts_data))
        for row, (action, key) in enumerate(shortcuts_data):
            shortcuts_table.setItem(row, 0, QTableWidgetItem(action))
            item_key = QTableWidgetItem(key)
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Make key bold
            font = item_key.font()
            font.setBold(True)
            item_key.setFont(font)
            shortcuts_table.setItem(row, 1, item_key)
            
        shortcuts_layout.addWidget(shortcuts_table)
        tabs.addTab(shortcuts_tab, "⌨️ Shortcuts")
        
        layout.addWidget(tabs)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
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
        about_box.setIconPixmap(pixmap)
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
            self.data_manager.recalculate_all_tasks() # Trigger full schedule recalculation
            self._apply_stylesheet() # Apply potential font size/theme changes
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
        
        # Ensure WBS column visibility and sort action visibility are respected after header update
        is_wbs_visible = self.toggle_wbs_action.isChecked()
        self.task_tree.setColumnHidden(3, not is_wbs_visible)
        if hasattr(self, 'sort_wbs_action'):
            self.sort_wbs_action.setVisible(is_wbs_visible)
        
        # Convert tasks
        self.data_manager.convert_all_tasks_to_unit(new_unit)
        
        # Refresh all views
        self._update_all_views()
