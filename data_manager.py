"""
Data Manager - Handles CRUD operations for tasks and resources
Enhanced with hierarchical tasks, dependency types, and status indicators
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from settings_manager import ProjectSettings, DurationUnit

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

class Task:
    """Task data model with hierarchy and dependency types"""
    
    _next_id = 1
    
    def __init__(self, name: str, start_date: datetime, end_date: datetime,
                 percent_complete: int = 0, predecessors: List[Tuple[int, str]] = None,
                 assigned_resources: List[str] = None, notes: str = "",
                 task_id: int = None, parent_id: int = None, is_summary: bool = False,
                 is_milestone: bool = False):
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
                self.predecessors = predecessors
            else:
                self.predecessors = [(pred_id, DependencyType.FS.name) for pred_id in predecessors]
        else:
            self.predecessors = predecessors or []
        
        self.assigned_resources = assigned_resources or []
        self.notes = notes
        
        # Store original dates
        self._original_start = start_date
        self._original_end = end_date
    
        # Hierarchy fields
        self.parent_id = parent_id
        self.is_summary = is_summary
        self._original_start = start_date  # Store original for summary tasks
        self._original_end = end_date
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'percent_complete': self.percent_complete,
            'predecessors': self.predecessors,
            'assigned_resources': self.assigned_resources,
            'notes': self.notes,
            'parent_id': self.parent_id,
            'is_summary': self.is_summary,
            'is_milestone': self.is_milestone
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary with backward compatibility"""
        # Handle old format predecessors
        predecessors = data.get('predecessors', [])
        if predecessors and len(predecessors) > 0:
            if isinstance(predecessors[0], (list, tuple)):
                predecessors = [tuple(p) if isinstance(p, list) else p for p in predecessors]
            else:
                predecessors = [(pred_id, DependencyType.FS.name) for pred_id in predecessors]
        
        return Task(
            name=data['name'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            percent_complete=data.get('percent_complete', 0),
            predecessors=predecessors,
            assigned_resources=data.get('assigned_resources', []),
            notes=data.get('notes', ''),
            task_id=data['id'],
            parent_id=data.get('parent_id'),
            is_summary=data.get('is_summary', False),
            is_milestone=data.get('is_milestone', False)
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
                self.end_date = calendar_manager.add_working_days(self.start_date, int(duration) - 1)
            else:
                self.end_date = self.start_date + timedelta(days=int(duration) - 1)
        else:
            if calendar_manager:
                hours_per_day = calendar_manager.hours_per_day
                days_needed = duration / hours_per_day
                self.end_date = calendar_manager.add_working_days(
                    self.start_date, 
                    int(days_needed) if duration % hours_per_day == 0 else int(days_needed) + 1
                )
            else:
                days_needed = duration / 8.0
                self.end_date = self.start_date + timedelta(days=int(days_needed))
    
    def set_duration_and_update_start(self, duration: float, unit: DurationUnit,
                                     calendar_manager=None):
        """Set duration and update start date accordingly (keeping end date fixed)"""
        # MILESTONES IGNORE DURATION CHANGES
        if self.is_milestone:
            self.start_date = self.end_date
            return
        
        if unit == DurationUnit.DAYS:
            if calendar_manager:
                # Calculate backwards
                temp_date = self.end_date
                for _ in range(int(duration) - 1):
                    temp_date -= timedelta(days=1)
                    while not calendar_manager.is_working_day(temp_date):
                        temp_date -= timedelta(days=1)
                self.start_date = temp_date
            else:
                self.start_date = self.end_date - timedelta(days=int(duration) - 1)
        else:
            if calendar_manager:
                hours_per_day = calendar_manager.hours_per_day
                days_needed = duration / hours_per_day
                
                temp_date = self.end_date
                for _ in range(int(days_needed)):
                    temp_date -= timedelta(days=1)
                    while not calendar_manager.is_working_day(temp_date):
                        temp_date -= timedelta(days=1)
                self.start_date = temp_date
            else:
                days_needed = duration / 8.0
                self.start_date = self.end_date - timedelta(days=int(days_needed))
                
class Resource:
    """Resource data model"""
    
    def __init__(self, name: str, max_hours_per_day: float = 8.0,
                 exceptions: List[str] = None):
        self.name = name
        self.max_hours_per_day = max_hours_per_day
        self.exceptions = exceptions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary"""
        return {
            'name': self.name,
            'max_hours_per_day': self.max_hours_per_day,
            'exceptions': self.exceptions
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Resource':
        """Create resource from dictionary"""
        return Resource(
            name=data['name'],
            max_hours_per_day=data.get('max_hours_per_day', 8.0),
            exceptions=data.get('exceptions', [])
        )


class DataManager:
    """Manages all project data with hierarchy and dependency support"""
    
    def __init__(self, calendar_manager=None):
        self.tasks: List[Task] = []
        self.resources: List[Resource] = []
        self.calendar_manager = calendar_manager
        self.project_name: str = "Untitled Project"
        self.settings = ProjectSettings()
    
    # Task CRUD Operations
    
    def add_task(self, task: Task, parent_id: int = None) -> bool:
        """Add a new task with validation"""
        task.parent_id = parent_id
        
        # Validate if parent exists
        if parent_id is not None:
            parent = self.get_task(parent_id)
            if not parent:
                return False
            # Mark parent as summary task
            parent.is_summary = True
        
        # Validate predecessors
        if not self._validate_predecessors(task):
            return False
        
        # Auto-calculate dates based on predecessors
        self._auto_calculate_dates_from_predecessors(task)
        
        self.tasks.append(task)
        
        # Update parent summary dates
        if parent_id is not None:
            self._update_summary_task_dates(parent_id)
        
        # Auto-adjust dependent tasks
        self._auto_adjust_dependent_tasks(task)
        
        return True
    
    def update_task(self, task_id: int, updated_task: Task) -> bool:
        """Update an existing task"""
        old_task = self.get_task(task_id)
        if not old_task:
            return False
        
        # Preserve hierarchy
        updated_task.parent_id = old_task.parent_id
        updated_task.is_summary = old_task.is_summary
        
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                if not self._validate_predecessors(updated_task, exclude_id=task_id):
                    return False
                
                # Auto-calculate dates from predecessors
                self._auto_calculate_dates_from_predecessors(updated_task)
                
                self.tasks[i] = updated_task
                
                # Update summary task if this has a parent
                if updated_task.parent_id is not None:
                    self._update_summary_task_dates(updated_task.parent_id)
                
                # Update children if this is a summary task
                if updated_task.is_summary:
                    self._update_summary_task_dates(task_id)
                
                # Update dependent tasks
                self._auto_adjust_dependent_tasks(updated_task)
                
                return True
        return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task and update dependencies"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Delete all child tasks first
        children = self.get_child_tasks(task_id)
        for child in children:
            self.delete_task(child.id)
        
        # Remove task
        self.tasks = [t for t in self.tasks if t.id != task_id]
        
        # Remove from all predecessor lists
        for t in self.tasks:
            t.predecessors = [p for p in t.predecessors if p[0] != task_id]
        
        # Update parent summary dates if exists
        if task.parent_id is not None:
            parent = self.get_task(task.parent_id)
            if parent:
                children_remaining = self.get_child_tasks(task.parent_id)
                if not children_remaining:
                    parent.is_summary = False
                else:
                    self._update_summary_task_dates(task.parent_id)
        
        return True
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return self.tasks.copy()
    
    def get_child_tasks(self, parent_id: int) -> List[Task]:
        """Get all direct children of a task"""
        return [t for t in self.tasks if t.parent_id == parent_id]
    
    def get_all_descendants(self, task_id: int) -> List[Task]:
        """Get all descendants (children, grandchildren, etc.) of a task"""
        descendants = []
        children = self.get_child_tasks(task_id)
        
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendants(child.id))
        
        return descendants
    
    def get_top_level_tasks(self) -> List[Task]:
        """Get all tasks without parents"""
        return [t for t in self.tasks if t.parent_id is None]
    
    def move_task(self, task_id: int, new_parent_id: int = None) -> bool:
        """Move a task to a new parent"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Prevent circular references
        if new_parent_id is not None:
            descendants = self.get_all_descendants(task_id)
            if any(d.id == new_parent_id for d in descendants):
                return False
        
        old_parent_id = task.parent_id
        
        # Update task parent
        task.parent_id = new_parent_id
        
        # Update old parent
        if old_parent_id is not None:
            old_parent = self.get_task(old_parent_id)
            if old_parent:
                remaining_children = self.get_child_tasks(old_parent_id)
                if not remaining_children:
                    old_parent.is_summary = False
                else:
                    self._update_summary_task_dates(old_parent_id)
        
        # Update new parent
        if new_parent_id is not None:
            new_parent = self.get_task(new_parent_id)
            if new_parent:
                new_parent.is_summary = True
                self._update_summary_task_dates(new_parent_id)
        
        return True
    
    # Resource CRUD Operations (unchanged)
    
    def add_resource(self, resource: Resource) -> bool:
        """Add a new resource"""
        if any(r.name == resource.name for r in self.resources):
            return False
        self.resources.append(resource)
        return True
    
    def update_resource(self, old_name: str, updated_resource: Resource) -> bool:
        """Update an existing resource"""
        for i, resource in enumerate(self.resources):
            if resource.name == old_name:
                if old_name != updated_resource.name:
                    for task in self.tasks:
                        if old_name in task.assigned_resources:
                            idx = task.assigned_resources.index(old_name)
                            task.assigned_resources[idx] = updated_resource.name
                self.resources[i] = updated_resource
                return True
        return False
    
    def delete_resource(self, name: str) -> bool:
        """Delete a resource"""
        self.resources = [r for r in self.resources if r.name != name]
        for task in self.tasks:
            if name in task.assigned_resources:
                task.assigned_resources.remove(name)
        return True
    
    def get_resource(self, name: str) -> Optional[Resource]:
        """Get resource by name"""
        for resource in self.resources:
            if resource.name == name:
                return resource
        return None
    
    def get_all_resources(self) -> List[Resource]:
        """Get all resources"""
        return self.resources.copy()
    
    # Validation and Business Logic
    
    def _validate_predecessors(self, task: Task, exclude_id: int = None) -> bool:
        """Validate that task doesn't create circular dependencies"""
        for pred_id, dep_type in task.predecessors:
            if pred_id == exclude_id or pred_id == task.id:
                continue
            
            predecessor = self.get_task(pred_id)
            if not predecessor:
                continue
            
            # Check for circular dependencies
            if self._creates_circular_dependency(task.id, pred_id):
                return False
        
        return True
    
    def _creates_circular_dependency(self, task_id: int, pred_id: int) -> bool:
        """Check if adding predecessor would create a circular dependency"""
        visited = set()
        
        def has_path(from_id: int, to_id: int) -> bool:
            if from_id == to_id:
                return True
            if from_id in visited:
                return False
            visited.add(from_id)
            
            task = self.get_task(from_id)
            if not task:
                return False
            
            for pred_id, _ in task.predecessors:
                if has_path(pred_id, to_id):
                    return True
            return False
        
        return has_path(pred_id, task_id)
    
    def _auto_calculate_dates_from_predecessors(self, task: Task):
        """Auto-calculate task dates based on predecessors and dependency types"""
        if not task.predecessors:
            return
        
        # Find the most constraining predecessor
        latest_start = None
        latest_end = None
        
        for pred_id, dep_type_str in task.predecessors:
            predecessor = self.get_task(pred_id)
            if not predecessor:
                continue
            
            dep_type = DependencyType[dep_type_str]
            
            if dep_type == DependencyType.FS:
                # Finish-to-Start: task starts after predecessor ends
                constraint_start = predecessor.end_date + timedelta(days=1)
                if self.calendar_manager:
                    # Move to next working day
                    while not self.calendar_manager.is_working_day(constraint_start):
                        constraint_start += timedelta(days=1)
                
                if latest_start is None or constraint_start > latest_start:
                    latest_start = constraint_start
            
            elif dep_type == DependencyType.SS:
                # Start-to-Start: task starts when predecessor starts
                constraint_start = predecessor.start_date
                if latest_start is None or constraint_start > latest_start:
                    latest_start = constraint_start
            
            elif dep_type == DependencyType.FF:
                # Finish-to-Finish: task ends when predecessor ends
                constraint_end = predecessor.end_date
                if latest_end is None or constraint_end > latest_end:
                    latest_end = constraint_end
            
            elif dep_type == DependencyType.SF:
                # Start-to-Finish: task ends when predecessor starts
                constraint_end = predecessor.start_date
                if latest_end is None or constraint_end > latest_end:
                    latest_end = constraint_end
        
        # Apply constraints to task
        duration = task.duration
        
        if latest_start is not None:
            task.start_date = latest_start
            if latest_end is None:
                task.end_date = latest_start + timedelta(days=duration - 1)
        
        if latest_end is not None:
            task.end_date = latest_end
            if latest_start is None:
                task.start_date = latest_end - timedelta(days=duration - 1)
    
    def _auto_adjust_dependent_tasks(self, updated_task: Task):
        """Auto-shift dependent tasks when a task changes"""
        # Find all tasks that have this task as a predecessor
        dependent_tasks = [
            t for t in self.tasks 
            if any(pred_id == updated_task.id for pred_id, _ in t.predecessors)
        ]
        
        for dep_task in dependent_tasks:
            # Recalculate dates based on predecessors
            self._auto_calculate_dates_from_predecessors(dep_task)
            
            # Update parent summary if exists
            if dep_task.parent_id is not None:
                self._update_summary_task_dates(dep_task.parent_id)
            
            # Recursively adjust tasks dependent on this one
            self._auto_adjust_dependent_tasks(dep_task)
    
    def _update_summary_task_dates(self, summary_task_id: int):
        """Update summary task dates based on child tasks"""
        summary_task = self.get_task(summary_task_id)
        if not summary_task or not summary_task.is_summary:
            return
        
        children = self.get_child_tasks(summary_task_id)
        if not children:
            return
        # *** EXCLUDE MILESTONES FROM DURATION CALCULATION ***
        non_milestone_children = [c for c in children if not c.is_milestone]
        
        # Find earliest start and latest end among children
        earliest_start = min(child.start_date for child in children)
        latest_end = max(child.end_date for child in children)
        
        # Calculate average completion
        if non_milestone_children:
            total_duration = sum(child.duration for child in non_milestone_children)
            if total_duration > 0:
                weighted_completion = sum(
                    child.duration * child.percent_complete 
                    for child in non_milestone_children
                )
                summary_task.percent_complete = int(weighted_completion / total_duration)
        else:
            # If only milestones, calculate based on completed milestones
            if children:
                completed = sum(1 for c in children if c.percent_complete == 100)
                summary_task.percent_complete = int((completed / len(children)) * 100)
        
        # Update summary task dates
        summary_task.start_date = earliest_start
        summary_task.end_date = latest_end
        
        # Recursively update parent if exists
        if summary_task.parent_id is not None:
            self._update_summary_task_dates(summary_task.parent_id)
    
    # Project Analytics
    
    def get_project_start_date(self) -> Optional[datetime]:
        """Get earliest task start date (top-level only)"""
        top_level = self.get_top_level_tasks()
        if not top_level:
            return None
        return min(task.start_date for task in top_level)
    
    def get_project_end_date(self) -> Optional[datetime]:
        """Get latest task end date (top-level only)"""
        top_level = self.get_top_level_tasks()
        if not top_level:
            return None
        return max(task.end_date for task in top_level)
    
    def get_overall_completion(self) -> float:
        """Calculate overall project completion percentage"""
        if not self.tasks:
            return 0.0
        
        total_duration = sum(task.duration for task in self.tasks)
        if total_duration == 0:
            return 0.0
        
        weighted_completion = sum(
            task.duration * task.percent_complete 
            for task in self.tasks
        )
        
        return weighted_completion / total_duration
    
    def get_resource_allocation(self) -> Dict[str, Dict[str, float]]:
        """Calculate total effort and hours per resource"""
        allocation = {}
        
        for resource in self.resources:
            allocation[resource.name] = {
                'total_hours': 0.0,
                'max_hours_per_day': resource.max_hours_per_day,
                'tasks_assigned': 0
            }
        
        for task in self.tasks:
            # Skip summary tasks
            if task.is_summary:
                continue
            
            task_hours = task.duration * 8
            if self.calendar_manager:
                task_hours = self.calendar_manager.calculate_working_hours(
                    task.start_date, task.end_date
                )
            
            num_resources = len(task.assigned_resources) or 1
            hours_per_resource = task_hours / num_resources
            
            for resource_name in task.assigned_resources:
                if resource_name in allocation:
                    allocation[resource_name]['total_hours'] += hours_per_resource
                    allocation[resource_name]['tasks_assigned'] += 1
        
        return allocation
    
    def check_resource_overallocation(self) -> Dict[str, List[str]]:
        """Check for resource over-allocation warnings"""
        warnings = {}
        resource_daily_hours = {}
        
        for task in self.tasks:
            # Skip summary tasks
            if task.is_summary:
                continue
            
            current_date = task.start_date
            while current_date <= task.end_date:
                if self.calendar_manager and not self.calendar_manager.is_working_day(current_date):
                    current_date += timedelta(days=1)
                    continue
                
                date_key = current_date.strftime('%Y-%m-%d')
                
                for resource_name in task.assigned_resources:
                    key = f"{resource_name}_{date_key}"
                    hours_per_day = 8.0
                    if self.calendar_manager:
                        hours_per_day = self.calendar_manager.hours_per_day
                    
                    if key not in resource_daily_hours:
                        resource_daily_hours[key] = 0
                    
                    resource_daily_hours[key] += hours_per_day / len(task.assigned_resources)
                
                current_date += timedelta(days=1)
        
        # Check against max hours
        for key, hours in resource_daily_hours.items():
            resource_name, date = key.split('_', 1)
            resource = self.get_resource(resource_name)
            
            if resource and hours > resource.max_hours_per_day:
                if resource_name not in warnings:
                    warnings[resource_name] = []
                warnings[resource_name].append(
                    f"Over-allocated on {date}: {hours:.1f}h / {resource.max_hours_per_day}h"
                )
        
        return warnings
    
    # Data Persistence
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all data to dictionary"""
        return {
            'project_name': self.project_name,
            'tasks': [task.to_dict() for task in self.tasks],
            'resources': [resource.to_dict() for resource in self.resources],
            'next_task_id': Task._next_id,
            'version': '2.0'  # Version tracking for compatibility
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Import all data from dictionary with backward compatibility"""
        version = data.get('version', '1.0')
        
        Task._next_id = data.get('next_task_id', 1)
        self.project_name = data.get('project_name', 'Untitled Project')
        
        self.tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
        self.resources = [Resource.from_dict(r) for r in data.get('resources', [])]
    
    def clear_all(self):
        """Clear all data"""
        self.tasks.clear()
        self.resources.clear()
        self.project_name = "Untitled Project"
        Task._next_id = 1
    
    def bulk_indent_tasks(self, task_ids: List[int]) -> bool:
        """Indent multiple tasks at once"""
        # Sort tasks by their current position
        tasks = [self.get_task(tid) for tid in task_ids if self.get_task(tid)]
        if not tasks:
            return False
        
        # Sort by ID to maintain order
        tasks.sort(key=lambda t: t.id)
        
        success_count = 0
        for task in tasks:
            # Find previous sibling
            siblings = [t for t in self.get_all_tasks() 
                       if t.parent_id == task.parent_id and t.id != task.id and t.id < task.id]
            
            if siblings:
                # Sort and get the last one before this task
                siblings.sort(key=lambda t: t.id)
                previous_task = siblings[-1]
                
                # Try to move under previous task
                if self.move_task(task.id, previous_task.id):
                    success_count += 1
        
        return success_count > 0
    
    def bulk_outdent_tasks(self, task_ids: List[int]) -> bool:
        """Outdent multiple tasks at once"""
        tasks = [self.get_task(tid) for tid in task_ids if self.get_task(tid)]
        if not tasks:
            return False
        
        success_count = 0
        for task in tasks:
            if task.parent_id is not None:
                parent = self.get_task(task.parent_id)
                if parent:
                    new_parent_id = parent.parent_id
                    if self.move_task(task.id, new_parent_id):
                        success_count += 1
        
        return success_count > 0
    
    def convert_all_tasks_to_unit(self, new_unit: DurationUnit):
        """
        Convert all task durations when unit changes.
        This recalculates end dates based on current start dates and durations.
        """
        for task in self.tasks:
            if not task.is_summary:
                # Get current duration in the new unit
                current_duration = task.get_duration(new_unit, self.calendar_manager)
                # This ensures consistency - no actual change needed as calculation adapts
                pass
            else:
                # Summary tasks auto-update from children
                self._update_summary_task_dates(task.id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all data to dictionary"""
        return {
            'project_name': self.project_name,
            'tasks': [task.to_dict() for task in self.tasks],
            'resources': [resource.to_dict() for resource in self.resources],
            'next_task_id': Task._next_id,
            'settings': self.settings.to_dict(),  # ADD THIS
            'version': '2.1'  # Increment version
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Import all data from dictionary with backward compatibility"""
        version = data.get('version', '1.0')
        
        Task._next_id = data.get('next_task_id', 1)
        self.project_name = data.get('project_name', 'Untitled Project')
        
        # Load tasks
        self.tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
        
        # *** BACKWARD COMPATIBILITY: Add is_milestone to old tasks ***
        for task in self.tasks:
            if not hasattr(task, 'is_milestone'):
                task.is_milestone = False
        
        # Load resources
        self.resources = [Resource.from_dict(r) for r in data.get('resources', [])]
        
        # Load settings (with backward compatibility)
        if 'settings' in data:
            self.settings.from_dict(data['settings'])
        else:
            self.settings = ProjectSettings()
    
    def insert_task_at_position(self, task: Task, insert_after_id: int = None) -> bool:
        """
        Insert a task at a specific position and renumber subsequent tasks
        
        Args:
            task: The task to insert (its ID will be set automatically)
            insert_after_id: Insert after this task ID. If None, append at end.
        
        Returns:
            True if successful
        """
        if insert_after_id is None:
            # Just add at the end
            return self.add_task(task)
        
        # Find the task to insert after
        reference_task = self.get_task(insert_after_id)
        if not reference_task:
            return False
        
        # The new task should get ID = insert_after_id + 1
        new_task_id = insert_after_id + 1
        
        # Renumber all tasks with ID >= new_task_id (shift them up by 1)
        self._renumber_tasks_from(new_task_id, shift=1)
        
        # Set the new task's ID
        task.id = new_task_id
        
        # Set parent to match the reference task
        task.parent_id = reference_task.parent_id
        
        # Validate predecessors
        if not self._validate_predecessors(task):
            # Rollback renumbering
            self._renumber_tasks_from(new_task_id + 1, shift=-1)
            return False
        
        # Auto-calculate dates from predecessors
        self._auto_calculate_dates_from_predecessors(task)
        
        # Add the task
        self.tasks.append(task)
        
        # Update summary tasks if needed
        if task.parent_id is not None:
            self._update_summary_task_dates(task.parent_id)
        
        # Update next ID counter
        Task._next_id = max(Task._next_id, max(t.id for t in self.tasks) + 1)
        
        return True
    
    def insert_task_before(self, task: Task, insert_before_id: int) -> bool:
        """
        Insert a task before a specific task ID
        
        Args:
            task: The task to insert
            insert_before_id: Insert before this task ID
        
        Returns:
            True if successful
        """
        reference_task = self.get_task(insert_before_id)
        if not reference_task:
            return False
        
        # The new task gets the ID of the reference task
        new_task_id = insert_before_id
        
        # Renumber all tasks with ID >= new_task_id (shift them up by 1)
        self._renumber_tasks_from(new_task_id, shift=1)
        
        # Set the new task's ID
        task.id = new_task_id
        
        # Set parent to match the reference task
        task.parent_id = reference_task.parent_id
        
        # Validate predecessors
        if not self._validate_predecessors(task):
            # Rollback renumbering
            self._renumber_tasks_from(new_task_id + 1, shift=-1)
            return False
        
        # Auto-calculate dates from predecessors
        self._auto_calculate_dates_from_predecessors(task)
        
        # Add the task
        self.tasks.append(task)
        
        # Update summary tasks if needed
        if task.parent_id is not None:
            self._update_summary_task_dates(task.parent_id)
        
        # Update next ID counter
        Task._next_id = max(Task._next_id, max(t.id for t in self.tasks) + 1)
        
        return True
    
    def _renumber_tasks_from(self, start_id: int, shift: int):
        """
        Renumber tasks starting from start_id by shifting their IDs
        Also updates all predecessor references and parent_id references
        
        Args:
            start_id: Start renumbering from this ID
            shift: Amount to shift (positive or negative)
        """
        # Create a mapping of old ID to new ID
        id_mapping = {}
        
        # First pass: renumber tasks and build mapping
        for task in self.tasks:
            if task.id >= start_id:
                old_id = task.id
                new_id = task.id + shift
                task.id = new_id
                id_mapping[old_id] = new_id
        
        # Second pass: update all predecessor references
        for task in self.tasks:
            updated_predecessors = []
            for pred_id, dep_type in task.predecessors:
                # If this predecessor was renumbered, use the new ID
                if pred_id in id_mapping:
                    updated_predecessors.append((id_mapping[pred_id], dep_type))
                else:
                    updated_predecessors.append((pred_id, dep_type))
            task.predecessors = updated_predecessors
        
        # Third pass: update parent_id references
        for task in self.tasks:
            if task.parent_id in id_mapping:
                task.parent_id = id_mapping[task.parent_id]
    
    def get_next_available_id(self) -> int:
        """Get the next available task ID"""
        if not self.tasks:
            return 1
        return max(t.id for t in self.tasks) + 1