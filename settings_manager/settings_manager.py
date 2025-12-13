"""
Settings Manager - Manages project-wide settings including duration units
"""

from typing import Dict, Any
from enum import Enum
from datetime import datetime
import logging

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
        self.project_start_date = None
        self.default_date_format = DateFormat.YYYY_MM_DD
        self.app_font_size = 9 # Default application font size
        self._listeners = []  # Callbacks for setting changes
    
    def reset_defaults(self):
        """Reset settings to application defaults"""
        self.duration_unit = DurationUnit.DAYS
        self.project_start_date = datetime.now()
        self.default_date_format = DateFormat.YYYY_MM_DD
        self.app_font_size = 9
        
        # Notify listeners
        for listener in self._listeners:
            listener(None, None) # Generic update
    
    def get_strftime_format(self) -> str:
        """Returns the strftime compatible format string for the current default_date_format."""
        if self.default_date_format == DateFormat.DD_MM_YYYY:
            return "%d-%m-%Y %H:%M:%S"
        elif self.default_date_format == DateFormat.DD_MMM_YYYY:
            return "%d-%b-%Y %H:%M:%S"
        elif self.default_date_format == DateFormat.YYYY_MM_DD:
            return "%Y-%m-%dT%H:%M:%S"
        return "%Y-%m-%dT%H:%M:%S" # Default fallback

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

    def set_app_font_size(self, size: int):
        """Set application font size and notify listeners"""
        self.app_font_size = size
        # We can reuse the same listener mechanism or add a specific one. 
        # existing listeners expect (old_unit, new_unit) for duration changes.
        # It's better to update listeners to handle different types of changes, 
        # or just assume listeners re-read settings.
        # For simplicity, let's just trigger a full update where needed.
        # But wait, add_listener implementation suggests it's generic?
        # The current implementation of set_duration_unit passes old/new values.
        # Let's emit a generic change event or similar.
        # For now, let's just update the value. The UI will need to observe this.
    
    def add_listener(self, callback):
        """Add a listener for settings changes"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback):
        """Remove a listener"""
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
        data = {
            'duration_unit': self.duration_unit.value,
            'default_date_format': self.default_date_format.value,
            'app_font_size': self.app_font_size
        }
        if self.project_start_date:
            data['project_start_date'] = self.project_start_date.strftime(self.get_strftime_format())
        return data
    
    def from_dict(self, data: Dict[str, Any]):
        """Import settings from dictionary"""
        unit_str = data.get('duration_unit', 'days')
        try:
            self.duration_unit = DurationUnit(unit_str)
        except ValueError:
            self.duration_unit = DurationUnit.DAYS  # Default fallback
            
        self.app_font_size = data.get('app_font_size', 9)
        
        start_date_str = data.get('project_start_date')
        if start_date_str:
            # List of common date formats to try
            possible_formats = [
                '%Y-%m-%dT%H:%M:%S',  # ISO format (default for YYYY_MM_DD)
                '%d-%m-%Y %H:%M:%S',  # DD-MM-YYYY
                '%d-%b-%Y %H:%M:%S',  # DD-MMM-YYYY
                '%Y-%m-%d %H:%M:%S',  # YYYY-MM-DD (with time)
                '%Y-%m-%d',           # YYYY-MM-DD (no time)
                '%d-%m-%Y',           # DD-MM-YYYY (no time)
                '%d-%b-%Y'            # DD-MMM-YYYY (no time)
            ]
            
            parsed_date = None
            for fmt in possible_formats:
                try:
                    parsed_date = datetime.strptime(start_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date:
                self.project_start_date = parsed_date
            else:
                # If none of the formats work, log a warning or raise an error
                logging.warning(f"Could not parse project_start_date '{start_date_str}' with any known format.")
                self.project_start_date = None
        else:
            self.project_start_date = None
        
        date_format_str = data.get('default_date_format', DateFormat.YYYY_MM_DD.value)
        try:
            self.default_date_format = DateFormat(date_format_str)
        except ValueError:
            self.default_date_format = DateFormat.YYYY_MM_DD # Default fallback (assign enum member directly)
