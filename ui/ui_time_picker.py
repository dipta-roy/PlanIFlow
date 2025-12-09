"""
Interactive Time Picker Widget for selecting time with sliders
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTimeEdit, 
                             QLabel, QSlider, QSpinBox)
from PyQt6.QtCore import QTime, Qt, pyqtSignal


class TimePickerWidget(QWidget):
    """Interactive time picker with sliders"""
    
    timeChanged = pyqtSignal(QTime)
    
    def __init__(self, initial_time: QTime = None, parent=None):
        super().__init__(parent)
        self.selected_time = initial_time if initial_time else QTime(8, 0)
        self._create_ui()
        
    def _create_ui(self):
        """Create the time picker UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Digital time display and edit
        time_layout = QHBoxLayout()
        
        # Time edit widget (interactive)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(self.selected_time)
        self.time_edit.setMinimumWidth(120)
        self.time_edit.timeChanged.connect(self._on_time_edit_changed)
        
        time_layout.addStretch()
        time_layout.addWidget(QLabel("Time:"))
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        
        layout.addLayout(time_layout)
        
        # Hour slider
        hour_layout = QHBoxLayout()
        hour_layout.addWidget(QLabel("Hour:"))
        
        self.hour_slider = QSlider(Qt.Orientation.Horizontal)
        self.hour_slider.setRange(0, 23)
        self.hour_slider.setValue(self.selected_time.hour())
        self.hour_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.hour_slider.setTickInterval(1)
        self.hour_slider.valueChanged.connect(self._on_hour_changed)
        hour_layout.addWidget(self.hour_slider)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(self.selected_time.hour())
        self.hour_spin.valueChanged.connect(self._on_hour_spin_changed)
        hour_layout.addWidget(self.hour_spin)
        
        layout.addLayout(hour_layout)
        
        # Minute slider
        minute_layout = QHBoxLayout()
        minute_layout.addWidget(QLabel("Minute:"))
        
        self.minute_slider = QSlider(Qt.Orientation.Horizontal)
        self.minute_slider.setRange(0, 59)
        self.minute_slider.setValue(self.selected_time.minute())
        self.minute_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.minute_slider.setTickInterval(5)
        self.minute_slider.valueChanged.connect(self._on_minute_changed)
        minute_layout.addWidget(self.minute_slider)
        
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(self.selected_time.minute())
        self.minute_spin.valueChanged.connect(self._on_minute_spin_changed)
        minute_layout.addWidget(self.minute_spin)
        
        layout.addLayout(minute_layout)
        
    def _on_time_edit_changed(self, time: QTime):
        """Handle time edit changes"""
        self.selected_time = time
        self._update_controls()
        self.timeChanged.emit(self.selected_time)
        
    def _on_hour_changed(self, value: int):
        """Handle hour slider changes"""
        self.selected_time.setHMS(value, self.selected_time.minute(), 0)
        self._update_controls()
        self.timeChanged.emit(self.selected_time)
        
    def _on_hour_spin_changed(self, value: int):
        """Handle hour spinbox changes"""
        self.selected_time.setHMS(value, self.selected_time.minute(), 0)
        self._update_controls()
        self.timeChanged.emit(self.selected_time)
        
    def _on_minute_changed(self, value: int):
        """Handle minute slider changes"""
        self.selected_time.setHMS(self.selected_time.hour(), value, 0)
        self._update_controls()
        self.timeChanged.emit(self.selected_time)
        
    def _on_minute_spin_changed(self, value: int):
        """Handle minute spinbox changes"""
        self.selected_time.setHMS(self.selected_time.hour(), value, 0)
        self._update_controls()
        self.timeChanged.emit(self.selected_time)
        
    def _update_controls(self):
        """Update all controls to match selected time"""
        # Block signals to prevent loops
        self.time_edit.blockSignals(True)
        self.hour_slider.blockSignals(True)
        self.hour_spin.blockSignals(True)
        self.minute_slider.blockSignals(True)
        self.minute_spin.blockSignals(True)
        
        # Update values
        self.time_edit.setTime(self.selected_time)
        self.hour_slider.setValue(self.selected_time.hour())
        self.hour_spin.setValue(self.selected_time.hour())
        self.minute_slider.setValue(self.selected_time.minute())
        self.minute_spin.setValue(self.selected_time.minute())
        
        # Unblock signals
        self.time_edit.blockSignals(False)
        self.hour_slider.blockSignals(False)
        self.hour_spin.blockSignals(False)
        self.minute_slider.blockSignals(False)
        self.minute_spin.blockSignals(False)
        
    def get_time(self) -> QTime:
        """Get the currently selected time"""
        return self.selected_time
    
    def set_time(self, time: QTime):
        """Set the time"""
        self.selected_time = time
        self._update_controls()
