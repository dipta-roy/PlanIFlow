from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QRadioButton, QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt

class BulkAddDialog(QDialog):
    """Dialog for adding multiple tasks in bulk by pasting text lines"""
    
    def __init__(self, parent, has_selection: bool = False):
        super().__init__(parent)
        self.has_selection = has_selection
        self.setWindowTitle("Bulk Add Tasks")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Info Header
        info_label = QLabel("<b>Bulk Add Tasks</b><br>"
                            "Paste or type task names below. Each line will become a new task.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Text input area
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Enter task names here. Press Enter after each task."
        )
        layout.addWidget(self.text_input)
        
        # Options
        options_layout = QVBoxLayout()
        options_label = QLabel("<b>Options:</b>")
        options_layout.addWidget(options_label)
        
        self.toplevel_radio = QRadioButton("Add as top-level tasks")
        self.toplevel_radio.setChecked(True)
        options_layout.addWidget(self.toplevel_radio)
        
        self.subtask_radio = QRadioButton("Add as subtasks under selected task")
        self.subtask_radio.setEnabled(self.has_selection)
        if self.has_selection:
            self.subtask_radio.setChecked(True)
            self.toplevel_radio.setChecked(False)
        else:
            self.subtask_radio.setToolTip("Please select a task in the list first to add subtasks.")
            
        options_layout.addWidget(self.subtask_radio)
        
        # Button Group for radios
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.toplevel_radio)
        self.button_group.addButton(self.subtask_radio)
        
        layout.addLayout(options_layout)
        layout.addSpacing(10)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        add_button = QPushButton("Add Tasks")
        add_button.setDefault(True)
        add_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(add_button)
        
        layout.addLayout(button_layout)
        
    def validate_and_accept(self):
        """Validate input before accepting"""
        tasks = self.get_task_names()
        if not tasks:
            QMessageBox.warning(self, "No Tasks Found", 
                               "Please enter at least one task name.")
            return
        self.accept()
        
    def get_task_names(self) -> list[str]:
        """Returns the list of parsed task names from the text edit"""
        text = self.text_input.toPlainText().strip()
        if not text:
            return []
        # Split by lines and remove empty/whitespace-only lines
        return [line.strip() for line in text.split('\n') if line.strip()]
        
    def is_add_as_subtasks(self) -> bool:
        """Returns True if user chose to add as subtasks"""
        return self.subtask_radio.isChecked() and self.subtask_radio.isEnabled()
