"""
Baseline Models - For capturing project snapshots
"""

from datetime import datetime
from typing import Dict, Any, Optional
from settings_manager.settings_manager import DateFormat

class TaskSnapshot:
    """Snapshot of a task's state at a specific point in time"""
    
    def __init__(self, task_id: int, task_name: str, start_date: datetime, 
                 end_date: datetime, duration: float, percent_complete: int, wbs: str = ""):
        self.task_id = task_id
        self.task_name = task_name
        self.start_date = start_date
        self.end_date = end_date
        self.duration = duration
        self.percent_complete = percent_complete
        self.wbs = wbs
    
    def to_dict(self, date_format: DateFormat = None) -> Dict[str, Any]:
        """Convert snapshot to dictionary"""
        date_format_str = self._get_format_string(date_format) if date_format else '%Y-%m-%dT%H:%M:%S'
        
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'start_date': self.start_date.strftime(date_format_str),
            'end_date': self.end_date.strftime(date_format_str),
            'duration': self.duration,
            'percent_complete': self.percent_complete,
            'wbs': self.wbs
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any], date_format: DateFormat = None) -> 'TaskSnapshot':
        """Create snapshot from dictionary"""
        date_format_str = TaskSnapshot._get_format_string_static(date_format) if date_format else '%Y-%m-%dT%H:%M:%S'
        
        return TaskSnapshot(
            task_id=data['task_id'],
            task_name=data['task_name'],
            start_date=datetime.strptime(data['start_date'], date_format_str),
            end_date=datetime.strptime(data['end_date'], date_format_str),
            duration=float(data['duration']),
            percent_complete=int(data['percent_complete']),
            wbs=data.get('wbs', '')
        )
    
    def _get_format_string(self, date_format: DateFormat) -> str:
        """Get date format string"""
        if date_format == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y %H:%M:%S'
        elif date_format == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y %H:%M:%S'
        else:
            return '%Y-%m-%dT%H:%M:%S'
    
    @staticmethod
    def _get_format_string_static(date_format: DateFormat) -> str:
        """Get date format string (static version)"""
        if date_format == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y %H:%M:%S'
        elif date_format == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y %H:%M:%S'
        else:
            return '%Y-%m-%dT%H:%M:%S'


class Baseline:
    """Project baseline capturing task states at a specific point in time"""
    
    def __init__(self, name: str, created_date: datetime = None):
        self.name = name
        self.created_date = created_date or datetime.now()
        self.task_snapshots: Dict[int, TaskSnapshot] = {}  # task_id -> TaskSnapshot
    
    def add_task_snapshot(self, snapshot: TaskSnapshot):
        """Add a task snapshot to this baseline"""
        self.task_snapshots[snapshot.task_id] = snapshot
    
    def get_task_snapshot(self, task_id: int) -> Optional[TaskSnapshot]:
        """Get snapshot for a specific task"""
        return self.task_snapshots.get(task_id)
    
    def get_all_snapshots(self) -> Dict[int, TaskSnapshot]:
        """Get all task snapshots"""
        return self.task_snapshots
    
    def to_dict(self, date_format: DateFormat = None) -> Dict[str, Any]:
        """Convert baseline to dictionary"""
        date_format_str = self._get_format_string(date_format) if date_format else '%Y-%m-%dT%H:%M:%S'
        
        return {
            'name': self.name,
            'created_date': self.created_date.strftime(date_format_str),
            'task_snapshots': {
                str(task_id): snapshot.to_dict(date_format) 
                for task_id, snapshot in self.task_snapshots.items()
            }
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any], date_format: DateFormat = None) -> 'Baseline':
        """Create baseline from dictionary"""
        date_format_str = Baseline._get_format_string_static(date_format) if date_format else '%Y-%m-%dT%H:%M:%S'
        
        baseline = Baseline(
            name=data['name'],
            created_date=datetime.strptime(data['created_date'], date_format_str)
        )
        
        # Load task snapshots
        for task_id_str, snapshot_data in data.get('task_snapshots', {}).items():
            snapshot = TaskSnapshot.from_dict(snapshot_data, date_format)
            baseline.task_snapshots[int(task_id_str)] = snapshot
        
        return baseline
    
    def _get_format_string(self, date_format: DateFormat) -> str:
        """Get date format string"""
        if date_format == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y %H:%M:%S'
        elif date_format == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y %H:%M:%S'
        else:
            return '%Y-%m-%dT%H:%M:%S'
    
    @staticmethod
    def _get_format_string_static(date_format: DateFormat) -> str:
        """Get date format string (static version)"""
        if date_format == DateFormat.DD_MM_YYYY:
            return '%d-%m-%Y %H:%M:%S'
        elif date_format == DateFormat.DD_MMM_YYYY:
            return '%d-%b-%Y %H:%M:%S'
        else:
            return '%Y-%m-%dT%H:%M:%S'
