"""
Kanban Board - Interactive task management view with drag-and-drop
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QTextEdit,
                             QDialog, QComboBox, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag, QColor, QFont
from datetime import datetime

class TaskCard(QFrame):
    """Individual task card widget"""
    clicked = pyqtSignal(object)  # Emits the task object
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(300)
        self.setMaximumWidth(350)
        
        # Set fixed height for uniform card sizes
        self.setFixedHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Enable drag and drop
        self.setAcceptDrops(False)
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Task name (bold) with milestone indicator
        task_name_text = self.task.name
        if self.task.is_milestone:
            task_name_text = f"⭐ {task_name_text}"
        
        name_label = QLabel(task_name_text)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Task ID and WBS
        id_label = QLabel(f"ID: {self.task.id} | WBS: {self.task.wbs}")
        id_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(id_label)
        
        # Dates
        start_str = self.task.start_date.strftime('%Y-%m-%d')
        end_str = self.task.end_date.strftime('%Y-%m-%d')
        date_label = QLabel(f"📅 {start_str} → {end_str}")
        date_label.setStyleSheet("font-size: 9pt;")
        layout.addWidget(date_label)
        
        # Duration
        duration_label = QLabel(f"⏱️ Duration: {self.task.duration} days")
        duration_label.setStyleSheet("font-size: 9pt;")
        layout.addWidget(duration_label)
        
        # Progress
        progress_label = QLabel(f"📊 Progress: {self.task.percent_complete}%")
        progress_label.setStyleSheet("font-size: 9pt;")
        layout.addWidget(progress_label)
        
        # Resources
        if self.task.assigned_resources:
            resources_str = ", ".join([f"{name} ({alloc}%)" 
                                      for name, alloc in self.task.assigned_resources])
            resource_label = QLabel(f"👤 {resources_str}")
            resource_label.setWordWrap(True)
            resource_label.setStyleSheet("font-size: 9pt;")
            layout.addWidget(resource_label)
        
        # Notes preview (if any)
        if self.task.notes:
            notes_preview = self.task.notes[:50] + "..." if len(self.task.notes) > 50 else self.task.notes
            notes_label = QLabel(f"📝 {notes_preview}")
            notes_label.setWordWrap(True)
            notes_label.setStyleSheet("color: #555; font-size: 8pt; font-style: italic;")
            layout.addWidget(notes_label)
        
        layout.addStretch()
    
    def _apply_styling(self, dark_mode: bool = False):
        """Apply status-based styling with theme awareness"""
        status = self._get_task_status()
        
        if dark_mode:
            colors = {
                'To Do': '#1E293B',
                'In Progress': '#3B2D00',
                'Delayed': '#3E191C',
                'Completed': '#14381C'
            }
            border_colors = {
                'To Do': '#38BDF8',
                'In Progress': '#FACC15',
                'Delayed': '#F87171',
                'Completed': '#4ADE80'
            }
            bg_color = colors.get(status, '#2D2D2D')
            border_color = border_colors.get(status, '#555555')
            
            self.setStyleSheet(f"""
                TaskCard {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    padding: 5px;
                    color: #E2E8F0;
                }}
                TaskCard QLabel {{
                    color: #E2E8F0;
                }}
                TaskCard:hover {{
                    border: 2px solid {border_color};
                }}
            """)
        else:
            colors = {
                'To Do': '#E3F2FD',      # Light blue
                'In Progress': '#FFF9C4', # Light yellow
                'Delayed': '#FFCDD2',     # Light red
                'Completed': '#C8E6C9'    # Light green
            }
            border_colors = {
                'To Do': '#2196F3',
                'In Progress': '#FFC107',
                'Delayed': '#F44336',
                'Completed': '#4CAF50'
            }
            bg_color = colors.get(status, '#FFFFFF')
            border_color = border_colors.get(status, '#CCCCCC')
            
            self.setStyleSheet(f"""
                TaskCard {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    padding: 5px;
                }}
                TaskCard:hover {{
                    background-color: {self._lighten_color(bg_color)};
                    border: 2px solid {border_color};
                }}
            """)
    
    def _lighten_color(self, hex_color):
        """Lighten a hex color slightly for hover effect"""
        color = QColor(hex_color)
        h, s, v, a = color.getHsv()
        return QColor.fromHsv(h, max(0, s - 20), min(255, v + 20), a).name()
    
    def _get_task_status(self):
        """Determine task status for Kanban column"""
        if self.task.percent_complete == 100:
            return 'Completed'
        
        now = datetime.now()
        
        # Check if delayed (past end date and not complete)
        if self.task.end_date < now and self.task.percent_complete < 100:
            return 'Delayed'
        
        # Check if in progress (started but not complete)
        if self.task.start_date <= now < self.task.end_date and self.task.percent_complete > 0:
            return 'In Progress'
        
        # Default to To Do
        return 'To Do'
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag or click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle drag start"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        
        # Create drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.task.id))
        drag.setMimeData(mime_data)
        
        # Execute drag
        drag.exec(Qt.DropAction.MoveAction)
    
    def mouseReleaseEvent(self, event):
        """Handle click to open task details"""
        if event.button() == Qt.MouseButton.LeftButton:
            if (event.pos() - self.drag_start_position).manhattanLength() < 10:
                self.clicked.emit(self.task)


class KanbanColumn(QFrame):
    """Column for a specific status"""
    task_dropped = pyqtSignal(int, str)  # task_id, new_status
    
    def __init__(self, title, status_key, parent=None):
        super().__init__(parent)
        self.title = title
        self.status_key = status_key
        self.task_cards = []
        
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup column UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QLabel(self.title)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Count label
        self.count_label = QLabel("0 tasks")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.count_label)
        
        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(10)
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        # Styling
        self.apply_column_style(False)

    def apply_column_style(self, dark_mode: bool = False):
        self.dark_mode = dark_mode
        if dark_mode:
            self.count_label.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
            self.setStyleSheet("""
                KanbanColumn {
                    background-color: #252525;
                    border: 1px solid #3D3D3D;
                    border-radius: 5px;
                }
            """)
        else:
            self.count_label.setStyleSheet("color: #666; font-size: 9pt;")
            self.setStyleSheet("""
                KanbanColumn {
                    background-color: #F5F5F5;
                    border: 1px solid #CCCCCC;
                    border-radius: 5px;
                }
            """)
    
    def add_task_card(self, card):
        """Add a task card to this column"""
        self.cards_layout.addWidget(card)
        self.task_cards.append(card)
        self._update_count()
    
    def clear_cards(self):
        """Remove all task cards"""
        for card in self.task_cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.task_cards.clear()
        self._update_count()
    
    def _update_count(self):
        """Update task count label"""
        count = len(self.task_cards)
        self.count_label.setText(f"{count} task{'s' if count != 1 else ''}")
    
    def dragEnterEvent(self, event):
        """Accept drag events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            bg = "#1B381E" if getattr(self, 'dark_mode', False) else "#E8F5E9"
            self.setStyleSheet(f"""
                KanbanColumn {{
                    background-color: {bg};
                    border: 2px dashed #4CAF50;
                    border-radius: 5px;
                }}
            """)
    
    def dragLeaveEvent(self, event):
        """Reset styling when drag leaves"""
        self.apply_column_style(getattr(self, 'dark_mode', False))
    
    def dropEvent(self, event):
        """Handle task drop"""
        task_id = int(event.mimeData().text())
        self.task_dropped.emit(task_id, self.status_key)
        event.acceptProposedAction()
        
        # Reset styling
        self.dragLeaveEvent(None)


