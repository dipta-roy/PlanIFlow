from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QLabel, QLineEdit, QDateEdit, QGroupBox, 
                             QCheckBox, QPushButton, QComboBox, QFormLayout, QMessageBox, QSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QDate, QTime, Qt
from datetime import datetime
from settings_manager.settings_manager import DateFormat, DurationUnit, Currency
from calendar_manager.calendar_manager import CalendarManager
from ui.ui_time_picker import TimePickerWidget

class SettingsDialog(QDialog):
    """Unified settings dialog for Project, Calendar, and Interface settings"""
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.calendar_manager = data_manager.calendar_manager
        self.settings = data_manager.settings
        
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(650)
        self.setMinimumHeight(450)
        
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # Initialize tabs
        self.general_tab = self._create_general_tab()
        self.calendar_tab = self._create_calendar_tab()
        self.holidays_tab = self._create_holidays_tab()
        self.interface_tab = self._create_interface_tab()
        
        self.tabs.addTab(self.general_tab, "⚙️ General")
        self.tabs.addTab(self.calendar_tab, "📅 Calendar")
        self.tabs.addTab(self.holidays_tab, "🏖️ Holidays")
        self.tabs.addTab(self.interface_tab, "🖥️ Interface")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.setAutoDefault(False) # Prevent Accidental Enter submission
        ok_button.clicked.connect(self._save_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def _create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        
        # Project Name
        self.project_name_input = QLineEdit(self.data_manager.project_name)
        form_layout.addRow("Project Name:", self.project_name_input)
        
        # Project Start Date
        self.project_start_date_input = QDateEdit()
        self.project_start_date_input.setCalendarPopup(True)
        self.project_start_date_input.setDisplayFormat("yyyy-MM-dd")
        
        initial_date = QDate.currentDate()
        if self.settings.project_start_date:
            initial_date = QDate(self.settings.project_start_date.year,
                                 self.settings.project_start_date.month,
                                 self.settings.project_start_date.day)
        self.project_start_date_input.setDate(initial_date)
        form_layout.addRow("Project Start Date:", self.project_start_date_input)
        
        # Currency
        self.currency_combo = QComboBox()
        for c in Currency:
            self.currency_combo.addItem(f"{c.code} ({c.symbol})", c)
        
        current_currency_index = self.currency_combo.findData(self.settings.currency)
        if current_currency_index != -1:
            self.currency_combo.setCurrentIndex(current_currency_index)
            
        form_layout.addRow("Currency:", self.currency_combo)
        
        layout.addLayout(form_layout)
        
        # Disclaimer
        note_label = QLabel("ℹ️ Note: For new projects, please ensure you also configure the Calendar (working hours) and Date Format settings.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: blue; font-style: italic; margin-top: 10px;")
        layout.addWidget(note_label)
        
        layout.addStretch()
        return widget
        
    def _create_calendar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Disclaimer
        disclaimer_label = QLabel("ℹ️ Note: Please setup calendar time and working hours at the start of project creation for best results.")
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setStyleSheet("color: blue; font-style: italic;")
        layout.addWidget(disclaimer_label)
        
        # Working Hours Group
        hours_group = QGroupBox("Working Hours")
        hours_layout = QVBoxLayout()
        
        # Display Total Hours
        hours_display_layout = QHBoxLayout()
        hours_display_layout.addWidget(QLabel("Total Hours per Day:"))
        self.hours_display = QLineEdit()
        self.hours_display.setReadOnly(True)
        self.hours_display.setMaximumWidth(100)
        self.hours_display.setText(f"{self.calendar_manager.hours_per_day:.2f} hours")
        hours_display_layout.addWidget(self.hours_display)
        hours_display_layout.addStretch()
        hours_layout.addLayout(hours_display_layout)
        
        # Start Time
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(QLabel("Work Start Time:"))
        
        start_parts = self.calendar_manager.working_hours_start.split(':')
        start_qtime = QTime(int(start_parts[0]), int(start_parts[1]))
        self.start_time_picker = TimePickerWidget(start_qtime)
        self.start_time_picker.timeChanged.connect(self._update_hours_display)
        start_time_layout.addWidget(self.start_time_picker)
        hours_layout.addLayout(start_time_layout)
        
        # End Time
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(QLabel("Work End Time:"))
        
        end_parts = self.calendar_manager.working_hours_end.split(':')
        end_qtime = QTime(int(end_parts[0]), int(end_parts[1]))
        self.end_time_picker = TimePickerWidget(end_qtime)
        self.end_time_picker.timeChanged.connect(self._update_hours_display)
        end_time_layout.addWidget(self.end_time_picker)
        hours_layout.addLayout(end_time_layout)
        
        hours_group.setLayout(hours_layout)
        layout.addWidget(hours_group)
        
        # Working Days Group
        days_group = QGroupBox("Working Days")
        days_layout = QVBoxLayout()
        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        grid_layout = QHBoxLayout() # Use HBox for cleaner look if space allows, or flow
        
        # Split into two columns
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(i in self.calendar_manager.working_days)
            self.day_checkboxes[i] = checkbox
            if i < 4:
                col1.addWidget(checkbox)
            else:
                col2.addWidget(checkbox)
                
        grid_layout.addLayout(col1)
        grid_layout.addLayout(col2)
        days_layout.addLayout(grid_layout)
        
        days_group.setLayout(days_layout)
        layout.addWidget(days_group)
        
        return widget

    def _create_holidays_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel("Specify project-level holidays or non-working periods. These will affect all scheduling.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(info_label)
        
        # Holidays Table
        self.holidays_table = QTableWidget()
        self.holidays_table.setColumnCount(5)
        self.holidays_table.setHorizontalHeaderLabels(["Holiday Name", "Start Date", "End Date", "Recurring", "Comment"])
        self.holidays_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.holidays_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.holidays_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Populate table from calendar_manager
        holidays = self.calendar_manager.custom_holidays
        self.holidays_table.setRowCount(len(holidays))
        for row, holiday in enumerate(holidays):
            self.holidays_table.setItem(row, 0, QTableWidgetItem(holiday.get("name", "")))
            
            # Start Date Picker
            start_date_edit = QDateEdit()
            start_date_edit.setCalendarPopup(True)
            start_date_edit.setDisplayFormat("yyyy-MM-dd")
            s_date = QDate.fromString(holiday.get("start_date", ""), "yyyy-MM-dd")
            if s_date.isValid():
                start_date_edit.setDate(s_date)
            self.holidays_table.setCellWidget(row, 1, start_date_edit)
            
            # End Date Picker
            end_date_edit = QDateEdit()
            end_date_edit.setCalendarPopup(True)
            end_date_edit.setDisplayFormat("yyyy-MM-dd")
            e_date = QDate.fromString(holiday.get("end_date", ""), "yyyy-MM-dd")
            if e_date.isValid():
                end_date_edit.setDate(e_date)
            self.holidays_table.setCellWidget(row, 2, end_date_edit)
            
            # Recurring Checkbox
            recurring_cb = QCheckBox()
            recurring_cb.setChecked(holiday.get("is_recurring", False))
            cb_container = QWidget()
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.addWidget(recurring_cb)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.holidays_table.setCellWidget(row, 3, cb_container)
            
            self.holidays_table.setItem(row, 4, QTableWidgetItem(holiday.get("comment", "")))
            
        layout.addWidget(self.holidays_table)
        
        # Holiday buttons
        h_btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Add Holiday")
        add_btn.clicked.connect(self._add_holiday_row)
        h_btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("- Remove Selected")
        remove_btn.clicked.connect(self._remove_holiday_row)
        h_btn_layout.addWidget(remove_btn)
        
        h_btn_layout.addStretch()
        layout.addLayout(h_btn_layout)
        
        return widget

    def _add_holiday_row(self):
        row = self.holidays_table.rowCount()
        self.holidays_table.insertRow(row)
        
        self.holidays_table.setItem(row, 0, QTableWidgetItem("New Holiday"))
        
        # Start Date Picker
        start_date_edit = QDateEdit()
        start_date_edit.setCalendarPopup(True)
        start_date_edit.setDisplayFormat("yyyy-MM-dd")
        start_date_edit.setDate(QDate.currentDate())
        self.holidays_table.setCellWidget(row, 1, start_date_edit)
        
        # End Date Picker
        end_date_edit = QDateEdit()
        end_date_edit.setCalendarPopup(True)
        end_date_edit.setDisplayFormat("yyyy-MM-dd")
        end_date_edit.setDate(QDate.currentDate())
        self.holidays_table.setCellWidget(row, 2, end_date_edit)
        
        # Recurring Checkbox
        recurring_cb = QCheckBox()
        cb_container = QWidget()
        cb_layout = QHBoxLayout(cb_container)
        cb_layout.addWidget(recurring_cb)
        cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        self.holidays_table.setCellWidget(row, 3, cb_container)
        
        self.holidays_table.setItem(row, 4, QTableWidgetItem(""))

    def _remove_holiday_row(self):
        current_row = self.holidays_table.currentRow()
        if current_row >= 0:
            self.holidays_table.removeRow(current_row)
        else:
            QMessageBox.information(self, "Selection Required", "Please select a holiday row to remove.")

    def _create_interface_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_layout = QFormLayout()
        
        # Date Format
        self.date_format_combo = QComboBox()
        for df in DateFormat:
            self.date_format_combo.addItem(df.value, df)
        
        current_index = self.date_format_combo.findData(self.settings.default_date_format)
        if current_index != -1:
            self.date_format_combo.setCurrentIndex(current_index)
            
        form_layout.addRow("Date Format:", self.date_format_combo)
        
        # Duration Unit
        self.duration_unit_combo = QComboBox()
        for du in DurationUnit:
            self.duration_unit_combo.addItem(du.value, du)
            
        current_dur_index = self.duration_unit_combo.findData(self.settings.duration_unit)
        if current_dur_index != -1:
            self.duration_unit_combo.setCurrentIndex(current_dur_index)
            
        form_layout.addRow("Duration Unit:", self.duration_unit_combo)

        # App Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        # Handle None value for app_font_size
        current_font_size = getattr(self.settings, 'app_font_size', 9)
        if current_font_size is None or current_font_size == "":
            current_font_size = 9
        
        # Ensure it's an int
        try:
             current_font_size = int(current_font_size)
        except:
             current_font_size = 10
             
        self.font_size_spin.setValue(current_font_size)
        self.font_size_spin.setSuffix(" pt")
        form_layout.addRow("Application Font Size:", self.font_size_spin)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        return widget
        
    def _update_hours_display(self):
        start_time = self.start_time_picker.get_time()
        end_time = self.end_time_picker.get_time()
        
        start_hours = start_time.hour() + start_time.minute() / 60.0
        end_hours = end_time.hour() + end_time.minute() / 60.0
        
        hours_diff = end_hours - start_hours
        if hours_diff < 0:
            hours_diff += 24
            
        self.hours_display.setText(f"{hours_diff:.2f} hours")

    def _save_settings(self):
        # 1. Save General Settings
        self.data_manager.project_name = self.project_name_input.text()
        
        qdate = self.project_start_date_input.date()
        new_start_date = datetime(qdate.year(), qdate.month(), qdate.day())
        self.settings.project_start_date = new_start_date
        
        self.settings.currency = self.currency_combo.currentData()
        
        # 2. Save Calendar Settings
        start_time = self.start_time_picker.get_time()
        end_time = self.end_time_picker.get_time()
        start_str = start_time.toString("HH:mm")
        end_str = end_time.toString("HH:mm")
        
        self.calendar_manager.set_working_hours(start_str, end_str)
        
        working_days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
        self.calendar_manager.set_working_days(working_days)
        
        # 3. Save Holiday Settings
        new_custom_holidays = []
        for row in range(self.holidays_table.rowCount()):
            name_item = self.holidays_table.item(row, 0)
            name = name_item.text() if name_item else ""
            
            start_widget = self.holidays_table.cellWidget(row, 1)
            start = start_widget.date().toString("yyyy-MM-dd") if start_widget else ""
            
            end_widget = self.holidays_table.cellWidget(row, 2)
            end = end_widget.date().toString("yyyy-MM-dd") if end_widget else ""
            
            recurring_container = self.holidays_table.cellWidget(row, 3)
            is_recurring = False
            if recurring_container:
                cb = recurring_container.findChild(QCheckBox)
                if cb:
                    is_recurring = cb.isChecked()
            
            comment_item = self.holidays_table.item(row, 4)
            comment = comment_item.text() if comment_item else ""
            
            if start: # Basic validation
                new_custom_holidays.append({
                    "name": name,
                    "start_date": start,
                    "end_date": end or start,
                    "comment": comment,
                    "is_recurring": is_recurring
                })
        
        self.calendar_manager.custom_holidays = new_custom_holidays
        self.calendar_manager._sync_holidays()

        # 4. Save Interface Settings
        self.settings.default_date_format = self.date_format_combo.currentData()
        self.settings.duration_unit = self.duration_unit_combo.currentData()
        
        # Update App Font Size only if changed to avoid accidental resets
        new_font_size = self.font_size_spin.value()
        current_font_size = getattr(self.settings, 'app_font_size', 9)
        try:
            current_font_size = int(current_font_size)
        except (ValueError, TypeError):
            current_font_size = 9
            
        if new_font_size != current_font_size:
             self.settings.set_app_font_size(new_font_size)
        
        self.accept()
