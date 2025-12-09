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
        
        # Working hours configuration (stored as hour:minute in 24h format)
        self.working_hours_start: str = "08:00"  # 8:00 AM
        self.working_hours_end: str = "16:00"    # 4:00 PM (8 hours later)
        
        # Default hours per day (calculated from working hours)
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
    
    def set_working_hours(self, start_time: str, end_time: str):
        """Set working hours start and end times (format: HH:MM)"""
        self.working_hours_start = start_time
        self.working_hours_end = end_time
        # Recalculate hours per day
        self.hours_per_day = self._calculate_hours_from_times()
    
    def _calculate_hours_from_times(self) -> float:
        """Calculate hours per day from start and end times"""
        try:
            start_parts = self.working_hours_start.split(':')
            end_parts = self.working_hours_end.split(':')
            
            start_hours = int(start_parts[0]) + int(start_parts[1]) / 60.0
            end_hours = int(end_parts[0]) + int(end_parts[1]) / 60.0
            
            # Calculate difference
            hours_diff = end_hours - start_hours
            
            # Handle case where end is before start (crosses midnight)
            if hours_diff < 0:
                hours_diff += 24
            
            return max(0.0, hours_diff)
            return max(0.0, hours_diff)
        except:
            return 8.0  # Default fallback
            
    def get_working_start_time(self) -> tuple[int, int]:
        """Get working start time as (hour, minute)"""
        try:
            parts = self.working_hours_start.split(':')
            return int(parts[0]), int(parts[1])
        except:
            return 8, 0
            
    def get_working_end_time(self) -> tuple[int, int]:
        """Get working end time as (hour, minute)"""
        try:
            parts = self.working_hours_end.split(':')
            return int(parts[0]), int(parts[1])
        except:
            return 16, 0
    
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
        total_hours = 0.0
        
        start_h, start_m = self.get_working_start_time()
        end_h, end_m = self.get_working_end_time()
        
        # Normalize to just date for iteration
        current_date_iter = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_limit = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Determine working interval for a day relative to that day's midnight
        # work_start_td = timedelta(hours=start_h, minutes=start_m)
        # work_end_td = timedelta(hours=end_h, minutes=end_m)
        
        while current_date_iter <= end_date_limit:
            # Check if this day is a working day
            # We can pick a time (e.g. noon) to check, or just the date object if is_working_day handles it
            check_dt = current_date_iter.replace(hour=12) 
            if self.is_working_day(check_dt, resource_exceptions):
                
                # Define working window for this specific date
                daily_work_start = current_date_iter.replace(hour=start_h, minute=start_m)
                daily_work_end = current_date_iter.replace(hour=end_h, minute=end_m)
                
                # Handle overnight shifts? assuming day shift for now (end > start)
                if daily_work_end < daily_work_start:
                    daily_work_end += timedelta(days=1)
                
                # Determine overlap of task duration with today's working window
                # Task interval: [max(start_date, daily_work_start), min(end_date, daily_work_end)]
                
                overlap_start = max(start_date, daily_work_start)
                overlap_end = min(end_date, daily_work_end)
                
                if overlap_start < overlap_end:
                     total_hours += (overlap_end - overlap_start).total_seconds() / 3600.0
                     
            current_date_iter += timedelta(days=1)
            
        return total_hours
    
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
        """Add hours to a date, respecting working hours and skipping non-working days"""
        current_dt = start_date
        hours_remaining = hours
        
        # Get configured working hours
        start_h, start_m = self.get_working_start_time()
        end_h, end_m = self.get_working_end_time()
        
        try:
            # Normalize times to timedelta from midnight
            work_start_td = timedelta(hours=start_h, minutes=start_m)
            work_end_td = timedelta(hours=end_h, minutes=end_m)
            
            # If work end is smaller than start (night shift), handle simply by assuming full 24h for now or error?
            # Supporting typical day shifts for now.
            if work_end_td <= work_start_td:
                # Fallback to simple addition if invalid range
                return current_dt + timedelta(hours=hours)

            while hours_remaining > 0:
                # 1. Ensure current_dt is inside working hours
                
                # If non-working day, move to next working day start
                if not self.is_working_day(current_dt):
                    current_dt = self.get_next_working_day(current_dt)
                    current_dt = current_dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                    continue

                # Get time of day
                current_time_td = timedelta(hours=current_dt.hour, minutes=current_dt.minute, seconds=current_dt.second)
                
                # If before start, move to start
                if current_time_td < work_start_td:
                    current_dt = current_dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                    current_time_td = work_start_td
                
                # If after end, move to next working day start
                if current_time_td >= work_end_td:
                    current_dt = self.get_next_working_day(current_dt)
                    current_dt = current_dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                    continue
                
                # 2. Calculate available hours today
                time_until_end = (work_end_td - current_time_td).total_seconds() / 3600.0
                
                if hours_remaining <= time_until_end + 0.0001: # Epsilon for float comparison
                    # Duration fits in today
                    current_dt += timedelta(hours=hours_remaining)
                    return current_dt
                else:
                    # Use up remainder of today
                    hours_remaining -= time_until_end
                    # Move to start of next working day
                    current_dt = self.get_next_working_day(current_dt)
                    current_dt = current_dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            
            return current_dt
            
        except Exception as e:
            # Fallback
            print(f"Error in add_working_hours: {e}")
            return start_date + timedelta(hours=hours)

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
            'non_working_days': list(self.non_working_days),
            'working_hours_start': self.working_hours_start,
            'working_hours_end': self.working_hours_end
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Import calendar settings from dictionary"""
        self.working_days = set(data.get('working_days', [0, 1, 2, 3, 4]))
        self.non_working_days = set(data.get('non_working_days', []))
        
        # Backward compatibility: use hours_per_day if available
        self.hours_per_day = data.get('hours_per_day', 8.0)
        
        if 'working_hours_start' in data:
            self.working_hours_start = data['working_hours_start']
        else:
            self.working_hours_start = '08:00'
        
        if 'working_hours_end' in data:
            self.working_hours_end = data['working_hours_end']
        else:
            # Fallback: calculate end time from start and hours_per_day
            try:
                start_h, start_m = map(int, self.working_hours_start.split(':'))
                total_minutes = int(start_h * 60 + start_m + (self.hours_per_day * 60))
                
                # Handle overflow (next day) by wrapping around 24h
                end_h = (total_minutes // 60) % 24
                end_m = total_minutes % 60
                self.working_hours_end = f"{end_h:02d}:{end_m:02d}"
            except Exception:
                 self.working_hours_end = '16:00'
        
        # Ensure consistency
        self.hours_per_day = self._calculate_hours_from_times()
