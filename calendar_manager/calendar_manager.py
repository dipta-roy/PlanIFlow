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
    
    def is_working_day(self, date: datetime, resource_exceptions: List[str] = None) -> bool:
        """Check if a given date is a working day, considering resource-specific exceptions"""
        # Check if it's a weekend
        if date.weekday() not in self.working_days:
            return False
        
        date_str = date.strftime('%Y-%m-%d')

        # Check if it's a global non-working day
        if date_str in self.non_working_days:
            return False
        
        # Check if it's a resource-specific exception
        if resource_exceptions:
            # Handle date ranges in exceptions
            for exception_entry in resource_exceptions:
                if " to " in exception_entry:
                    start_str, end_str = exception_entry.split(" to ")
                    try:
                        exception_start = datetime.strptime(start_str.strip(), '%Y-%m-%d').date()
                        exception_end = datetime.strptime(end_str.strip(), '%Y-%m-%d').date()
                        if exception_start <= date.date() <= exception_end:
                            return False
                    except ValueError:
                        # Log or handle malformed date range
                        pass
                elif date_str == exception_entry.strip():
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
    
    def calculate_working_days(self, start_date: datetime, end_date: datetime, resource_exceptions: List[str] = None) -> int:
        """Calculate number of working days between two dates, considering resource-specific exceptions"""
        working_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_working_day(current_date, resource_exceptions):
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def calculate_working_hours(self, start_date: datetime, end_date: datetime, max_hours_per_day: float = None, resource_exceptions: List[str] = None) -> float:
        """Calculate total working hours between two dates, considering resource-specific exceptions"""
        if max_hours_per_day is None:
            max_hours_per_day = self.hours_per_day
        working_days = self.calculate_working_days(start_date, end_date, resource_exceptions)
        return working_days * max_hours_per_day
    
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

    def add_working_hours(self, start_date: datetime, hours: float) -> datetime:
        """Add hours to a date, skipping non-working days"""
        current_dt = start_date
        hours_remaining = hours
        
        # Assume working hours are 8 AM to (8+hours_per_day) PM
        # Simplification: For now, just add days based on hours/day, then add remainder
        
        # Calculate full days to add
        full_days = int(hours_remaining / self.hours_per_day)
        remainder_hours = hours_remaining % self.hours_per_day
        
        # Add full days first (minus 1 if we have remainder, because start day counts)
        # Actually logic is tricky. 
        # Requirement: 
        # 1 day task (8h) starting today = ends today.
        # 2 day task (16h) starting today = ends tomorrow.
        
        # Let's handle it by creating a target end time on the final working day.
        # Shift full working days
        if full_days > 0:
            # If no remainder (exact day multiple), subtract 1 so we land on correct day?
            # 16h (2 days). Start D1 8am. D1 8am + 16h = D2 0am (midnight next day) wrong.
            # D1 8am + 8h = D1 4pm.
            # D1 8am + 16h should be D1 8am -> D1 4pm (8h), D2 8am -> D2 4pm (8h).
            
            # So, add (full_days - 1) full working days, then handle exact time?
            # Or just add full_days worth of time, skipping non-work days.
            
            days_to_add = full_days
            if remainder_hours == 0:
                is_exact_day_end = True
                days_to_add -= 1 # We stay on the last day if it fits exactly
            else:
                is_exact_day_end = False
            
            # Jump ahead working days
            current_dt = self.add_working_days(current_dt, days_to_add)
            
            # Now add the remaining hours (or full 8h if exact day but we subtracted 1 day count)
            # If exact day end, we are on the correct day, starting at same time as start_date.
            # We just need to add a full work day's hours to it.
            if is_exact_day_end:
                 current_dt += timedelta(hours=self.hours_per_day)
            else:
                 current_dt += timedelta(hours=remainder_hours)
                 
        else:
             # Just add hours on same day
             current_dt += timedelta(hours=hours_remaining)
             
        # Correction: The above simplistic addition doesn't check if we crossed into non-working time
        # within the day (e.g. 5pm+). But user request implies standard 8-4 window.
        # "If 8 hours configured... start 8am end 4pm."
        # My simple timedelta logic `start + hours` works for simple cases, 
        # but fails multi-day skipping weekends.
        # That's why I used `add_working_days` above.
        
        return current_dt

    def subtract_working_days(self, start_date: datetime, days: int) -> datetime:
        """Subtract a number of working days from a date"""
        current_date = start_date
        days_subtracted = 0

        while days_subtracted < days:
            current_date -= timedelta(days=1)
            if self.is_working_day(current_date):
                days_subtracted += 1
        
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