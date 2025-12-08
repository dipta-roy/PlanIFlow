from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from settings_manager.settings_manager import DurationUnit, DateFormat

class DependencyType(Enum):
    """Dependency relationship types"""
    FS = "Finish-to-Start"  # Successor starts after predecessor finishes
    SS = "Start-to-Start"   # Successor starts when predecessor starts
    FF = "Finish-to-Finish" # Successor finishes when predecessor finishes
    SF = "Start-to-Finish"  # Successor finishes when predecessor starts

class TaskStatus(Enum):
    """Task status based on dates and completion"""
    OVERDUE = ("red", "Overdue")
    IN_PROGRESS = ("green", "In Progress")
    UPCOMING = ("grey", "Upcoming")
    COMPLETED = ("blue", "Completed")

class ScheduleType(Enum):
    """Scheduling type for tasks"""
    AUTO_SCHEDULED = "Auto Scheduled"
    MANUALLY_SCHEDULED = "Manually Scheduled"

class Task:
    """Task data model with hierarchy and dependency types"""
    
    _next_id = 1
    
    def __init__(self, name: str, start_date: datetime, end_date: datetime,
                 percent_complete: int = 0, predecessors: List[Tuple[int, str, int]] = None,
                 assigned_resources: List[str] = None, notes: str = "",
                 task_id: int = None, parent_id: int = None, is_summary: bool = False,
                 is_milestone: bool = False, wbs: str = None,
                 schedule_type: ScheduleType = ScheduleType.AUTO_SCHEDULED,
                 font_family: str = "Arial", font_size: int = 10, font_color: str = "#000000",
                 font_bold: bool = None, font_italic: bool = None, font_underline: bool = False,
                 background_color: str = "#FFFFFF"):
        """
        Initialize task with hierarchy support
        
        Args:
            predecessors: List of tuples [(task_id, dependency_type), ...]
            parent_id: ID of parent task (None for top-level tasks)
            is_summary: True if this is a summary task with subtasks
        """
        self.id = task_id if task_id is not None else Task._next_id
        if task_id is None:
            Task._next_id += 1
        else:
            Task._next_id = max(Task._next_id, task_id + 1)
        
        self.is_milestone = is_milestone
        self.is_summary = is_summary
        self.parent_id = parent_id
        self.wbs = wbs
        self.schedule_type = schedule_type
        
        # Now set other attributes
        self.name = name
        self.start_date = start_date
        
        # MILESTONE LOGIC: If milestone, end date = start date
        if self.is_milestone:
            self.end_date = start_date
        else:
            self.end_date = end_date
        
        self.percent_complete = percent_complete
        
        # Convert old format to new format if needed
        if predecessors and len(predecessors) > 0:
            if isinstance(predecessors[0], tuple):
                if len(predecessors[0]) == 3:
                    self.predecessors = predecessors
                else:
                    self.predecessors = [(pred_id, dep_type, 0) for pred_id, dep_type in predecessors]
            else:
                self.predecessors = [(pred_id, DependencyType.FS.name, 0) for pred_id in predecessors]
        else:
            self.predecessors = predecessors or []

        # Handle assigned_resources with allocation
        if assigned_resources and len(assigned_resources) > 0 and isinstance(assigned_resources[0], str):
            # Backward compatibility: convert list of strings to list of tuples
            self.assigned_resources = [(name, 100) for name in assigned_resources]
        else:
            self.assigned_resources = assigned_resources or []
        
        self.notes = notes
        
        # Font styling properties
        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color
        
        # Auto-apply formatting based on task type if not explicitly set
        # Summary tasks should be bold by default (unless explicitly set to False)
        if font_bold is None:
            self.font_bold = True if is_summary else False
        else:
            self.font_bold = font_bold
        
        # Milestones should be italic by default (unless explicitly set to False)
        if font_italic is None:
            self.font_italic = True if is_milestone else False
        else:
            self.font_italic = font_italic
            
        self.font_underline = font_underline
        self.background_color = background_color
        
        # Store original dates
        self._original_start = start_date
        self._original_end = end_date
    
        # Hierarchy fields
        self.parent_id = parent_id
        self.is_summary = is_summary
        self._original_start = start_date  # Store original for summary tasks
        self._original_end = end_date

        # Critical Path Analysis fields
        self.early_start: Optional[datetime] = None
        self.early_finish: Optional[datetime] = None
        self.late_start: Optional[datetime] = None
        self.late_finish: Optional[datetime] = None
        self.slack: Optional[timedelta] = None
        self.is_critical: bool = False
    
    @property
    def duration(self) -> int:
        """Calculate duration in days"""
        if self.is_milestone:
            return 0
        return (self.end_date - self.start_date).days + 1
    
    def get_status(self) -> TaskStatus:
        """Calculate task status based on dates and completion"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Completed tasks
        if self.percent_complete == 100:
            return TaskStatus.COMPLETED
        
        # Overdue tasks
        if self.end_date < today and self.percent_complete < 100:
            return TaskStatus.OVERDUE
        
        # In progress tasks
        if self.start_date <= today < self.end_date:
            return TaskStatus.IN_PROGRESS
        
        # Upcoming tasks
        return TaskStatus.UPCOMING
    
    def get_status_color(self) -> str:
        """Get color for current status"""
        return self.get_status().value[0]
    
    def get_status_text(self) -> str:
        """Get text description for current status"""
        return self.get_status().value[1]
    
    def get_level(self, all_tasks: List['Task']) -> int:
        """Calculate nesting level (0 = top level)"""
        if self.parent_id is None:
            return 0
        
        parent = next((t for t in all_tasks if t.id == self.parent_id), None)
        if parent:
            return parent.get_level(all_tasks) + 1
        return 0
    
    def _get_date_format_string(self, date_format: DateFormat) -> str:
        if date_format == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y %H:%M:%S'
        elif date_format == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y %H:%M:%S'
        else: # DateFormat.YYYY_MM_DD
            return '%Y-%m-%dT%H:%M:%S'

    def to_dict(self, date_format: DateFormat = None) -> Dict[str, Any]:
        if date_format is None:
            date_format = DateFormat.YYYY_MM_DD # Default for internal use
        format_string = self._get_date_format_string(date_format)
        
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.strftime(format_string),
            'end_date': self.end_date.strftime(format_string),
            'percent_complete': self.percent_complete,
            'predecessors': self.predecessors,
            'assigned_resources': self.assigned_resources,
            'notes': self.notes,
            'parent_id': self.parent_id,
            'is_summary': self.is_summary,
            'is_milestone': self.is_milestone,
            'wbs': self.wbs,
            'schedule_type': self.schedule_type.value,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'font_bold': self.font_bold,
            'font_italic': self.font_italic,
            'font_underline': self.font_underline,
            'background_color': self.background_color
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any], date_format: DateFormat = None) -> 'Task':
        """Create task from dictionary with backward compatibility"""
        if date_format is None:
            date_format = DateFormat.YYYY_MM_DD # Default for internal use
        
        # Helper to get format string
        def _get_format_string(df: DateFormat) -> str:
            if df == DateFormat.DD_MM_YYYY:
                return '%d-%m-%Y %H:%M:%S'
            elif df == DateFormat.DD_MMM_YYYY:
                return '%d-%b-%Y %H:%M:%S'
            else: # DateFormat.YYYY_MM_DD
                return '%Y-%m-%dT%H:%M:%S'
        
        format_string = _get_format_string(date_format)

        # Handle old format predecessors
        predecessors = data.get('predecessors', [])
        new_predecessors = []
        if predecessors:
            for pred in predecessors:
                if isinstance(pred, (list, tuple)):
                    if len(pred) == 2:
                        new_predecessors.append((pred[0], pred[1], 0))
                    elif len(pred) == 3:
                        new_predecessors.append(tuple(pred))
                    else: # Should not happen with good data, but as a fallback
                        new_predecessors.append((pred[0], DependencyType.FS.name, 0))
                else:
                    new_predecessors.append((pred, DependencyType.FS.name, 0))
        predecessors = new_predecessors
        
        # Handle assigned_resources with allocation for backward compatibility
        assigned_resources = data.get('assigned_resources', [])
        if assigned_resources and isinstance(assigned_resources[0], str):
            assigned_resources = [(name, 100) for name in assigned_resources]

        # Parse start_date
        start_date_str = data['start_date']
        parsed_start_date = None
        for fmt in [format_string, '%d-%m-%Y %H:%M:%S', '%d-%b-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
            try:
                parsed_start_date = datetime.strptime(start_date_str, fmt)
                break
            except ValueError:
                continue
        if parsed_start_date is None:
            raise ValueError(f"Could not parse start date '{start_date_str}' with any known format.")

        # Parse end_date
        end_date_str = data['end_date']
        parsed_end_date = None
        for fmt in [format_string, '%d-%m-%Y %H:%M:%S', '%d-%b-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
            try:
                parsed_end_date = datetime.strptime(end_date_str, fmt)
                break
            except ValueError:
                continue
        if parsed_end_date is None:
            raise ValueError(f"Could not parse end date '{end_date_str}' with any known format.")

        schedule_type_str = data.get('schedule_type', ScheduleType.AUTO_SCHEDULED.value)
        try:
            schedule_type = ScheduleType(schedule_type_str)
        except ValueError:
            schedule_type = ScheduleType.AUTO_SCHEDULED # Default fallback
            
        return Task(
            name=data['name'],
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            percent_complete=data.get('percent_complete', 0),
            predecessors=predecessors, # Use the processed predecessors
            assigned_resources=assigned_resources, # Use the processed assigned_resources
            notes=data.get('notes', ''),
            task_id=data.get('id'), # Pass task_id from data
            parent_id=data.get('parent_id'), # Pass parent_id from data
            is_summary=data.get('is_summary', False), # Pass is_summary from data
            is_milestone=data.get('is_milestone', False), # Pass is_milestone from data
            wbs=data.get('wbs'), # Pass wbs from data
            schedule_type=schedule_type,
            # Font styling with defaults for backward compatibility
            font_family=data.get('font_family', 'Arial'),
            font_size=data.get('font_size', 10),
            font_color=data.get('font_color', '#000000'),
            font_bold=data.get('font_bold', None),  # Use None to trigger automatic formatting
            font_italic=data.get('font_italic', None),  # Use None to trigger automatic formatting
            font_underline=data.get('font_underline', False),
            background_color=data.get('background_color', '#FFFFFF')
        )
    def calculate_duration_days(self, calendar_manager=None) -> int:
        """Calculate duration in working days"""
        if self.is_milestone:
            return 0
        
        if calendar_manager:
            return calendar_manager.calculate_working_days(self.start_date, self.end_date)
        else:
            return (self.end_date - self.start_date).days + 1
            
    def calculate_duration_hours(self, calendar_manager=None) -> float:
        """Calculate duration in working hours"""
        if self.is_milestone:
            return 0.0
        
        if calendar_manager:
            return calendar_manager.calculate_working_hours(self.start_date, self.end_date)
        else:
            days = (self.end_date - self.start_date).days + 1
            return days * 8.0
    
    def get_duration(self, unit: DurationUnit, calendar_manager=None) -> float:
        """Get duration in specified unit"""
        if self.is_milestone:
            return 0.0
        
        if unit == DurationUnit.DAYS:
            return self.calculate_duration_days(calendar_manager)
        else:
            return self.calculate_duration_hours(calendar_manager)
    
    def set_duration_and_update_end(self, duration: float, unit: DurationUnit, 
                                    calendar_manager=None):
        """Set duration and update end date accordingly"""
        # MILESTONES IGNORE DURATION CHANGES
        if self.is_milestone:
            self.end_date = self.start_date
            return
        
        if unit == DurationUnit.DAYS:
            if calendar_manager:
                start_is_working = calendar_manager.is_working_day(self.start_date)
                
                # A task of N days ends N-1 working days after it starts.
                # We subtract 1 if the start day is a working day, as it counts as the first day.
                days_to_add = int(duration) - (1 if start_is_working else 0)
                if days_to_add < 0: days_to_add = 0 # Ensure non-negative
                
                end_day = calendar_manager.add_working_days(self.start_date, days_to_add)
                
                # The end time should correspond to the end of the work day.
                # Assuming the workday starts at self.start_date's time and lasts for hours_per_day.
                end_time_on_day = self.start_date + timedelta(hours=calendar_manager.hours_per_day)

                self.end_date = end_day.replace(
                    hour=end_time_on_day.hour, 
                    minute=end_time_on_day.minute, 
                    second=end_time_on_day.second,
                    microsecond=end_time_on_day.microsecond
                )
            else:
                self.end_date = self.start_date + timedelta(days=int(duration) - 1)
        else:
            if calendar_manager:
                hours_per_day = calendar_manager.hours_per_day
                days_span = int(duration / hours_per_day)
                if duration % hours_per_day != 0:
                    days_span += 1
                
                start_is_working = calendar_manager.is_working_day(self.start_date)
                days_to_add = days_span - (1 if start_is_working else 0)
                
                self.end_date = calendar_manager.add_working_days(
                    self.start_date, 
                    max(0, days_to_add)
                )
            else:
                days_span = int(duration / 8.0)
                if duration % 8.0 != 0:
                    days_span += 1
                self.end_date = self.start_date + timedelta(days=max(0, days_span - 1))
    
    def set_duration_and_update_start(self, duration: float, unit: DurationUnit,
                                     calendar_manager=None):
        """Set duration and update start date accordingly (keeping end date fixed)"""
        # MILESTONES IGNORE DURATION CHANGES
        if self.is_milestone:
            self.start_date = self.end_date
            return
        
        if unit == DurationUnit.DAYS:
            if calendar_manager:
                end_is_working = calendar_manager.is_working_day(self.end_date)
                # For backwards calculation, we want to find start such that [start, end] has duration
                # If end is working, it counts as 1. Need to subtract (duration-1).
                # If end is non-working, it counts as 0. Need to subtract duration.
                # BUT subtract_working_days(date, 0) returns date.
                days_to_sub = int(duration) - (1 if end_is_working else 0)
                self.start_date = calendar_manager.subtract_working_days(self.end_date, max(0, days_to_sub))
            else:
                self.start_date = self.end_date - timedelta(days=int(duration) - 1)
        else:
            if calendar_manager:
                hours_per_day = calendar_manager.hours_per_day
                days_span = int(duration / hours_per_day)
                if duration % hours_per_day != 0:
                    days_span += 1
                
                end_is_working = calendar_manager.is_working_day(self.end_date)
                days_to_sub = days_span - (1 if end_is_working else 0)
                
                self.start_date = calendar_manager.subtract_working_days(self.end_date, max(0, days_to_sub))
            else:
                days_span = int(duration / 8.0)
                if duration % 8.0 != 0:
                    days_span += 1
                self.start_date = self.end_date - timedelta(days=max(0, days_span - 1))
                
class Resource:
    """Resource data model"""
    
    def __init__(self, name: str, max_hours_per_day: float = 8.0,
                 exceptions: List[str] = None, billing_rate: float = 0.0):
        self.name = name
        self.max_hours_per_day = max_hours_per_day
        self.exceptions = exceptions or []
        self.billing_rate = billing_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary"""
        return {
            'name': self.name,
            'max_hours_per_day': self.max_hours_per_day,
            'exceptions': self.exceptions,
            'billing_rate': self.billing_rate
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Resource':
        """Create resource from dictionary"""
        return Resource(
            name=data['name'],
            max_hours_per_day=data.get('max_hours_per_day', 8.0),
            exceptions=data.get('exceptions', []),
            billing_rate=data.get('billing_rate', 0.0)
        )
