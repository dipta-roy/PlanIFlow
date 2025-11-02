"""
Settings Manager - Manages project-wide settings including duration units
"""

from typing import Dict, Any
from enum import Enum
from datetime import datetime

class DurationUnit(Enum):
    """Duration unit options"""
    DAYS = "days"
    HOURS = "hours"

class DateFormat(Enum):
    """Date format options"""
    DD_MM_YYYY = "dd-mm-yyyy"
    DD_MMM_YYYY = "dd-MMM-yyyy"
    YYYY_MM_DD = "yyyy-mm-dd"

class ProjectSettings:
    """Project-wide settings"""
    
    def __init__(self):
        self.duration_unit = DurationUnit.DAYS
        self.project_start_date = None # New attribute
        self.default_date_format = DateFormat.YYYY_MM_DD # New attribute
        self._listeners = []  # Callbacks for setting changes
    
    def set_duration_unit(self, unit: DurationUnit):
        """Set duration unit and notify listeners"""
        old_unit = self.duration_unit
        self.duration_unit = unit
        
        # Notify all listeners of the change
        for listener in self._listeners:
            listener(old_unit, unit)
    
    def set_default_date_format(self, date_format: DateFormat):
        """Set default date format"""
        self.default_date_format = date_format
    
    def add_listener(self, callback):
        """Add a listener for settings changes"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback):
        """Remove a listener""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def get_duration_label(self) -> str:
        """Get label for duration column"""
        if self.duration_unit == DurationUnit.DAYS:
            return "Duration (days)"
        else:
            return "Duration (hours)"
    
    def get_duration_suffix(self) -> str:
        """Get suffix for duration display"""
        if self.duration_unit == DurationUnit.DAYS:
            return " days"
        else:
            return " hours"
    
    def to_dict(self) -> Dict[str, Any]:
        """Export settings to dictionary"""
        return {
            'duration_unit': self.duration_unit.value,
            'project_start_date': self.project_start_date.strftime('%Y-%m-%d') if self.project_start_date else None,
            'default_date_format': self.default_date_format.value
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Import settings from dictionary"""
        unit_str = data.get('duration_unit', 'days')
        try:
            self.duration_unit = DurationUnit(unit_str)
        except ValueError:
            self.duration_unit = DurationUnit.DAYS  # Default fallback
        
        start_date_str = data.get('project_start_date')
        if start_date_str:
            from datetime import datetime
            self.project_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            self.project_start_date = None
        
        date_format_str = data.get('default_date_format', DateFormat.YYYY_MM_DD.value)
        try:
            self.default_date_format = DateFormat(date_format_str)
        except ValueError:
            self.default_date_format = DateFormat.YYYY_MM_DD # Default fallback (assign enum member directly)
