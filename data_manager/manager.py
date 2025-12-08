from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from settings_manager.settings_manager import ProjectSettings, DurationUnit
from data_manager.models import Task, Resource, DependencyType, TaskStatus, ScheduleType
from data_manager.baseline import Baseline, TaskSnapshot

class DataManager:
    """Manages all project data with hierarchy and dependency support"""
    
    def __init__(self, calendar_manager=None):
        self.tasks: List[Task] = []
        self.resources: List[Resource] = [] # Initialize as empty, load_from_dict will handle default if needed
        self.calendar_manager = calendar_manager
        self.project_name: str = "Untitled Project"
        self.settings = ProjectSettings()
        self.baselines: List[Baseline] = []  # Maximum 3 baselines
    
    # Task CRUD Operations
    
    def _generate_wbs(self):
        """Generate WBS for all tasks based on their hierarchy."""
        # Sort tasks by parent_id and then by id to ensure consistent WBS generation
        sorted_tasks = sorted(self.tasks, key=lambda t: (t.parent_id if t.parent_id is not None else -1, t.id))
        
        # Build a dictionary for quick lookup of children
        children_map = {}
        for task in sorted_tasks:
            if task.parent_id not in children_map:
                children_map[task.parent_id] = []
            children_map[task.parent_id].append(task)

        def _assign_wbs_recursive(task_list: List[Task], prefix: str = ""):
            for i, task in enumerate(task_list):
                wbs_number = f"{prefix}{i + 1}"
                task.wbs = wbs_number
                if task.id in children_map:
                    _assign_wbs_recursive(children_map[task.id], f"{wbs_number}.")
        
        # Start WBS generation from top-level tasks (parent_id is None)
        top_level_tasks = [t for t in sorted_tasks if t.parent_id is None]
        _assign_wbs_recursive(top_level_tasks)

    def add_task(self, task: Task, parent_id: int = None) -> bool:
        """Add a new task with validation"""
        task.parent_id = parent_id
        
        # Validate if parent exists
        if parent_id is not None:
            parent = self.get_task(parent_id)
            if not parent:
                return False
            # Mark parent as summary task and make it bold
            if not parent.is_summary:  # Only update if not already a summary
                parent.is_summary = True
                parent.font_bold = True  # Auto-apply bold formatting
        
        # Validate predecessors
        if not self._validate_predecessors(task):
            return False
        
        # Auto-calculate dates based on predecessors
        self._auto_calculate_dates_from_predecessors(task)
        
        self.tasks.append(task)
        self._generate_wbs()
        
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
                # Validation: Summary tasks must always be Auto Scheduled
                if updated_task.is_summary and updated_task.schedule_type == ScheduleType.MANUALLY_SCHEDULED:
                    # Revert to Auto Scheduled if an attempt is made to set a summary task to Manual
                    updated_task.schedule_type = ScheduleType.AUTO_SCHEDULED
                    # Optionally, log a warning or return False to indicate validation failure
                    # For now, we'll just force it to Auto Scheduled

                if not self._validate_predecessors(updated_task, exclude_id=task_id):
                    return False
                
                # If schedule type changed from Manual to Auto, recalculate dates
                if old_task.schedule_type == ScheduleType.MANUALLY_SCHEDULED and \
                   updated_task.schedule_type == ScheduleType.AUTO_SCHEDULED:
                    self._auto_calculate_dates_from_predecessors(updated_task)
                # If an auto-scheduled task's duration is manually changed, switch to manually scheduled

                # If it's still Auto Scheduled, or changed from Auto to Manual,
                # _auto_calculate_dates_from_predecessors will be called by _auto_adjust_dependent_tasks
                # if needed, or skipped if it's Manual.
                
                self.tasks[i] = updated_task

                self._generate_wbs()
                
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
        self._generate_wbs()
        
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
                    parent.font_bold = False  # Remove bold formatting
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
        """Get all direct children of a task, sorted by ID"""
        return sorted([t for t in self.tasks if t.parent_id == parent_id], key=lambda t: t.id)
    
    def get_all_descendants(self, task_id: int) -> List[Task]:
        """Get all descendants (children, grandchildren, etc.) of a task"""
        descendants = []
        children = self.get_child_tasks(task_id)
        
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendants(child.id))
        
        return descendants
    
    def get_top_level_tasks(self) -> List[Task]:
        """Get all tasks without parents, sorted by ID"""
        return sorted([t for t in self.tasks if t.parent_id is None], key=lambda t: t.id)
    
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
        self._generate_wbs()
        
        # Update old parent
        if old_parent_id is not None:
            old_parent = self.get_task(old_parent_id)
            if old_parent:
                remaining_children = self.get_child_tasks(old_parent_id)
                if not remaining_children:
                    old_parent.is_summary = False
                    old_parent.font_bold = False  # Remove bold formatting
                else:
                    self._update_summary_task_dates(old_parent_id)
        
        # Update new parent
        if new_parent_id is not None:
            new_parent = self.get_task(new_parent_id)
            if new_parent:
                if not new_parent.is_summary:  # Only update if not already a summary
                    new_parent.is_summary = True
                    new_parent.font_bold = True  # Auto-apply bold formatting
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
                        task.assigned_resources = [
                            (updated_resource.name, alloc) if name == old_name else (name, alloc) 
                            for name, alloc in task.assigned_resources
                        ]
                self.resources[i] = updated_resource
                return True
        return False
    
    def delete_resource(self, name: str) -> bool:
        """Delete a resource"""
        self.resources = [r for r in self.resources if r.name != name]
        for task in self.tasks:
            task.assigned_resources = [(r_name, alloc) for r_name, alloc in task.assigned_resources if r_name != name]
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
    
    def get_successors(self, task_id: int) -> List[Task]:
        """Get all tasks that have the given task_id as a predecessor"""
        successors = []
        for task in self.tasks:
            if any(pred_id == task_id for pred_id, _, _ in task.predecessors):
                successors.append(task)
        return successors

    # Validation and Business Logic
    
    def _validate_predecessors(self, task: Task, exclude_id: int = None) -> bool:
        for pred_id, dep_type, lag_days in task.predecessors:
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
            
            for pred_id, _, _ in task.predecessors:
                if has_path(pred_id, to_id):
                    return True
            return False
        
        return has_path(pred_id, task_id)
    
    def _auto_calculate_dates_from_predecessors(self, task: Task):
        """Auto-calculate task dates based on predecessors and dependency types"""
        if task.schedule_type == ScheduleType.MANUALLY_SCHEDULED:
            return
        if not task.predecessors:
            # If no predecessors, reset to original start date if available
            if hasattr(task, '_original_start') and task._original_start:
                task.start_date = task._original_start
                duration = task.get_duration(self.settings.duration_unit, self.calendar_manager)
                task.set_duration_and_update_end(duration, self.settings.duration_unit, self.calendar_manager)
            return
        
        # Find the most constraining predecessor
        latest_start = None
        latest_end = None
        
        for pred_id, dep_type_str, lag_days in task.predecessors:
            predecessor = self.get_task(pred_id)
            if not predecessor:
                continue
            
            dep_type = DependencyType[dep_type_str]
            lag = timedelta(days=lag_days)

            if dep_type == DependencyType.FS:
                # Finish-to-Start: task starts after predecessor ends
                if self.calendar_manager:
                    # Milestones start immediately after predecessor ends (plus lag)
                    if task.is_milestone:
                        if lag_days >= 0:
                            constraint_start = self.calendar_manager.add_working_days(predecessor.end_date, lag_days)
                        else:
                            constraint_start = self.calendar_manager.subtract_working_days(predecessor.end_date, abs(lag_days))
                    # For regular tasks
                    else:
                        start_from = predecessor.end_date
                        days_to_add = lag_days

                        # If predecessor is not a milestone, or if it ends late, we move to the next day
                        # A bit of a simplification: assume "late" is after 4 PM (16:00)
                        if not predecessor.is_milestone or start_from.hour >= 16:
                            days_to_add += 1
                        
                        constraint_start = self.calendar_manager.add_working_days(start_from, days_to_add)
                        
                        # If we moved to a new day, snap to 8 AM
                        if days_to_add > lag_days:
                           constraint_start = constraint_start.replace(hour=8, minute=0, second=0, microsecond=0)

                else:
                    constraint_start = predecessor.end_date + timedelta(days=1) + lag

                if latest_start is None or constraint_start > latest_start:
                    latest_start = constraint_start
            
            elif dep_type == DependencyType.SS:
                # Start-to-Start: task starts when predecessor starts
                constraint_start = predecessor.start_date + lag
                if latest_start is None or constraint_start > latest_start:
                    latest_start = constraint_start
            
            elif dep_type == DependencyType.FF:
                # Finish-to-Finish: task ends when predecessor ends
                constraint_end = predecessor.end_date + lag
                if latest_end is None or constraint_end > latest_end:
                    latest_end = constraint_end
            
            elif dep_type == DependencyType.SF:
                # Start-to-Finish: task ends when predecessor starts
                constraint_end = predecessor.start_date + lag
                if latest_end is None or constraint_end > latest_end:
                    latest_end = constraint_end
        
        # Apply constraints to task
        # Store original duration before modifying start/end dates
        original_duration_days = task.calculate_duration_days(self.calendar_manager)

        if latest_start is not None:
            task.start_date = latest_start
            if latest_end is None: # Only update end_date if not constrained by FF/SF
                if task.is_milestone:
                    task.end_date = task.start_date
                elif self.calendar_manager:
                    # To calculate the end date, we find the target end day and then set the time.
                    days_to_add = original_duration_days - 1
                    if days_to_add < 0: days_to_add = 0
                    
                    end_day = self.calendar_manager.add_working_days(task.start_date, days_to_add)

                    # The end time should correspond to the end of the work day.
                    end_time_on_day = task.start_date + timedelta(hours=self.calendar_manager.hours_per_day)

                    task.end_date = end_day.replace(
                        hour=end_time_on_day.hour, 
                        minute=end_time_on_day.minute, 
                        second=end_time_on_day.second,
                        microsecond=end_time_on_day.microsecond
                    )
                else:
                    task.end_date = task.start_date + timedelta(days=original_duration_days - 1)

        if latest_end is not None:
            task.end_date = latest_end
            if latest_start is None: # Only update start_date if not constrained by FS/SS
                if self.calendar_manager:
                    # Calculate backwards from end_date to find start_date
                    temp_start = task.end_date
                    for _ in range(original_duration_days - 1):
                        temp_start -= timedelta(days=1)
                        while not self.calendar_manager.is_working_day(temp_start):
                            temp_start -= timedelta(days=1)
                    task.start_date = temp_start
                else:
                    task.start_date = task.end_date - timedelta(days=original_duration_days - 1)
    
    def _auto_adjust_dependent_tasks(self, initial_task: Task):
        """Auto-shift dependent tasks when a task changes, using an iterative approach"""
        queue = [initial_task.id] # Store task IDs in the queue
        # Use a set to keep track of tasks that have been added to the queue
        # to avoid redundant processing within a single propagation cycle
        queued_ids = {initial_task.id}
        
        # Use a separate set to track tasks whose dates have been finalized in this cycle
        # This prevents infinite loops in circular dependencies, but allows re-evaluation if needed
        finalized_ids = set()

        while queue:
            task_id = queue.pop(0)
            task = self.get_task(task_id)
            if not task or task_id in finalized_ids:
                continue

            # Only auto-adjust AUTO_SCHEDULED tasks
            if task.schedule_type == ScheduleType.MANUALLY_SCHEDULED:
                finalized_ids.add(task_id) # Mark as finalized to prevent re-processing
                continue

            original_start = task.start_date
            original_end = task.end_date

            # Recalculate dates based on predecessors
            self._auto_calculate_dates_from_predecessors(task)

            # If dates changed, or if it's the initial task, mark as finalized and add successors to queue
            if original_start != task.start_date or original_end != task.end_date or task_id == initial_task.id:
                finalized_ids.add(task_id)

                # Update parent summary if exists
                if task.parent_id is not None:
                    self._update_summary_task_dates(task.parent_id)
                
                # Add all direct successors to the queue for re-evaluation
                for successor in self.get_successors(task.id):
                    # Only add AUTO_SCHEDULED successors to the queue
                    if successor.schedule_type == ScheduleType.AUTO_SCHEDULED and successor.id not in queued_ids:
                        queue.append(successor.id)
                        queued_ids.add(successor.id)

        # After all dependencies are resolved, update all summary tasks from bottom-up
        # This ensures summary tasks reflect the latest dates of their children
        for task in sorted(self.tasks, key=lambda t: t.get_level(self.tasks), reverse=True):
            if task.is_summary:
                self._update_summary_task_dates(task.id)

    
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
                'tasks_assigned': 0,
                'billing_rate': resource.billing_rate
            }
        
        for task in self.tasks:
            # Skip summary tasks and milestones
            if task.is_summary or task.is_milestone:
                continue
            
            for resource_name, allocation_percent in task.assigned_resources:
                if resource_name in allocation:
                    resource_obj = self.get_resource(resource_name)
                    if resource_obj and self.calendar_manager:
                        # Calculate task hours considering resource-specific exceptions
                        individual_task_hours = self.calendar_manager.calculate_working_hours(
                            task.start_date, task.end_date, resource_exceptions=resource_obj.exceptions
                        )
                    else:
                        # Fallback if no calendar manager or resource not found
                        individual_task_hours = task.duration * 8

                    effort_hours = individual_task_hours * (allocation_percent / 100.0)
                    allocation[resource_name]['total_hours'] += effort_hours
                    allocation[resource_name]['tasks_assigned'] += 1
        
        # Calculate total amount after all hours are accumulated
        for resource_name, data in allocation.items():
            data['total_amount'] = data['total_hours'] * data['billing_rate']

        return allocation
    
    def check_resource_overallocation(self) -> Dict[str, List[str]]:
        """Check for resource over-allocation warnings"""
        warnings = {}
        resource_daily_hours = {}
        
        for task in self.tasks:
            # Skip summary tasks and milestones
            if task.is_summary or task.is_milestone:
                continue
            
            current_date = task.start_date
            while current_date <= task.end_date:
                date_key = current_date.strftime('%Y-%m-%d') # Define date_key here

                if self.calendar_manager and not self.calendar_manager.is_working_day(current_date):
                    current_date += timedelta(days=1)
                    continue
                
                for resource_name, allocation_percent in task.assigned_resources:
                    resource = self.get_resource(resource_name)
                    if not resource: # Should not happen if data is consistent
                        continue

                    # Check if current_date is a working day for this specific resource
                    if self.calendar_manager and not self.calendar_manager.is_working_day(current_date, resource.exceptions):
                        continue # Skip this day for this resource if it's an exception

                    key = f"{resource_name}_{date_key}"
                    hours_per_day = 8.0
                    if self.calendar_manager:
                        hours_per_day = self.calendar_manager.hours_per_day
                    
                    if key not in resource_daily_hours:
                        resource_daily_hours[key] = 0
                    
                    resource_daily_hours[key] += (hours_per_day * (allocation_percent / 100.0))
                
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
    
    def load_from_dict(self, data: Dict[str, Any]):
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
        self.baselines.clear()
        self.project_name = "Untitled Project"
        Task._next_id = 1
    
    def bulk_indent_tasks(self, task_ids: List[int]) -> set:
        """Indent multiple tasks at once. Returns set of new parent IDs."""
        # Sort tasks by their current position
        tasks = [self.get_task(tid) for tid in task_ids if self.get_task(tid)]
        if not tasks:
            return set()
        
        # Sort by ID to maintain order
        tasks.sort(key=lambda t: t.id)
        
        affected_parents = set()
        
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
                    affected_parents.add(previous_task.id)
        
        return affected_parents
    
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
    
    def save_to_dict(self) -> Dict[str, Any]:
        """Export all data to dictionary"""
        return {
            'project_name': self.project_name,
            'tasks': [task.to_dict(date_format=self.settings.default_date_format) for task in self.tasks],
            'resources': [resource.to_dict() for resource in self.resources], # Include resources
            'baselines': [baseline.to_dict(date_format=self.settings.default_date_format) for baseline in self.baselines], # Include baselines
        }
    
    def load_from_dict(self, data: Dict[str, Any]):
        """Import all data from dictionary with backward compatibility"""
        version = data.get('version', '1.0')
        
        Task._next_id = data.get('next_task_id', 1)
        self.project_name = data.get('project_name', 'Untitled Project')
        
        # Load settings (with backward compatibility)
        if 'settings' in data:
            self.settings.from_dict(data['settings'])
        else:
            self.settings = ProjectSettings()
        
        # Load tasks using the retrieved date format
        self.tasks = [Task.from_dict(t, date_format=self.settings.default_date_format) for t in data.get('tasks', [])]
        self._generate_wbs() # Generate WBS for loaded tasks
        
        # *** BACKWARD COMPATIBILITY: Add is_milestone to old tasks ***
        for task in self.tasks:
            if not hasattr(task, 'is_milestone'):
                task.is_milestone = False
        
        # Clear existing resources before loading new ones
        self.resources.clear()
        
        # Load resources, preserving existing ones if none are provided in the data
        loaded_resources_data = data.get('resources')
        if loaded_resources_data is not None: # Only overwrite if 'resources' key is explicitly present
            self.resources = [Resource.from_dict(r) for r in loaded_resources_data]
        
        # Ensure there's always at least a default resource if none were loaded
        if not self.resources:
            self.resources.append(Resource(name="Default Resource", max_hours_per_day=8.0, billing_rate=50.0))
        
        # Re-evaluate all task dates based on predecessors after loading
        # This is crucial for correct dependency handling on import
        for task in self.tasks:
            self._auto_calculate_dates_from_predecessors(task)
        
        # Update summary task dates after all individual task dates are set
        # This ensures hierarchy dates are correct
        for task in self.get_top_level_tasks():
            if task.is_summary:
                self._update_summary_task_dates(task.id)
        
        # Load baselines (with backward compatibility)
        self.baselines.clear()
        loaded_baselines_data = data.get('baselines')
        if loaded_baselines_data is not None:
            self.baselines = [Baseline.from_dict(b, date_format=self.settings.default_date_format) for b in loaded_baselines_data]
    
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
        self._generate_wbs()
        
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
        self._generate_wbs()
        
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
            for pred_id, dep_type, lag in task.predecessors:
                # If this predecessor was renumbered, use the new ID
                if pred_id in id_mapping:
                    updated_predecessors.append((id_mapping[pred_id], dep_type, lag))
                else:
                    updated_predecessors.append((pred_id, dep_type, lag))
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

    def calculate_critical_path(self):
        """Calculates the critical path for all tasks in the project."""
        if not self.tasks:
            return

        # 1. Initialize ES/EF for all tasks
        for task in self.tasks:
            task.early_start = None
            task.early_finish = None
            task.late_start = None
            task.late_finish = None
            task.slack = None
            task.is_critical = False

        # 2. Forward Pass: Calculate Early Start (ES) and Early Finish (EF)
        # Process tasks in topological order (or by ID for simplicity, assuming no circular deps)
        sorted_tasks = sorted(self.tasks, key=lambda t: t.id)

        for task in sorted_tasks:
            if not task.predecessors:
                task.early_start = task.start_date  # Use its own start date if no predecessors
            else:
                max_pred_ef = None
                for pred_id, dep_type_str, lag_days in task.predecessors:
                    predecessor = self.get_task(pred_id)
                    if not predecessor or not predecessor.early_finish:
                        continue # Skip if predecessor not found or not processed yet

                    dep_type = DependencyType[dep_type_str]
                    lag = timedelta(days=lag_days)

                    if dep_type == DependencyType.FS:
                        # FS: Successor starts after predecessor finishes
                        if self.calendar_manager:
                            if lag_days >= 0:
                                pred_constraint_date = self.calendar_manager.add_working_days(predecessor.early_finish, lag_days + 1)
                            else:
                                pred_constraint_date = self.calendar_manager.subtract_working_days(predecessor.early_finish, abs(lag_days) - 1)
                        else:
                            pred_constraint_date = predecessor.early_finish + timedelta(days=1) + lag
                    elif dep_type == DependencyType.SS:
                        # SS: Successor starts when predecessor starts
                        pred_constraint_date = predecessor.early_start + lag
                    elif dep_type == DependencyType.FF:
                        # FF: Successor finishes when predecessor finishes (this affects EF, not ES directly)
                        # We'll handle this by calculating ES from EF later
                        pred_constraint_date = predecessor.early_finish + lag
                    elif dep_type == DependencyType.SF:
                        # SF: Successor finishes when predecessor starts (this affects EF, not ES directly)
                        # We'll handle this by calculating ES from EF later
                        pred_constraint_date = predecessor.early_start + lag
                    else:
                        pred_constraint_date = predecessor.early_finish + timedelta(days=1) + lag # Default to FS

                    if max_pred_ef is None or pred_constraint_date > max_pred_ef:
                        max_pred_ef = pred_constraint_date

                if max_pred_ef: # If there were valid predecessors
                    task.early_start = max_pred_ef
                else:
                    task.early_start = task.start_date # Fallback if no valid predecessors or first task

            # Calculate Early Finish
            if task.early_start:
                if task.is_milestone:
                    task.early_finish = task.early_start
                else:
                    duration_days = task.calculate_duration_days(self.calendar_manager)
                    if self.calendar_manager:
                        task.early_finish = self.calendar_manager.add_working_days(task.early_start, duration_days - 1)
                    else:
                        task.early_finish = task.early_start + timedelta(days=duration_days - 1)

        # 3. Backward Pass: Calculate Late Start (LS) and Late Finish (LF)
        # Determine project finish date (latest EF of all tasks)
        project_finish_date = max(t.early_finish for t in self.tasks if t.early_finish) if self.tasks else datetime.now()

        # Initialize LF for tasks with no successors to project_finish_date
        for task in self.tasks:
            if not self.get_successors(task.id):
                task.late_finish = project_finish_date
            else:
                task.late_finish = None # Will be calculated from successors

        # Process tasks in reverse topological order (or by ID descending)
        sorted_tasks_reverse = sorted(self.tasks, key=lambda t: t.id, reverse=True)

        for task in sorted_tasks_reverse:
            if not self.get_successors(task.id):
                # Already set to project_finish_date or its own EF if it's the last task
                if not task.late_finish:
                    task.late_finish = task.early_finish # Fallback if no successors and not project end
            else:
                min_succ_ls = None
                for successor in self.get_successors(task.id):
                    if not successor.late_start:
                        continue # Successor not processed yet

                    # Find the dependency type from task to successor
                    dep_info = next(((pid, dt, ld) for pid, dt, ld in successor.predecessors if pid == task.id), None)
                    if not dep_info:
                        continue

                    _, dep_type_str, lag_days = dep_info
                    dep_type = DependencyType[dep_type_str]
                    lag = timedelta(days=lag_days)

                    if dep_type == DependencyType.FS:
                        # FS: Successor starts after predecessor finishes
                        if self.calendar_manager:
                            if lag_days >= 0:
                                succ_constraint_date = self.calendar_manager.subtract_working_days(successor.late_start, lag_days + 1)
                            else:
                                succ_constraint_date = self.calendar_manager.add_working_days(successor.late_start, abs(lag_days) - 1)
                        else:
                            succ_constraint_date = successor.late_start - timedelta(days=1) - lag
                    elif dep_type == DependencyType.SS:
                        # SS: Successor starts when predecessor starts
                        succ_constraint_date = successor.late_start - lag
                    elif dep_type == DependencyType.FF:
                        # FF: Successor finishes when predecessor finishes
                        succ_constraint_date = successor.late_finish - lag
                    elif dep_type == DependencyType.SF:
                        # SF: Successor finishes when predecessor starts
                        succ_constraint_date = successor.late_finish - lag
                    else:
                        succ_constraint_date = successor.late_start - timedelta(days=1) - lag # Default to FS

                    if min_succ_ls is None or succ_constraint_date < min_succ_ls:
                        min_succ_ls = succ_constraint_date

                if min_succ_ls: # If there were valid successors
                    task.late_finish = min_succ_ls
                else:
                    task.late_finish = task.early_finish # Fallback if no valid successors

            # Calculate Late Start
            if task.late_finish:
                if task.is_milestone:
                    task.late_start = task.late_finish
                else:
                    duration_days = task.calculate_duration_days(self.calendar_manager)
                    if self.calendar_manager:
                        task.late_start = self.calendar_manager.subtract_working_days(task.late_finish, duration_days - 1)
                    else:
                        task.late_start = task.late_finish - timedelta(days=duration_days - 1)

        # 4. Calculate Slack and Identify Critical Tasks
        for task in self.tasks:
            if task.early_start and task.late_start:
                task.slack = task.late_start - task.early_start
                # A task is critical if its slack is zero or negative (due to lag)
                task.is_critical = (task.slack <= timedelta(days=0))

    def get_cost_breakdown_data(self) -> Dict[str, Any]:
        """
        Calculates and returns monthly/daily cost breakdown data.
        Returns a dictionary with 'headers' (list of strings) and 'rows' (list of lists of strings).
        """
        if not self.get_project_start_date() or not self.get_project_end_date():
            return {'headers': ["Period", "Total"], 'rows': []}

        start_date = self.get_project_start_date()
        end_date = self.get_project_end_date()

        headers = []
        period_type = ""

        # Determine if duration is less than a month
        if (end_date - start_date).days < 30:
            period_type = "Daily"
            delta = timedelta(days=1)
            current_date = start_date
            while current_date <= end_date:
                headers.append(current_date.strftime("%d-%b"))
                current_date += delta
        else:
            period_type = "Monthly"
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                headers.append(current_date.strftime("%b-%Y"))
                current_date = (current_date + timedelta(days=32)).replace(day=1)

        column_headers = ["Period", "Total"] + [resource.name for resource in self.resources]
        rows = []

        for i, period_str in enumerate(headers):
            row_data = [period_str]
            
            period_start_dt = None
            period_end_dt = None

            if period_type == "Daily":
                period_start_dt = start_date + timedelta(days=i)
                period_end_dt = period_start_dt
            else: # Monthly breakdown
                period_start_dt = datetime.strptime(period_str, "%b-%Y")
                period_end_dt = (period_start_dt + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                # Ensure period_end_dt does not exceed project_end_date
                if period_end_dt > end_date:
                    period_end_dt = end_date

            period_total_cost = 0
            resource_costs_in_period = {res.name: 0.0 for res in self.resources}

            for task in self.tasks:
                if task.is_summary or task.is_milestone: # Skip summary tasks and milestones
                    continue

                # Determine overlap between task and current period
                overlap_start = max(task.start_date, period_start_dt)
                overlap_end = min(task.end_date, period_end_dt)

                if overlap_start <= overlap_end:
                    for resource_name, allocation_percent in task.assigned_resources:
                        resource = self.get_resource(resource_name)
                        if resource:
                            # Calculate working hours in the overlap period for this specific resource
                            overlap_working_hours = self.calendar_manager.calculate_working_hours(overlap_start, overlap_end, resource_exceptions=resource.exceptions)
                            # Calculate resource's allocated hours for this overlap
                            allocated_hours_in_overlap = overlap_working_hours * (allocation_percent / 100.0)
                            cost_for_resource_in_overlap = allocated_hours_in_overlap * resource.billing_rate
                            resource_costs_in_period[resource_name] += cost_for_resource_in_overlap            
            
            # Add Total column
            for resource_name, cost in resource_costs_in_period.items():
                period_total_cost += cost
            row_data.append(f"${period_total_cost:.2f}")

            # Add individual resource columns
            for resource in self.resources:
                cost = resource_costs_in_period[resource.name]
                row_data.append(f"${cost:.2f}")
            rows.append(row_data)
        
        return {'headers': column_headers, 'rows': rows}
    
    # Baseline Management
    
    def create_baseline(self, name: str) -> bool:
        """
        Create a new baseline from current project state
        
        Args:
            name: Name for the baseline
            
        Returns:
            True if successful, False if limit reached or name exists
        """
        # Check if we've reached the maximum of 3 baselines
        if len(self.baselines) >= 3:
            return False
        
        # Check if baseline name already exists
        if any(b.name == name for b in self.baselines):
            return False
        
        # Check if there are tasks to baseline
        if not self.tasks:
            return False
        
        # Create new baseline
        baseline = Baseline(name=name, created_date=datetime.now())
        
        # Capture snapshots of all tasks
        for task in self.tasks:
            duration = task.get_duration(self.settings.duration_unit, self.calendar_manager)
            snapshot = TaskSnapshot(
                task_id=task.id,
                task_name=task.name,
                start_date=task.start_date,
                end_date=task.end_date,
                duration=duration,
                percent_complete=task.percent_complete,
                wbs=task.wbs
            )
            baseline.add_task_snapshot(snapshot)
        
        self.baselines.append(baseline)
        return True
    
    def delete_baseline(self, name: str) -> bool:
        """
        Delete a baseline by name
        
        Args:
            name: Name of the baseline to delete
            
        Returns:
            True if successful, False if not found
        """
        initial_count = len(self.baselines)
        self.baselines = [b for b in self.baselines if b.name != name]
        return len(self.baselines) < initial_count
    
    def get_baseline(self, name: str) -> Optional[Baseline]:
        """
        Get a baseline by name
        
        Args:
            name: Name of the baseline
            
        Returns:
            Baseline object or None if not found
        """
        for baseline in self.baselines:
            if baseline.name == name:
                return baseline
        return None
    
    def get_all_baselines(self) -> List[Baseline]:
        """Get all baselines"""
        return self.baselines.copy()
    
    def rename_baseline(self, old_name: str, new_name: str) -> bool:
        """
        Rename a baseline
        
        Args:
            old_name: Current name of the baseline
            new_name: New name for the baseline
            
        Returns:
            True if successful, False if baseline not found or new name exists
        """
        # Check if new name already exists
        if any(b.name == new_name for b in self.baselines):
            return False
        
        baseline = self.get_baseline(old_name)
        if not baseline:
            return False
        
        baseline.name = new_name
        return True
    
    def get_baseline_comparison(self, baseline_name: str) -> Dict[str, Any]:
        """
        Compare current project state against a baseline
        
        Args:
            baseline_name: Name of the baseline to compare against
            
        Returns:
            Dictionary containing comparison data with variances
        """
        baseline = self.get_baseline(baseline_name)
        if not baseline:
            return {}
        
        comparisons = []
        
        for task in self.tasks:
            snapshot = baseline.get_task_snapshot(task.id)
            
            # Calculate current duration
            current_duration = task.get_duration(self.settings.duration_unit, self.calendar_manager)
            
            if snapshot:
                # Task exists in baseline - calculate variances
                start_variance_days = (task.start_date - snapshot.start_date).days
                end_variance_days = (task.end_date - snapshot.end_date).days
                duration_variance = current_duration - snapshot.duration
                completion_variance = task.percent_complete - snapshot.percent_complete
                
                comparisons.append({
                    'task_id': task.id,
                    'task_name': task.name,
                    'wbs': task.wbs,
                    'is_summary': task.is_summary,
                    # Current values
                    'current_start': task.start_date,
                    'current_end': task.end_date,
                    'current_duration': current_duration,
                    'current_complete': task.percent_complete,
                    # Baseline values
                    'baseline_start': snapshot.start_date,
                    'baseline_end': snapshot.end_date,
                    'baseline_duration': snapshot.duration,
                    'baseline_complete': snapshot.percent_complete,
                    # Variances
                    'start_variance_days': start_variance_days,
                    'end_variance_days': end_variance_days,
                    'duration_variance': duration_variance,
                    'completion_variance': completion_variance,
                    # Status indicators
                    'start_status': 'late' if start_variance_days > 0 else ('early' if start_variance_days < 0 else 'on-track'),
                    'end_status': 'late' if end_variance_days > 0 else ('early' if end_variance_days < 0 else 'on-track'),
                    'duration_status': 'over' if duration_variance > 0 else ('under' if duration_variance < 0 else 'on-track'),
                })
            else:
                # Task added after baseline
                comparisons.append({
                    'task_id': task.id,
                    'task_name': task.name,
                    'wbs': task.wbs,
                    'is_summary': task.is_summary,
                    'current_start': task.start_date,
                    'current_end': task.end_date,
                    'current_duration': current_duration,
                    'current_complete': task.percent_complete,
                    'baseline_start': None,
                    'baseline_end': None,
                    'baseline_duration': None,
                    'baseline_complete': None,
                    'start_variance_days': None,
                    'end_variance_days': None,
                    'duration_variance': None,
                    'completion_variance': None,
                    'start_status': 'new',
                    'end_status': 'new',
                    'duration_status': 'new',
                })
        
        # Check for deleted tasks (in baseline but not in current)
        for task_id, snapshot in baseline.get_all_snapshots().items():
            if not self.get_task(task_id):
                comparisons.append({
                    'task_id': task_id,
                    'task_name': snapshot.task_name + " (Deleted)",
                    'wbs': snapshot.wbs,
                    'is_summary': False,
                    'current_start': None,
                    'current_end': None,
                    'current_duration': None,
                    'current_complete': None,
                    'baseline_start': snapshot.start_date,
                    'baseline_end': snapshot.end_date,
                    'baseline_duration': snapshot.duration,
                    'baseline_complete': snapshot.percent_complete,
                    'start_variance_days': None,
                    'end_variance_days': None,
                    'duration_variance': None,
                    'completion_variance': None,
                    'start_status': 'deleted',
                    'end_status': 'deleted',
                    'duration_status': 'deleted',
                })
        
        # Sort comparisons by task ID
        comparisons.sort(key=lambda x: x['task_id'])
        
        # Calculate summary statistics
        active_comparisons = [c for c in comparisons if c['start_status'] not in ['new', 'deleted']]
        
        summary = {
            'total_tasks': len(comparisons),
            'tasks_on_track': sum(1 for c in active_comparisons if c['end_status'] == 'on-track'),
            'tasks_late': sum(1 for c in active_comparisons if c['end_status'] == 'late'),
            'tasks_early': sum(1 for c in active_comparisons if c['end_status'] == 'early'),
            'tasks_new': sum(1 for c in comparisons if c['start_status'] == 'new'),
            'tasks_deleted': sum(1 for c in comparisons if c['start_status'] == 'deleted'),
            'avg_duration_variance': sum(c['duration_variance'] for c in active_comparisons if c['duration_variance'] is not None) / len(active_comparisons) if active_comparisons else 0,
            'avg_completion_variance': sum(c['completion_variance'] for c in active_comparisons if c['completion_variance'] is not None) / len(active_comparisons) if active_comparisons else 0,
        }
        
        return {
            'baseline_name': baseline_name,
            'baseline_date': baseline.created_date,
            'comparisons': comparisons,
            'summary': summary
        }