class TaskDetailDialog(QDialog):
    """Dialog for viewing/editing task details"""
    
    def __init__(self, task, data_manager, parent=None):
        super().__init__(parent)
        self.task = task
        self.data_manager = data_manager
        self.setWindowTitle(f"Task Details - {task.name}")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup detail dialog UI"""
        layout = QVBoxLayout(self)
        
        # Task info grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        grid.addWidget(QLabel("Task Name:"), 0, 0)
        name_val = QLabel(self.task.name)
        name_val.setStyleSheet("font-weight: bold;")
        grid.addWidget(name_val, 0, 1)
        
        grid.addWidget(QLabel("WBS:"), 1, 0)
        grid.addWidget(QLabel(self.task.wbs), 1, 1)
        
        grid.addWidget(QLabel("Dates:"), 2, 0)
        start_str = self.task.start_date.strftime('%Y-%m-%d')
        end_str = self.task.end_date.strftime('%Y-%m-%d')
        grid.addWidget(QLabel(f"{start_str} to {end_str}"), 2, 1)
        
        grid.addWidget(QLabel("Duration:"), 3, 0)
        grid.addWidget(QLabel(f"{self.task.duration} days"), 3, 1)
        
        grid.addWidget(QLabel("Progress:"), 4, 0)
        grid.addWidget(QLabel(f"{self.task.percent_complete}%"), 4, 1)
        
        if self.task.assigned_resources:
            grid.addWidget(QLabel("Resources:"), 5, 0)
            res_str = ", ".join([f"{name} ({alloc}%)" 
                                for name, alloc in self.task.assigned_resources])
            grid.addWidget(QLabel(res_str), 5, 1)
        
        layout.addLayout(grid)
        
        # Notes editor
        layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(self.task.notes or "")
        layout.addWidget(self.notes_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Notes")
        save_btn.clicked.connect(self._save_notes)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Close")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _save_notes(self):
        """Save updated notes"""
        self.task.notes = self.notes_edit.toPlainText()
        self.data_manager.update_task(self.task.id, self.task)
        self.accept()


class KanbanBoard(QWidget):
    """Main Kanban board widget"""
    
    def __init__(self, main_window_or_data_manager, main_window=None, parent=None):
        super().__init__(parent)
        if main_window is not None:
            self.data_manager = main_window_or_data_manager
            self.main_window = main_window
        else:
            self.main_window = main_window_or_data_manager
            self.data_manager = getattr(main_window_or_data_manager, 'data_manager', main_window_or_data_manager)
        self.dark_mode = getattr(self.main_window, 'dark_mode', False)
        self.columns = {}
        
        self._setup_ui()
        self.set_dark_mode(self.dark_mode)


    def set_dark_mode(self, dark_mode: bool):
        """Update dark mode state and refresh board theme"""
        self.dark_mode = dark_mode
        for column in self.columns.values():
            column.apply_column_style(dark_mode)
        self.refresh_board()

    def update_data_manager(self, data_manager):
        """Update the data manager reference"""
        self.data_manager = data_manager
        self.refresh_board()
    
    def _setup_ui(self):
        """Setup Kanban board UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with filters
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Kanban Board")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filter by view type
        header_layout.addWidget(QLabel("View:"))
        self.view_filter = QComboBox()
        self.view_filter.addItems(["Work Tasks & Milestones", "Work Tasks Only", "Milestones Only"])
        self.view_filter.currentTextChanged.connect(self.refresh_board)
        header_layout.addWidget(self.view_filter)
        
        # Filter by resource
        header_layout.addWidget(QLabel("Resource:"))
        self.resource_filter = QComboBox()
        self.resource_filter.addItem("All Resources")
        self.resource_filter.currentTextChanged.connect(self.refresh_board)
        header_layout.addWidget(self.resource_filter)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_board)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Columns container
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(10)
        
        # Create columns
        column_configs = [
            ("📝 To Do", "To Do"),
            ("🚀 In Progress", "In Progress"),
            ("⚠️ Delayed", "Delayed"),
            ("✅ Completed", "Completed")
        ]
        
        for title, status_key in column_configs:
            column = KanbanColumn(title, status_key)
            column.task_dropped.connect(self._handle_task_drop)
            self.columns[status_key] = column
            columns_layout.addWidget(column)
        
        layout.addLayout(columns_layout)
    
    def refresh_board(self):
        """Refresh the Kanban board with current tasks"""
        # Update resource filter
        self.resource_filter.blockSignals(True)
        current_resource = self.resource_filter.currentText()
        self.resource_filter.clear()
        self.resource_filter.addItem("All Resources")
        for resource in self.data_manager.get_all_resources():
            self.resource_filter.addItem(resource.name)
        
        # Restore selection
        index = self.resource_filter.findText(current_resource)
        if index >= 0:
            self.resource_filter.setCurrentIndex(index)
        self.resource_filter.blockSignals(False)
        
        # Clear all columns
        for column in self.columns.values():
            column.clear_cards()
        
        # Get filtered tasks
        tasks = self._get_filtered_tasks()
        
        # Add tasks to appropriate columns
        for task in tasks:
            card = TaskCard(task)
            card._apply_styling(dark_mode=getattr(self, 'dark_mode', False))
            card.clicked.connect(self._show_task_details)
            
            # Determine status
            status = self._get_task_status(task)
            
            if status in self.columns:
                self.columns[status].add_task_card(card)
    
    def _get_filtered_tasks(self):
        """Get tasks based on current filters, excluding summary tasks"""
        tasks = self.data_manager.get_all_tasks()
        
        # Always exclude summary tasks from Kanban board
        tasks = [t for t in tasks if not t.is_summary]
        
        # Filter by view type
        view_type = self.view_filter.currentText()
        if view_type == "Work Tasks Only":
            tasks = [t for t in tasks if not t.is_milestone]
        elif view_type == "Milestones Only":
            tasks = [t for t in tasks if t.is_milestone]
        
        # Filter by resource
        resource = self.resource_filter.currentText()
        if resource and resource != "All Resources":
            tasks = [t for t in tasks 
                    if any(name == resource for name, _ in t.assigned_resources)]
        
        return tasks
    
    def _get_task_status(self, task):
        """Determine task status for Kanban column"""
        if task.percent_complete == 100:
            return 'Completed'
        
        now = datetime.now()
        
        # Check if delayed (past end date and not complete)
        if task.end_date < now and task.percent_complete < 100:
            return 'Delayed'
        
        # Check if in progress (started but not complete)
        if task.start_date <= now < task.end_date and task.percent_complete > 0:
            return 'In Progress'
        
        # Check if blocked (has notes indicating blocking issues)
        if task.notes and any(keyword in task.notes.lower() 
                             for keyword in ['blocked', 'waiting', 'dependency']):
            return 'Blocked'
        
        # Default to To Do
        return 'To Do'
    
    def _handle_task_drop(self, task_id, _new_status):
        """Handle task being dropped into a new column"""
        # Note: In a full implementation, you might update task status
        # For now, we just refresh the board
        self.refresh_board()
    
    def _show_task_details(self, task):
        """Show task details dialog"""
        dialog = TaskDetailDialog(task, self.data_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_board()
            # Notify main window to refresh other views
            if hasattr(self.main_window, '_update_all_views'):
                self.main_window._update_all_views()
