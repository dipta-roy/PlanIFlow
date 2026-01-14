from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
import traceback
from data_manager.models import Task, ScheduleType, Resource
from ui.ui_task_dialog import TaskDialog
from ui.ui_resource_dialog import ResourceDialog
from command_manager.commands import EditTaskCommand, DeleteTaskCommand, AddTaskCommand, MoveTaskCommand
from constants.constants import ERROR_TITLE, ERROR_GENERIC_MESSAGE

class TaskOperationsMixin:
    """Mixin for task and resource operations in MainWindow"""

    def _quick_add_task(self):
        """Quickly add a task with just the name from the quick add input field"""
        task_name = self.quick_add_task_input.text().strip()
        
        if not task_name:
            return
        
        # Create task with default values based on calendar settings
        now = datetime.now()
        start_hour, start_minute = self.data_manager.calendar_manager.get_working_start_time()
        end_hour, end_minute = self.data_manager.calendar_manager.get_working_end_time()
        
        
        if self.data_manager.settings.project_start_date:
            base_date = self.data_manager.settings.project_start_date
        else:
            base_date = now
            
        start_date = base_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_date = base_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        task = Task(
            name=task_name,
            start_date=start_date,
            end_date=end_date,
            percent_complete=0,
            predecessors=[],
            assigned_resources=[],
            notes="",
            schedule_type=ScheduleType.AUTO_SCHEDULED,
            font_family='Arial',
            font_size=10,
            font_color='#000000',
            background_color='#FFFFFF'
        )
        
        command_data = task.to_dict()
        
        def on_success():
            self._update_all_views()
            self.status_label.setText(f"Task '{task.name}' added successfully")
            self.quick_add_task_input.clear()
            
        command = AddTaskCommand(self.data_manager, command_data, mode='append', on_success_callback=on_success)
        
        if not self.command_manager.execute_command(command):
            QMessageBox.warning(self, "Validation Error", 
                              "Task could not be added.")
    
    def _add_task_dialog(self):
        """Show add task dialog"""
        dialog = TaskDialog(self, self.data_manager, is_milestone=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            # Create a throwaway task to ensure all defaults and formats are correct before serialization
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                is_milestone=task_data.get('is_milestone', False),
                schedule_type=task_data['schedule_type'],
                font_family=task_data.get('font_family', 'Arial'),
                font_size=task_data.get('font_size', 10),
                font_color=task_data.get('font_color', '#000000'),
                background_color=task_data.get('background_color', '#FFFFFF'),
                font_bold=task_data.get('font_bold', None),
                font_italic=task_data.get('font_italic', None),
                font_underline=task_data.get('font_underline', False)
            )
            
            # Serialize for command
            command_data = task.to_dict()
            
            def on_success():
                self._update_all_views()
                self.status_label.setText(f"Task '{task.name}' added successfully")
                
            command = AddTaskCommand(self.data_manager, command_data, mode='append', on_success_callback=on_success)
            
            if not self.command_manager.execute_command(command):
                 QMessageBox.warning(self, "Validation Error", 
                                   "Task has circular dependencies or invalid dates.")
    
    def _add_subtask_dialog(self):
        """Show add subtask dialog"""
        # Get selected task
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a parent task first.")
            return
        
        parent_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        parent_task = self.data_manager.get_task(parent_id)
        
        if not parent_task:
            return
        
        dialog = TaskDialog(self, self.data_manager, parent_task=parent_task, is_milestone=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                schedule_type=task_data['schedule_type'],
                font_family=task_data.get('font_family', 'Arial'),
                font_size=task_data.get('font_size', 10),
                font_color=task_data.get('font_color', '#000000'),
                background_color=task_data.get('background_color', '#FFFFFF'),
                font_bold=task_data.get('font_bold', None),
                font_italic=task_data.get('font_italic', None),
                font_underline=task_data.get('font_underline', False)
            )
            
            command_data = task.to_dict()

            def on_success():
                self._update_all_views()
                self.status_label.setText(f"Subtask '{task.name}' added to '{parent_task.name}'")

            command = AddTaskCommand(self.data_manager, command_data, mode='append', parent_id=parent_id, on_success_callback=on_success)
            
            if not self.command_manager.execute_command(command):
                QMessageBox.warning(self, "Validation Error", 
                                  "Task has circular dependencies or invalid dates.")
    
    def _edit_task_dialog(self):
        """Show edit task dialog using Command pattern"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a task to edit.")
            return
        
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        # Getting the live object to snapshot previous state
        task = self.data_manager.get_task(task_id)
        
        if task:
            try:
                # Capture old state for Undo
                old_task_data = task.to_dict()

                dialog = TaskDialog(self, self.data_manager, task, is_milestone=task.is_milestone)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    task_data = dialog.task_data
                    
                    updated_task = Task(
                        name=task_data['name'],
                        start_date=task_data['start_date'],
                        end_date=task_data['end_date'],
                        percent_complete=task_data['percent_complete'],
                        predecessors=task_data['predecessors'],
                        assigned_resources=task_data['assigned_resources'],
                        notes=task_data['notes'],
                        task_id=task.id,
                        is_milestone=task_data.get('is_milestone', task.is_milestone),
                        is_summary=task.is_summary, # Summary status is usually structural
                        schedule_type=task_data['schedule_type'],
                        font_family=task_data.get('font_family', 'Arial'),
                        font_size=task_data.get('font_size', 10),
                        font_color=task_data.get('font_color', '#000000'),
                        background_color=task_data.get('background_color', '#FFFFFF'),
                        font_bold=task_data.get('font_bold', None),
                        font_italic=task_data.get('font_italic', None),
                        font_underline=task_data.get('font_underline', False)
                    )
                    
                    new_task_data = updated_task.to_dict()

                    # Define callback for success
                    def on_success():
                        self._update_all_views()
                        self.status_label.setText(f"✓ Task '{updated_task.name}' updated successfully")

                    command = EditTaskCommand(
                        self.data_manager, 
                        task_id, 
                        old_task_data, 
                        new_task_data, 
                        on_success_callback=on_success
                    )

                    if not self.command_manager.execute_command(command):
                        QMessageBox.warning(self, "Validation Error", 
                                          "Task update failed due to circular dependencies.")

            except Exception as e:
                QMessageBox.critical(self, ERROR_TITLE, f"{ERROR_GENERIC_MESSAGE}\n\nDetails: {e}")
                traceback.print_exc()
    
    def _delete_task(self):
        """Delete selected task using Command pattern"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a task to delete.")
            return
        
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        
        if task:
            # Check if it has subtasks
            children = self.data_manager.get_child_tasks(task_id)
            msg = f"Delete task '{task.name}'?"
            if children:
                msg = f"Delete task '{task.name}' and all {len(children)} subtask(s)?"
            
            reply = QMessageBox.question(self, "Confirm Delete", msg,
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                # Callback to refresh UI on success
                def on_success():
                    self._update_all_views()
                    self.status_label.setText("Task deleted")

                command = DeleteTaskCommand(self.data_manager, task_id, on_success_callback=on_success)
                
                if not self.command_manager.execute_command(command):
                    QMessageBox.warning(self, "Error", "Failed to delete task.")
    
    def _indent_task(self):
        """Indent selected task (make it a subtask of previous sibling in visual order)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to indent.")
            return
        
        current_item = selected_items[0]
        task_id = current_item.data(2, Qt.ItemDataRole.UserRole)
        
        if task_id is None:
            QMessageBox.warning(self, "Error", "Could not identify selected task.")
            return
        
        task = self.data_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Selected task not found.")
            return
        
        # Get the parent item (None if top-level)
        parent_item = current_item.parent()
        
        # Find the index of current item
        if parent_item is None:
            # Top-level item
            root = self.task_tree.invisibleRootItem()
            index = root.indexOfChild(current_item)
            
            if index == 0:
                QMessageBox.information(self, "Cannot Indent", 
                                      f"Cannot indent '{task.name}'.\n\n"
                                      "This is the first task. There is no task above it to indent under.")
                return
            
            # Get the previous sibling item
            previous_item = root.child(index - 1)
        else:
            # Child item
            index = parent_item.indexOfChild(current_item)
            
            if index == 0:
                QMessageBox.information(self, "Cannot Indent", 
                                      f"Cannot indent '{task.name}'.\n\n"
                                      "This is the first subtask under its parent.\n"
                                      "There is no task above it to indent under.")
                return
            
            # Get the previous sibling item
            previous_item = parent_item.child(index - 1)
        
        # Get the task ID of the previous item
        previous_task_id = previous_item.data(2, Qt.ItemDataRole.UserRole)
        if previous_task_id is None:
            QMessageBox.warning(self, "Error", "Could not identify previous task.")
            return
        
        previous_task = self.data_manager.get_task(previous_task_id)
        if not previous_task:
            QMessageBox.warning(self, "Error", "Previous task not found.")
            return
        
        # Perform the indent (make current task a child of previous task)
        if self.data_manager.move_task(task_id, previous_task_id):
            self.expanded_tasks.add(previous_task_id)
            self._update_all_views()
            self.status_label.setText(f"✓ '{task.name}' indented under '{previous_task.name}'")
        else:
            QMessageBox.warning(self, "Cannot Indent", 
                              f"Cannot indent '{task.name}' under '{previous_task.name}'.\n\n"
                              "This would create a circular dependency.")
    
    def _outdent_task(self):
        """Outdent selected task (move up one level)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to outdent.")
            return
        
        current_item = selected_items[0]
        task_id = current_item.data(2, Qt.ItemDataRole.UserRole)
        
        if task_id is None:
            QMessageBox.warning(self, "Error", "Could not identify selected task.")
            return
        
        task = self.data_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Selected task not found.")
            return
        
        if task.parent_id is None:
            QMessageBox.information(self, "Cannot Outdent", 
                                  f"Cannot outdent '{task.name}'.\n\n"
                                  "This task is already at the top level.")
            return
        
        parent = self.data_manager.get_task(task.parent_id)
        if not parent:
            QMessageBox.warning(self, "Error", "Parent task not found.")
            return
        
        # Get the grandparent ID (None means move to top level)
        new_parent_id = parent.parent_id
        
        # Perform the outdent
        if self.data_manager.move_task(task_id, new_parent_id):
            self._update_all_views()
            if new_parent_id is None:
                self.status_label.setText(f"✓ '{task.name}' moved to top level")
            else:
                grandparent = self.data_manager.get_task(new_parent_id)
                self.status_label.setText(f"✓ '{task.name}' outdented (now under '{grandparent.name}')")
        else:
            QMessageBox.warning(self, "Error", "Failed to outdent task.")
    
    def _add_resource_dialog(self):
        """Show add resource dialog"""
        dialog = ResourceDialog(self, self.data_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            resource_data = dialog.get_resource_data()
            
            resource = Resource(
                name=resource_data['name'],
                max_hours_per_day=resource_data['max_hours_per_day'],
                exceptions=resource_data['exceptions'],
                billing_rate=float(resource_data.get('billing_rate', 0.0))
            )
            
            if self.data_manager.add_resource(resource):
                self._update_all_views()
                self.resource_summary._update_resource_delegates()
                self.status_label.setText(f"Resource '{resource.name}' added successfully")
            else:
                QMessageBox.warning(self, "Duplicate Resource", 
                                  "A resource with this name already exists.")
    

    def _add_milestone_dialog(self):
        """Show add milestone dialog"""
        dialog = TaskDialog(self, self.data_manager, is_milestone=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['start_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                is_milestone=task_data.get('is_milestone', True),
                font_family=task_data.get('font_family', 'Arial'),
                font_size=task_data.get('font_size', 10),
                font_color=task_data.get('font_color', '#000000'),
                background_color=task_data.get('background_color', '#FFFFFF'),
                font_bold=task_data.get('font_bold', None),
                font_italic=None,
                font_underline=task_data.get('font_underline', False)
            )
            
            if self.data_manager.add_task(task):
                self._update_all_views()
                self.status_label.setText(f"✓ Milestone '{task.name}' added successfully")
            else:
                QMessageBox.warning(self, "Validation Error", 
                                  "Milestone has circular dependencies or invalid dates.")

    def _insert_task_above(self):
        """Insert a new task above the selected task (renumbers IDs)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to insert above.")
            return
        
        # Get selected task
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        selected_task = self.data_manager.get_task(task_id)
        
        if not selected_task:
            return
        
        # Show info about renumbering
        reply = QMessageBox.question(
            self,
            "Insert Task",
            f"Insert a new task before '{selected_task.name}' (ID {selected_task.id})?\n\n"
            f"The new task will get ID {selected_task.id}.\n"
            f"All tasks from ID {selected_task.id} onwards will be renumbered.\n"
            f"Predecessors will be updated automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Open dialog for new task
        dialog = TaskDialog(self, self.data_manager)
        
        if selected_task.start_date:
            default_end = selected_task.start_date - timedelta(days=1)
            default_start = default_end - timedelta(days=6)
            
            dialog.start_date_input.setDate(QDate(default_start.year, default_start.month, default_start.day))
            dialog.end_date_input.setDate(QDate(default_end.year, default_end.month, default_end.day))
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            new_task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                task_id=None,
                is_milestone=task_data.get('is_milestone', False),
                font_family=task_data.get('font_family', 'Arial'),
                font_size=task_data.get('font_size', 10),
                font_color=task_data.get('font_color', '#000000'),
                background_color=task_data.get('background_color', '#FFFFFF'),
                font_bold=task_data.get('font_bold', None),
                font_italic=task_data.get('font_italic', None),
                font_underline=task_data.get('font_underline', False)
            )
            
            if self.data_manager.insert_task_before(new_task, selected_task.id):
                self._update_all_views()
                self.status_label.setText(
                    f"✓ Task '{new_task.name}' inserted at ID {new_task.id}. "
                    f"Tasks renumbered."
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to insert task.")
    
    def _insert_task_below(self):
        """Insert a new task below the selected task (renumbers IDs)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to insert below.")
            return
        
        # Get selected task
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        selected_task = self.data_manager.get_task(task_id)
        
        if not selected_task:
            return
        
        # Show info about renumbering
        new_id = selected_task.id + 1
        reply = QMessageBox.question(
            self,
            "Insert Task",
            f"Insert a new task after '{selected_task.name}' (ID {selected_task.id})?\n\n"
            f"The new task will get ID {new_id}.\n"
            f"All tasks from ID {new_id} onwards will be renumbered.\n"
            f"Predecessors will be updated automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Open dialog for new task
        dialog = TaskDialog(self, self.data_manager)
        
        # Pre-fill with dates just after the selected task
        if selected_task.end_date:
            default_start = selected_task.end_date + timedelta(days=1)
            default_end = default_start + timedelta(days=6)
            
            dialog.start_date_input.setDate(QDate(default_start.year, default_start.month, default_start.day))
            dialog.end_date_input.setDate(QDate(default_end.year, default_end.month, default_end.day))
            
            # Auto-add the selected task as predecessor
            dialog._add_predecessor_row()
            if dialog.predecessor_rows:
                task_combo, dep_type_combo, lag_spin, _ = dialog.predecessor_rows[0]
                # Find and select the current task
                for i in range(task_combo.count()):
                    if task_combo.itemData(i) == selected_task.id:
                        task_combo.setCurrentIndex(i)
                        break
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            new_task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                end_date=task_data['end_date'],
                percent_complete=task_data['percent_complete'],
                predecessors=task_data['predecessors'],
                assigned_resources=task_data['assigned_resources'],
                notes=task_data['notes'],
                task_id=None,
                is_milestone=task_data.get('is_milestone', False),
                font_family=task_data.get('font_family', 'Arial'),
                font_size=task_data.get('font_size', 10),
                font_color=task_data.get('font_color', '#000000'),
                background_color=task_data.get('background_color', '#FFFFFF'),
                font_bold=task_data.get('font_bold', None),
                font_italic=task_data.get('font_italic', None),
                font_underline=task_data.get('font_underline', False)
            )
            
            if self.data_manager.insert_task_at_position(new_task, selected_task.id):
                self._update_all_views()
                self.status_label.setText(
                    f"✓ Task '{new_task.name}' inserted at ID {new_task.id}. "
                    f"Tasks renumbered."
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to insert task.")
    
    def _convert_to_milestone(self):
        """Convert selected task to milestone"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to convert.")
            return
        
        task_id = selected_items[0].data(2, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id)
        
        if not task:
            return
        
        # Check if it's a summary task
        if getattr(task, 'is_summary', False):
            QMessageBox.warning(self, "Cannot Convert", 
                              "Cannot convert a summary task to a milestone.\n"
                              "Summary tasks have subtasks and must remain as summaries.")
            return
        
        # Check current state
        is_milestone = getattr(task, 'is_milestone', False)
        
        if is_milestone:
            # Convert milestone to regular task
            reply = QMessageBox.question(
                self, 
                "Convert to Task",
                f"Convert milestone '{task.name}' to a regular task?\n\n"
                "You'll need to set the end date.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                task.is_milestone = False
                # Set default end date (1 day duration) based on working hours
                end_h, end_m = self.data_manager.calendar_manager.get_working_end_time()
                task.end_date = task.start_date.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                
                # Ensure end date is not before start date (e.g. if start was late in day)
                if task.end_date <= task.start_date:
                     task.end_date = task.start_date + timedelta(hours=1)
                # Remove italic formatting when converting to task
                task.font_italic = False
                
                # Update task in data manager to trigger auto-adjustment of dependent tasks
                if self.data_manager.update_task(task_id, task):
                    self._update_all_views()
                    self.status_label.setText(f"✓ Converted '{task.name}' to regular task")
                else:
                    QMessageBox.warning(self, "Update Failed", 
                                      "Failed to update task. Please try again.")
        else:
            # Convert regular task to milestone
            reply = QMessageBox.question(
                self, 
                "Convert to Milestone",
                f"Convert task '{task.name}' to a milestone?\n\n"
                "The end date will be set to the start date (0 duration).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                task.is_milestone = True
                task.end_date = task.start_date
                # Add italic formatting when converting to milestone
                task.font_italic = True
                
                # Update task in data manager to trigger auto-adjustment of dependent tasks
                if self.data_manager.update_task(task_id, task):
                    self._update_all_views()
                    self.status_label.setText(f"✓ Converted '{task.name}' to milestone")
                else:
                    QMessageBox.warning(self, "Update Failed", 
                                      "Failed to update task. Please try again.")


    def _bulk_indent_tasks(self):
        """Indent multiple selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select one or more tasks to indent.")
            return
        
        # Get task IDs
        task_ids = []
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                task_ids.append(task_id)
        
        if not task_ids:
            return
        
        affected_parents = self.data_manager.bulk_indent_tasks(task_ids)
        if affected_parents:
            # Add all new parents to expanded tasks set so they stay open
            for parent_id in affected_parents:
                self.expanded_tasks.add(parent_id)
            
            self._update_all_views()
            self.status_label.setText(f"✓ Indented {len(task_ids)} task(s)")
        else:
            QMessageBox.warning(self, "Cannot Indent", 
                              "Could not indent the selected tasks.\n"
                              "Make sure they have tasks above them to indent under.")
    
    def _bulk_outdent_tasks(self):
        """Outdent multiple selected tasks"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select one or more tasks to outdent.")
            return
        
        # Get task IDs
        task_ids = []
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                task_ids.append(task_id)
        
        if not task_ids:
            return
        
        # Perform bulk outdent
        if self.data_manager.bulk_outdent_tasks(task_ids):
            self._update_all_views()
            self.status_label.setText(f"✓ Outdented {len(task_ids)} task(s)")
        else:
            QMessageBox.warning(self, "Cannot Outdent", 
                              "Could not outdent the selected tasks.\n"
                              "Make sure they are not already at top level.")
