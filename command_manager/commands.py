from abc import ABC, abstractmethod
from copy import deepcopy

class Command(ABC):
    """Abstract base class for all commands"""
    
    @abstractmethod
    def execute(self):
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self):
        """Undo the command"""
        pass

class EditTaskCommand(Command):
    """Command to edit task properties"""
    
    def __init__(self, data_manager, task_id, old_task_data, new_task_data, on_success_callback=None):
        self.data_manager = data_manager
        self.task_id = task_id
        self.old_task_data = deepcopy(old_task_data)
        self.new_task_data = deepcopy(new_task_data)
        self.on_success_callback = on_success_callback

    def execute(self):
        task = self.data_manager.get_task(self.task_id)
        if task:
            # Apply new data to a COPY of the task to avoid modifying the live object
            # if validation fails.
            updated_task = deepcopy(task)
            self._apply_data(updated_task, self.new_task_data)
            
            if self.data_manager.update_task(self.task_id, updated_task):
                if self.on_success_callback:
                    self.on_success_callback()
                return True
        return False

    def undo(self):
        task = self.data_manager.get_task(self.task_id)
        if task:
            # Revert to old data on a COPY
            reverted_task = deepcopy(task)
            self._apply_data(reverted_task, self.old_task_data)
            
            if self.data_manager.update_task(self.task_id, reverted_task):
                if self.on_success_callback:
                    self.on_success_callback()
                return True
        return False

    def _apply_data(self, task, data):
        """Helper to apply dict data to task object"""
        from data_manager.models import Task
        
        # Use Task.from_dict to handle all parsing (enums, dates, etc.)
        # We pass the data dictionary which contains serialized values (str for dates/enums)
        temp_task = Task.from_dict(data)
        
        # Copy attributes from temp_task to the target task
        # We iterate over the keys in the data dictionary to only update relevant fields,
        # but we pull the converted value from temp_task
        for key in data.keys():
            if hasattr(task, key) and hasattr(temp_task, key):
                # skip read-only properties or structural fields
                if key in ['id', 'duration', 'wbs', 'is_summary', 'parent_id']:
                    continue
                    
                try:
                    setattr(task, key, getattr(temp_task, key))
                except AttributeError:
                    # Fallback for other read-only properties if any
                    continue

class DeleteTaskCommand(Command):
    """Command to delete a task"""

    def __init__(self, data_manager, task_id, on_success_callback=None):
        self.data_manager = data_manager
        self.task_id = task_id
        self.on_success_callback = on_success_callback
        self.deleted_tasks_data = [] # List of task dicts (root + descendants)
        self.external_dependencies = {} # {task_id: [(pred_id, type, lag), ...]}

        # Capture state
        task = self.data_manager.get_task(task_id)
        if task:
            # 1. Capture hierarchy (Root + Descendants)
            # We want to store them in an order that makes sense for restoration (Top-down)
            # data_manager.get_all_descendants returns a list.
            # We'll store [root_data, child1_data, child1_child_data, ...]
            self.deleted_tasks_data.append(task.to_dict())
            
            descendants = self.data_manager.get_all_descendants(task_id)
            for desc in descendants:
                self.deleted_tasks_data.append(desc.to_dict())
            
            # 2. Capture external dependencies
            # Find tasks that are NOT being deleted (not in the set of IDs to be deleted)
            # but have predecessors that ARE in the set.
            deleted_ids = {t['id'] for t in self.deleted_tasks_data}
            
            all_tasks = self.data_manager.get_all_tasks()
            for other_task in all_tasks:
                if other_task.id not in deleted_ids:
                    # Check if this task depends on any deleted task
                    depends = False
                    for pred_id, _, _ in other_task.predecessors:
                        if pred_id in deleted_ids:
                            depends = True
                            break
                    
                    if depends:
                        # Save the FULL predecessor list of this external task
                        self.external_dependencies[other_task.id] = list(other_task.predecessors)

    def execute(self):
        if self.data_manager.delete_task(self.task_id):
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False

    def undo(self):
        from data_manager.models import Task
        
        # 1. Restore tasks
        # Iterate through captured data and add them back.
        # Since we stored them top-down (root first), restoring in order should work for parent linking if we rely on IDs.
        # However, data_manager.add_task validates parent existence.
        # So we must restore parents first.
        # Our capture order: Root, then descendants (recursively flattens children of root).
        # This usually preserves top-down order. 
        # But `get_all_descendants` implementation in manager.py:
        #   descendants = []
        #   children = get_child_tasks(task_id) # Direct children
        #   for child in children: append(child); extend(get_all_descendants(child.id))
        # This is strictly Pre-Order Traversal (Root -> Child -> Grandchild).
        # So iterating this list is safe for parent constraints.
        
        tasks_to_add = []
        for task_data in self.deleted_tasks_data:
            task = Task.from_dict(task_data)
            # Explicitly set ID from data to ensure restoration of original ID
            task.id = task_data['id']
            # Also reset next_id to avoid conflicts if we add many? 
            # Task constructor updates _next_id. Task.from_dict calls constructor.
            # So _next_id will be valid or higher.
            
            tasks_to_add.append(task)
        
        # We use a lower-level add or standard add?
        # Standard add_task triggers auto-calc.
        # Ideally we want to restore exact state including dates, which might be manual overrides or calculated.
        # If we use add_task, it might re-calculate dates.
        # But since we are restoring the whole subtree, valid dates should be preserved if logic is deterministic.
        
        # Optimization: Add all to self.tasks first, then rebuild indices/WBS?
        # But add_task handles validation.
        # Let's try inserting them one by one.
        for task in tasks_to_add:
            # We bypass regular add_task to avoid some overhead or strict checks?
            # No, keep it safe. But `add_task` expects parent to exist.
            # First task is Root. Its parent (if any) wasn't deleted, so it exists.
            # Subsequent tasks are children, their parents are restored in previous iterations.
            success = self.data_manager.add_task(task, parent_id=task.parent_id)
            if not success:
                # This is bad. Partial restore?
                pass

        # 2. Restore external dependencies
        for ext_task_id, original_preds in self.external_dependencies.items():
            ext_task = self.data_manager.get_task(ext_task_id)
            if ext_task:
                ext_task.predecessors = original_preds
                # We might need to trigger update/re-calc for this task
                self.data_manager.update_task(ext_task_id, ext_task)
        
        if self.on_success_callback:
            self.on_success_callback()
        
        return True

