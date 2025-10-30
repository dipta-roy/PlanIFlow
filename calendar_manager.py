"""
Calendar Manager - Handles work hours, holidays, and working days
"""

from datetime import datetime, timedelta
from typing import List, Set, Dict, Any

class CalendarManager:
    """Manages working calendar, holidays, and work hours"""
    
    def __init__(self):
        # Default working days (0 = Monday, 6 = Sunday)
        self.working_days: Set[int] = {0, 1, 2, 3, 4}  # Mon-Fri
        
        # Default hours per day
        self.hours_per_day: float = 8.0
        
        # Non-working days (holidays, special dates)
        self.non_working_days: Set[str] = set()  # ISO date strings
    
    def is_working_day(self, date: datetime) -> bool:
        """Check if a given date is a working day"""
        # Check if it's a weekend
        if date.weekday() not in self.working_days:
            return False
        
        # Check if it's a holiday
        date_str = date.strftime('%Y-%m-%d')
        if date_str in self.non_working_days:
            return False
        
        return True
    
    def add_holiday(self, date: datetime):
        """Add a non-working day"""
        date_str = date.strftime('%Y-%m-%d')
        self.non_working_days.add(date_str)
    
    def remove_holiday(self, date: datetime):
        """Remove a non-working day"""
        date_str = date.strftime('%Y-%m-%d')
        self.non_working_days.discard(date_str)
    
    def set_working_days(self, days: List[int]):
        """Set working days (0-6, Mon-Sun)"""
        self.working_days = set(days)
    
    def set_hours_per_day(self, hours: float):
        """Set default working hours per day"""
        self.hours_per_day = max(0.0, hours)
    
    def calculate_working_days(self, start_date: datetime, end_date: datetime) -> int:
        """Calculate number of working days between two dates"""
        working_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_working_day(current_date):
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def calculate_working_hours(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate total working hours between two dates"""
        working_days = self.calculate_working_days(start_date, end_date)
        return working_days * self.hours_per_day
    
    def get_next_working_day(self, date: datetime) -> datetime:
        """Get the next working day after the given date"""
        next_day = date + timedelta(days=1)
        while not self.is_working_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def add_working_days(self, start_date: datetime, days: int) -> datetime:
        """Add a number of working days to a date"""
        current_date = start_date
        days_added = 0
        
        while days_added < days:
            current_date += timedelta(days=1)
            if self.is_working_day(current_date):
                days_added += 1
        
        return current_date
    
    def to_dict(self) -> Dict[str, Any]:
        """Export calendar settings to dictionary"""
        return {
            'working_days': list(self.working_days),
            'hours_per_day': self.hours_per_day,
            'non_working_days': list(self.non_working_days)
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Import calendar settings from dictionary"""
        self.working_days = set(data.get('working_days', [0, 1, 2, 3, 4]))
        self.hours_per_day = data.get('hours_per_day', 8.0)
        self.non_working_days = set(data.get('non_working_days', []))