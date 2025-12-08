from PyQt6.QtWidgets import (QMessageBox, QTreeWidgetItem, QHeaderView, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QBrush, QFont
from datetime import datetime
import re
import traceback

from data_manager import Task, DependencyType, ScheduleType
from settings_manager.settings_manager import DurationUnit, DateFormat
from ui.ui_delegates import SortableTreeWidgetItem

class TreeViewOperationsMixin:
    """Mixin for task tree view operations in MainWindow"""

    def _update_task_tree(self):
        """Update hierarchical task tree"""
        # Capture current sort state
        current_sort_col = self.task_tree.header().sortIndicatorSection()
        current_sort_order = self.task_tree.header().sortIndicatorOrder()

        # Capture column widths
        header = self.task_tree.header()
        column_widths = [header.sectionSize(i) for i in range(header.count())]

        # Disable sorting during update
        self.task_tree.setSortingEnabled(False)
        self.task_tree.blockSignals(True)
        self.task_tree.clear()
        
        # Ensure backward compatibility
        for task in self.data_manager.get_all_tasks():
            if not hasattr(task, 'is_milestone'):
                task.is_milestone = False
            if not hasattr(task, 'is_summary'):
                task.is_summary = False
        
        # Get filters
        search_text = self.search_box.text().lower()
        resource_filter = self.resource_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        # --- NEW FILTERING LOGIC ---
        tasks_to_display = set()
        all_tasks = self.data_manager.get_all_tasks()
        
        # Pass 1: Identify tasks that directly match the filter criteria
        for task in all_tasks:
            match_name = True
            if search_text:
                cleaned_search_text = search_text.replace('◆', '').replace('▶', '').strip()
                if cleaned_search_text and cleaned_search_text not in task.name.lower():
                    match_name = False
            
            match_resource = True
            if resource_filter != "All Resources":
                # Check if the resource_filter name exists in any of the assigned_resources tuples
                resource_names_assigned = [res[0] for res in task.assigned_resources]
                if resource_filter not in resource_names_assigned:
                    match_resource = False
            
            match_status = True
            if status_filter != "All":
                if status_filter != task.get_status_text():
                    match_status = False
            
            if match_name and match_resource and match_status:
                tasks_to_display.add(task.id)
        
        # Pass 2: Include all ancestors of tasks that are to be displayed
        # This ensures that if a child matches, its parent is also shown
        for task_id in list(tasks_to_display): # Iterate over a copy as set changes during iteration
            current_task = self.data_manager.get_task(task_id)
            while current_task and current_task.parent_id is not None:
                parent_task = self.data_manager.get_task(current_task.parent_id)
                if parent_task:
                    tasks_to_display.add(parent_task.id)
                    current_task = parent_task
                else:
                    break # Parent not found, stop
        
        # Helper function to add tasks to tree, only if they are in tasks_to_display
        # and their parent is also in tasks_to_display (or is None for top-level)
        added_items = {} # To store QTreeWidgetItem references by task ID

        def add_task_to_tree_filtered(task: Task, parent_item: QTreeWidgetItem = None, level: int = 0):
            if task.id not in tasks_to_display:
                return None

            # Create tree item
            item = SortableTreeWidgetItem(main_window=self)
            
            # Set flags for editability for each column
            # Column 0: Schedule Type (editable)
            # Column 1: Status (not editable)
            # Column 2: ID (not editable)
            # Column 3: WBS (not editable)
            # Other columns are generally editable
            for col_idx in range(self.task_tree.columnCount()):
                if col_idx in [1, 2, 3]:  # Status, ID, WBS columns
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            # COLUMN 0: Schedule Type
            item.setText(0, task.schedule_type.value)
            
            # COLUMN 1: Status
            status_color = task.get_status_color()
            status_text = task.get_status_text()
            item.setText(1, status_text)
            item.setData(1, Qt.ItemDataRole.UserRole, status_color)
            
            # COLUMN 2: Task ID (not editable)
            item.setText(2, str(task.id))
            item.setData(2, Qt.ItemDataRole.UserRole, task.id)
            item.setData(2, Qt.ItemDataRole.DisplayRole, task.id)  # Store as int, display as string
            
            # COLUMN 3: WBS (not editable)
            item.setText(3, task.wbs if task.wbs else "")

            # COLUMN 4: Task Name WITH MANUAL INDENTATION
            is_milestone = getattr(task, 'is_milestone', False)
            is_summary = getattr(task, 'is_summary', False)
            
            # Add spacing based on level (use em space for better appearance)
            indent = "    " * level  # 4 spaces per level
            
            if is_milestone:
                display_name = f"{indent}◆ {task.name}"
            elif is_summary:
                display_name = f"{indent}▶ {task.name}"
            else:
                display_name = f"{indent}{task.name}"
            
            item.setText(4, display_name)
            
            # Apply font styling from task properties
            font = item.font(4)
            # Use actual font properties from the task
            font.setBold(getattr(task, 'font_bold', False))
            font.setItalic(getattr(task, 'font_italic', False))
            item.setFont(4, font)
            
            # COLUMN 5: Start Date
            item.setText(5, task.start_date.strftime(self._get_strftime_format_string()))
            
            # COLUMN 6: End Date
            if is_milestone:
                item.setText(6, task.start_date.strftime(self._get_strftime_format_string()))
            else:
                item.setText(6, task.end_date.strftime(self._get_strftime_format_string()))
            
            # COLUMN 7: Duration
            duration = task.get_duration(
                self.data_manager.settings.duration_unit,
                self.calendar_manager
            )
            
            if is_milestone:
                item.setText(7, "0")
            elif self.data_manager.settings.duration_unit == DurationUnit.HOURS:
                item.setText(7, f"{duration:.1f}")
            else:
                item.setText(7, str(int(duration)))
            
            # COLUMN 8: % Complete
            item.setText(8, f"{task.percent_complete}%")
            
            # COLUMN 9: Predecessors
            pred_texts = []
            for pred_id, dep_type, lag_days in task.predecessors:
                lag_str = ""
                if lag_days > 0:
                    lag_str = f"+{lag_days}d"
                elif lag_days < 0:
                    lag_str = f"{lag_days}d"
                
                pred_texts.append(f"{pred_id}{dep_type}{lag_str}")
            item.setText(9, ", ".join(pred_texts))
            
            # COLUMN 10: Resources
            resource_texts = [f"{name} ({alloc} %)" for name, alloc in task.assigned_resources]
            item.setText(10, ", ".join(resource_texts))
            
            # COLUMN 11: Notes
            item.setText(11, task.notes)
            
            # Set row color based on status
            color_map = {
                'red': QColor(255, 235, 238),
                'green': QColor(232, 245, 233),
                'grey': QColor(245, 245, 245),
                'blue': QColor(227, 242, 253)
            }
            
            # Special color for milestones
            if is_milestone:
                milestone_color = QColor(255, 255, 200)  # Light yellow
                for col in range(self.task_tree.columnCount()):
                    item.setBackground(col, QBrush(milestone_color))
            elif not self.dark_mode:
                bg_color = color_map.get(status_color, QColor(255, 255, 255))
                # SLIGHTLY LIGHTER BACKGROUND FOR DEEPER LEVELS
                if level > 0:
                    bg_color = bg_color.lighter(100 + (level * 2))
                for col in range(self.task_tree.columnCount()):
                    item.setBackground(col, QBrush(bg_color))
            
            # Add to tree
            if parent_item:
                parent_item.addChild(item)
            else:
                self.task_tree.addTopLevelItem(item)
            
            added_items[task.id] = item

            # Add children recursively, but only if they are also in tasks_to_display
            children = self.data_manager.get_child_tasks(task.id)
            for child in children:
                add_task_to_tree_filtered(child, item, level + 1)
            
            # Restore expanded state
            if task.id in self.expanded_tasks:
                item.setExpanded(True)
            
            return item
        
        # Build tree starting from top-level tasks that are in tasks_to_display
        top_level_tasks = [t for t in self.data_manager.get_top_level_tasks() if t.id in tasks_to_display]
        for task in top_level_tasks:
            add_task_to_tree_filtered(task, None, 0)

        # Re-enable signals
        self.task_tree.blockSignals(False)
        
        # Set WBS column visibility
        self.task_tree.setColumnHidden(3, not self.toggle_wbs_action.isChecked())
        
        # Restore column widths
        for i, width in enumerate(column_widths):
            if width > 0: # Only restore if the width was saved
                header.resizeSection(i, width)
        
        # Enable sorting first
        self.task_tree.setSortingEnabled(True)
        
        # Restore sort state or apply default ID sort
        if current_sort_col != -1:
            # Restore previous sort
            self.task_tree.sortByColumn(current_sort_col, current_sort_order)
        else:
            # Default to ID ascending sort
            self.task_tree.sortByColumn(2, Qt.SortOrder.AscendingOrder)

    def _filter_tasks(self):
        """Apply filters to task tree"""
        self._update_task_tree()
    
    def _clear_filters(self):
        """Clear all filters"""
        self.search_box.clear()
        self.resource_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(self.status_filter.findText("All"))
        self._update_task_tree()

    def _expand_all_tasks(self):
        """Expand all tasks in tree"""
        self.task_tree.expandAll()
        # Track all summary tasks as expanded
        for task in self.data_manager.get_all_tasks():
            if task.is_summary:
                self.expanded_tasks.add(task.id)
        self.status_label.setText("✓ Expanded all tasks")
    
    def _collapse_all_tasks(self):
        """Collapse all tasks in tree"""
        self.task_tree.collapseAll()
        self.expanded_tasks.clear()
        self.status_label.setText("✓ Collapsed all tasks")

    def _expand_selected(self):
        """Expand only the selected summary task (not its children)"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a task to expand.")
            return
        
        expanded_count = 0
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                if item.childCount() > 0:
                    item.setExpanded(True)
                    self.expanded_tasks.add(task_id)
                    expanded_count += 1
        
        if expanded_count > 0:
            self.status_label.setText(f"✓ Expanded {expanded_count} task(s)")
        else:
            QMessageBox.information(self, "No Expandable Task", 
                                  "Selected task(s) have no subtasks to expand.")

    def _collapse_selected(self):
        """Collapse selected summary task"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a summary task to collapse.")
            return
        
        collapsed_count = 0
        for item in selected_items:
            # Get task ID from column 2
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            
            if task_id is not None:
                item.setExpanded(False)
                self.expanded_tasks.discard(task_id)
                collapsed_count += 1
        
        if collapsed_count > 0:
            self.status_label.setText(f"✓ Collapsed {collapsed_count} task(s)")

    def _expand_all_children_of_selected(self):
        """Expand selected summary task and all its children recursively"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", 
                                  "Please select a summary task to expand its children.")
            return
        
        expanded_count = 0
        for item in selected_items:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            if task_id is not None:
                task = self.data_manager.get_task(task_id)
                if task and task.is_summary:
                    self._expand_item_recursively(item)
                    self.expanded_tasks.add(task_id)
                    # Also add all descendants to expanded_tasks for tracking
                    descendants = self.data_manager.get_all_descendants(task_id)
                    for desc in descendants:
                        if desc.is_summary:
                            self.expanded_tasks.add(desc.id)
                    expanded_count += 1
                else:
                    # If not a summary task, just expand the item if it has children
                    if item.childCount() > 0:
                        item.setExpanded(True)
                        if task_id:
                            self.expanded_tasks.add(task_id)
                        expanded_count += 1
        
        if expanded_count > 0:
            self.status_label.setText(f"✓ Expanded children of {expanded_count} task(s)")
        else:
            QMessageBox.information(self, "No Expandable Children", 
                                  "Selected task(s) have no subtasks to expand recursively.")

    def _expand_item_recursively(self, item: QTreeWidgetItem):
        """Recursively expand an item and all its children"""
        item.setExpanded(True)
        for i in range(item.childCount()):
            child = item.child(i)
            self._expand_item_recursively(child)
    
    def _collapse_item_recursively(self, item: QTreeWidgetItem):
        """Recursively collapse an item and all its children"""
        for i in range(item.childCount()):
            child = item.child(i)
            self._collapse_item_recursively(child)
        item.setExpanded(False)

    def _toggle_expand_collapse(self):
        """Toggle expand/collapse for selected item"""
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            return
        
        # Note: This method currently operates on the first selected item.
        # If multiple items are selected, only the first one's state will be toggled.
        item = selected_items[0]
        if item.isExpanded():
            self._collapse_selected()
        else:
            self._expand_selected()

    def _toggle_wbs_column_visibility(self):
        """Toggle visibility of the WBS column"""
        is_visible = self.toggle_wbs_action.isChecked()
        self.task_tree.setColumnHidden(3, not is_visible)
        self.status_label.setText(f"✓ WBS column visibility toggled: {is_visible}")

    def _sort_by_column(self, column: int):
        """Sort tree by specific column"""
        current_order = self.task_tree.header().sortIndicatorOrder()
        # Toggle order if clicking same column
        if self.task_tree.sortColumn() == column:
            new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            new_order = Qt.SortOrder.AscendingOrder
        
        self.task_tree.sortByColumn(column, new_order)
    
    def _on_tree_clicked(self, index):
        """Handle click on tree item to toggle expand/collapse for summary tasks"""
        item = self.task_tree.itemFromIndex(index)
        if item:
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            task = self.data_manager.get_task(task_id)

            if task and task.is_summary:
                item.setExpanded(not item.isExpanded())
                if item.isExpanded():
                    self.expanded_tasks.add(task_id)
                else:
                    self.expanded_tasks.discard(task_id)
    
    def _show_task_context_menu(self, position):
        """Show context menu on task right-click"""
        item = self.task_tree.itemAt(position)
        if not item:
            return
        
        # Get task ID from column 2
        task_id = item.data(2, Qt.ItemDataRole.UserRole)
        task = self.data_manager.get_task(task_id) if task_id else None
        
        menu = QMenu(self)
        
        # *** ADD INSERT OPTIONS ***
        insert_above_action = QAction("➕ Insert Task Above", self)
        insert_above_action.triggered.connect(self._insert_task_above)
        menu.addAction(insert_above_action)
        
        insert_below_action = QAction("➕ Insert Task Below", self)
        insert_below_action.triggered.connect(self._insert_task_below)
        menu.addAction(insert_below_action)
        
        menu.addSeparator()
        
        # Edit action
        edit_action = QAction("✏️ Edit Task", self)
        edit_action.triggered.connect(self._edit_task_dialog)
        menu.addAction(edit_action)
        
        # Delete action
        delete_action = QAction("🗑️ Delete Task", self)
        delete_action.triggered.connect(self._delete_task)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # *** ADD CONVERT TO MILESTONE OPTION ***
        if task and not getattr(task, 'is_summary', False):
            is_milestone = getattr(task, 'is_milestone', False)
            
            if is_milestone:
                convert_action = QAction("🔄 Convert to Task", self)
                convert_action.triggered.connect(self._convert_to_milestone)
                menu.addAction(convert_action)
            else:
                convert_action = QAction("🔄 Convert to Milestone", self)
                convert_action.triggered.connect(self._convert_to_milestone)
                menu.addAction(convert_action)
            
            menu.addSeparator()
            
        # Expand/Collapse actions for summary tasks
        if task and task.is_summary:
            if item.isExpanded():
                collapse_action = QAction("⊖ Collapse", self)
                collapse_action.triggered.connect(self._collapse_selected)
                menu.addAction(collapse_action)
                
                collapse_all_action = QAction("⊟ Collapse All Children", self)
                collapse_all_action.triggered.connect(lambda: self._collapse_item_recursively(item))
                menu.addAction(collapse_all_action)
            else:
                expand_action = QAction("⊕ Expand", self)
                expand_action.triggered.connect(self._expand_selected)
                menu.addAction(expand_action)
                
                expand_all_action = QAction("⊞ Expand All Children", self)
                expand_all_action.triggered.connect(self._expand_all_children_of_selected)
                menu.addAction(expand_all_action)
            
            menu.addSeparator()
        
        # Indent/Outdent
        indent_action = QAction("→ Indent", self)
        indent_action.triggered.connect(self._indent_task)
        menu.addAction(indent_action)
        
        if task and task.parent_id is not None:
            outdent_action = QAction("← Outdent", self)
            outdent_action.triggered.connect(self._outdent_task)
            menu.addAction(outdent_action)
        
        menu.addSeparator()
        
        # Add subtask
        add_subtask_action = QAction("➕ Add Subtask", self)
        add_subtask_action.triggered.connect(self._add_subtask_dialog)
        menu.addAction(add_subtask_action)
        
        menu.exec(self.task_tree.mapToGlobal(position))

    def _show_header_context_menu(self, position):
        """Show context menu on header right-click"""
        header = self.task_tree.header()
        column = header.logicalIndexAt(position)
        
        menu = QMenu(self)
        
        # Sort ascending
        sort_asc_action = QAction(f"Sort Ascending", self)
        sort_asc_action.triggered.connect(lambda: self.task_tree.sortByColumn(column, Qt.SortOrder.AscendingOrder))
        menu.addAction(sort_asc_action)
        
        # Sort descending
        sort_desc_action = QAction(f"Sort Descending", self)
        sort_desc_action.triggered.connect(lambda: self.task_tree.sortByColumn(column, Qt.SortOrder.DescendingOrder))
        menu.addAction(sort_desc_action)
        
        menu.addSeparator()
        
        # Reset to default (ID ascending)
        reset_action = QAction("Reset to Default (ID)", self)
        reset_action.triggered.connect(lambda: self.task_tree.sortByColumn(2, Qt.SortOrder.AscendingOrder))
        menu.addAction(reset_action)
        
        menu.exec(header.mapToGlobal(position))
        
    def _on_header_clicked(self, logical_index):
        """Handle header click for sorting"""
        # Toggle sort order
        current_order = self.task_tree.header().sortIndicatorOrder()
        new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        
        # Sort by the clicked column
        self.task_tree.sortByColumn(logical_index, new_order)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Track expanded items"""
        # Get task ID from column 2
        task_id = item.data(2, Qt.ItemDataRole.UserRole)
        if task_id:
            self.expanded_tasks.add(task_id)
    
    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Track collapsed items"""
        # Get task ID from column 2
        task_id = item.data(2, Qt.ItemDataRole.UserRole)
        if task_id:
            self.expanded_tasks.discard(task_id)

    def _on_task_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle single click on tree item to toggle expand/collapse for summary tasks"""
        # Check if the clicked item has children (i.e., it's a summary task)
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            task_id = item.data(2, Qt.ItemDataRole.UserRole)
            if task_id:
                if item.isExpanded():
                    self.expanded_tasks.add(task_id)
                else:
                    self.expanded_tasks.discard(task_id)
        
        # Update formatting buttons to reflect selected task's formatting
        if hasattr(self, '_update_formatting_buttons'):
            self._update_formatting_buttons()
    
    def _on_task_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle inline editing of task properties"""
        # Block signals to prevent recursive calls during update
        self.task_tree.blockSignals(True)

        task_id = item.data(2, Qt.ItemDataRole.UserRole) # Task ID is in column 2
        task = self.data_manager.get_task(task_id)

        if not task:
            self.task_tree.blockSignals(False)
            return

        original_task = Task.from_dict(task.to_dict()) # Create a copy to revert if validation fails

        try:
            new_value = item.text(column)
            changed = False

            if column == 0: # Schedule Type
                try:
                    new_schedule_type = ScheduleType(new_value)
                    # Validation: Summary tasks must always be Auto Scheduled
                    if task.is_summary and new_schedule_type == ScheduleType.MANUALLY_SCHEDULED:
                        QMessageBox.warning(self, "Validation Error",
                                            "Summary tasks must always be 'Auto Scheduled'. Reverting change.")
                        item.setText(0, task.schedule_type.value) # Revert UI
                        self.task_tree.blockSignals(False)
                        return
                    
                    if task.schedule_type != new_schedule_type:
                        task.schedule_type = new_schedule_type
                        changed = True
                except ValueError:
                    QMessageBox.critical(self, "Input Error", f"Invalid Schedule Type: {new_value}")
                    self._revert_task_item_in_ui(item, original_task)
                    self.task_tree.blockSignals(False)
                    return
            elif column == 4:  # Task Name
                # Clean up display markers before saving to actual task name
                cleaned_name = new_value.lstrip(' ▶◆')
                if task.name != cleaned_name:
                    task.name = cleaned_name
                    changed = True
            elif column == 5:  # Start Date
                new_start_date = datetime.strptime(new_value, self._get_strftime_format_string())
                if task.start_date.date() != new_start_date.date():
                    task.start_date = new_start_date
                    changed = True
            elif column == 6:  # End Date
                if not task.is_milestone: # Milestones have fixed end date
                    new_end_date = datetime.strptime(new_value, self._get_strftime_format_string())
                    if task.end_date.date() != new_end_date.date():
                        task.end_date = new_end_date
                        changed = True
            elif column == 7:  # Duration
                new_duration = float(new_value)
                if task.is_milestone and new_duration > 0:
                    task.is_milestone = False
                    task.font_italic = False  # Remove italic when converting to task
                    task.set_duration_and_update_end(new_duration, self.data_manager.settings.duration_unit, self.calendar_manager)
                    changed = True
                elif not task.is_milestone and new_duration == 0:
                    task.is_milestone = True
                    task.end_date = task.start_date
                    task.font_italic = True  # Add italic when converting to milestone
                    changed = True
                elif not task.is_milestone:
                    current_duration_unit = self.data_manager.settings.duration_unit
                    if abs(task.get_duration(current_duration_unit, self.calendar_manager) - new_duration) > 0.01:
                        task.set_duration_and_update_end(new_duration, current_duration_unit, self.calendar_manager)
                        changed = True
            elif column == 8:  # % Complete
                try:
                    new_percent_complete = int(new_value.strip('%'))
                    if not (0 <= new_percent_complete <= 100):
                        raise ValueError("Percentage must be between 0 and 100.")
                    if task.percent_complete != new_percent_complete:
                        task.percent_complete = new_percent_complete
                        changed = True
                    item.setText(8, f"{task.percent_complete}%")
                except ValueError as ve:
                    QMessageBox.critical(self, "Input Error", f"Invalid input for % Complete: {ve}")
                    self._revert_task_item_in_ui(item, original_task)
                    self.task_tree.blockSignals(False)
                    return
            elif column == 9:  # Dependencies
                new_predecessors = []
                if new_value.strip():
                    for pred_str in new_value.split(','):
                        pred_str = pred_str.strip()
                        if not pred_str:
                            continue

                        lag_days = 0
                        dep_type = DependencyType.FS.name

                        # Regex to handle formats like "1", "1 FS", "1FS+2d", "1 (FS-1d)"
                        # Updated regex: (?:([+-])(\d+)(d)?)?
                        # Group 3: sign (+ or -)
                        # Group 4: digits (the lag value)
                        # Group 5: 'd' if present, None otherwise
                        match = re.match(r'(\d+)\s*([A-Z]{2})?(?:([+-])(\d+)(d)?)?', pred_str)
                        if match:
                            pred_id = int(match.group(1))
                            if match.group(2):
                                dep_type = match.group(2)
                            
                            # Check if lag part was matched
                            if match.group(3) and match.group(4):
                                lag_days = int(match.group(4))
                                if match.group(3) == '-':
                                    lag_days = -lag_days
                            
                            new_predecessors.append((pred_id, dep_type, lag_days))

                if task.predecessors != new_predecessors:
                    task.predecessors = new_predecessors
                    changed = True
                
                # Explicitly update the item's text with the formatted predecessors
                # This ensures the 'd' is added back for display
                formatted_predecessors = []
                for pred_id, dep_type, lag_days in new_predecessors:
                    lag_str = ""
                    if lag_days > 0:
                        lag_str = f"+{lag_days}d"
                    elif lag_days < 0:
                        lag_str = f"{lag_days}d"
                    formatted_predecessors.append(f"{pred_id}{dep_type}{lag_str}")
                item.setText(9, ", ".join(formatted_predecessors))
            elif column == 10:  # Resources
                new_resources = []
                if new_value.strip():
                    for r_str in new_value.split(','):
                        match = re.match(r'(.+?)\s*\((\d+)\s*%\)', r_str.strip())
                        if match:
                            new_resources.append((match.group(1).strip(), int(match.group(2))))
                        else:
                            # For backward compatibility, if no percentage is specified, assume 100%
                            new_resources.append((r_str.strip(), 100))
                if task.assigned_resources != new_resources:
                    task.assigned_resources = new_resources
                    changed = True
            elif column == 11:  # Notes
                if task.notes != new_value:
                    task.notes = new_value
                    changed = True

            if changed:
                if self.data_manager.update_task(task_id, task):
                    self._update_all_views()
                    self.status_label.setText(f"✓ Task '{task.name}' updated successfully")
                else:
                    QMessageBox.warning(self, "Validation Error",
                                      "Task update failed (e.g., circular dependency, invalid date).")
                    # Revert changes in UI if update failed
                    self._revert_task_item_in_ui(item, original_task)

        except Exception as e:
            QMessageBox.critical(self, "Input Error", f"Invalid input for {item.text(0)}: {e}")
            # Revert changes in UI if input was invalid
            self._revert_task_item_in_ui(item, original_task)

        self.task_tree.blockSignals(False)

    def _revert_task_item_in_ui(self, item: QTreeWidgetItem, original_task: Task):
        """Revert the UI item to its original task values"""
        # Temporarily block signals to prevent itemChanged from firing again
        self.task_tree.blockSignals(True)

        # Update each column with original data
        item.setText(0, original_task.schedule_type.value) # Schedule Type
        item.setText(4, original_task.name) # Task Name
        item.setText(5, original_task.start_date.strftime(self._get_strftime_format_string())) # Start Date
        if original_task.is_milestone:
            item.setText(6, original_task.start_date.strftime(self._get_strftime_format_string()))
        else:
            item.setText(6, original_task.end_date.strftime(self._get_strftime_format_string())) # End Date
        
        # Duration
        duration = original_task.get_duration(
            self.data_manager.settings.duration_unit,
            self.calendar_manager
        )
        if original_task.is_milestone:
            item.setText(7, "0")
        elif self.data_manager.settings.duration_unit == DurationUnit.HOURS:
            item.setText(7, f"{duration:.1f}")
        else:
            item.setText(7, str(int(duration)))

        item.setText(8, f"{original_task.percent_complete}%") # % Complete
        
        pred_texts = []
        for pred_id, dep_type, lag_days in original_task.predecessors:
            lag_str = ""
            if lag_days > 0:
                lag_str = f"+{lag_days}d"
            elif lag_days < 0:
                lag_str = f"{lag_days}d"
            
            pred_texts.append(f"{pred_id}{dep_type}{lag_str}")
        item.setText(9, ", ".join(pred_texts)) # Dependencies
        resource_texts = [f"{name} ({alloc}%)" for name, alloc in original_task.assigned_resources]
        item.setText(10, ", ".join(resource_texts)) # Resources
        item.setText(11, original_task.notes) # Notes

        self.task_tree.blockSignals(False)

    def _get_strftime_format_string(self) -> str:
        """Converts the DateFormat enum to a strftime compatible format string."""
        date_format_enum = self.data_manager.settings.default_date_format
        if date_format_enum == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y'
        elif date_format_enum == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y'
        else: # DateFormat.YYYY_MM_DD
            return '%Y-%m-%d'