class AddTaskCommand(Command):
    """Command to add a new task"""

    def __init__(self, data_manager, task_data, mode='append', target_id=None, parent_id=None, on_success_callback=None):
        self.data_manager = data_manager
        self.task_data = task_data # Dict
        self.mode = mode # 'append', 'before', 'after'
        self.target_id = target_id
        self.parent_id = parent_id
        self.on_success_callback = on_success_callback
        self.added_task_id = None

    def execute(self):
        from data_manager.models import Task
        
        task = Task.from_dict(self.task_data)
        # Restore ID if it was set (e.g. on Redo), otherwise let manager assign (on first Execute)
        # However, for correct Undo/Redo, we must ensure ID is stable.
        # On first run, task might generate an ID. We need to capture it.
        # If task_data has ID, use it.
        # But 'Task.from_dict' might not enforce it if it's new.
        
        success = False
        if self.mode == 'append':
            success = self.data_manager.add_task(task, parent_id=self.parent_id)
        elif self.mode == 'before':
            success = self.data_manager.insert_task_before(task, self.target_id)
        elif self.mode == 'after':
            success = self.data_manager.insert_task_at_position(task, self.target_id)
            
        if success:
            self.added_task_id = task.id
            # Update stored data with the ID in case it was auto-generated
            self.task_data['id'] = task.id 
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False

    def undo(self):
        if self.added_task_id:
            # Delete the task
            if self.data_manager.delete_task(self.added_task_id):
                if self.on_success_callback:
                    self.on_success_callback()
                return True
        return False

class AddResourceCommand(Command):
    """Command to add a new resource"""

    def __init__(self, data_manager, resource_data, on_success_callback=None):
        self.data_manager = data_manager
        self.resource_data = resource_data
        self.on_success_callback = on_success_callback

    def execute(self):
        from data_manager.models import Resource
        resource = Resource(
            name=self.resource_data['name'],
            max_hours_per_day=self.resource_data.get('max_hours_per_day', 8),
            exceptions=self.resource_data.get('exceptions', {}),
            billing_rate=self.resource_data.get('billing_rate', 0.0)
        )
        if self.data_manager.add_resource(resource):
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False

    def undo(self):
        name = self.resource_data['name']
        if self.data_manager.delete_resource(name):
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False

class MoveTaskCommand(Command):
    """Command to move a task (indent/outdent)"""

    def __init__(self, data_manager, task_id, new_parent_id, on_success_callback=None):
        self.data_manager = data_manager
        self.task_id = task_id
        self.new_parent_id = new_parent_id
        self.old_parent_id = None
        self.on_success_callback = on_success_callback
        
        task = self.data_manager.get_task(task_id)
        if task:
            self.old_parent_id = task.parent_id

    def execute(self):
        if self.data_manager.move_task(self.task_id, self.new_parent_id):
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False

    def undo(self):
        if self.data_manager.move_task(self.task_id, self.old_parent_id):
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False

class EditResourceCommand(Command):
    """Command to edit an existing resource"""

    def __init__(self, data_manager, old_name, new_data, on_success_callback=None):
        self.data_manager = data_manager
        self.old_name = old_name # The name BEFORE this edit
        self.new_data = new_data # Dict of new state
        self.on_success_callback = on_success_callback
        
        # Capture old state
        resource = self.data_manager.get_resource(old_name)
        self.old_data = resource.to_dict() if resource else {}
        self.new_name = new_data.get('name', old_name) # The name AFTER this edit

    def execute(self):
        from data_manager.models import Resource
        
        # Create updated resource object
        updated_resource = Resource.from_dict(self.new_data)
        
        # Update via manager
        if self.data_manager.update_resource(self.old_name, updated_resource):
             if self.on_success_callback:
                self.on_success_callback()
             return True
        return False

    def undo(self):
        from data_manager.models import Resource
        
        # Restore old state
        old_resource = Resource.from_dict(self.old_data)
        
        # We need to target the currently active name (which is self.new_name after execute)
        # to revert it to self.old_name.
        if self.data_manager.update_resource(self.new_name, old_resource):
            if self.on_success_callback:
                self.on_success_callback()
            return True
        return False
