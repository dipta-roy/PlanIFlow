class CommandManager:
    """Manages command history for undo/redo"""
    
    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []
        self._max_history = 100

    def execute_command(self, command):
        """Execute a command and add to history"""
        if command.execute():
            self._undo_stack.append(command)
            self._redo_stack.clear() # Clear redo stack on new action
            
            # Limit history size
            if len(self._undo_stack) > self._max_history:
                self._undo_stack.pop(0)
            return True
        return False

    def undo(self):
        """Undo the last command"""
        if not self._undo_stack:
            return False
            
        command = self._undo_stack.pop()
        if command.undo():
            self._redo_stack.append(command)
            return True
        else:
            self._redo_stack.append(command) 
            return False

    def redo(self):
        """Redo the last undone command"""
        if not self._redo_stack:
            return False
            
        command = self._redo_stack.pop()
        if command.execute():
            self._undo_stack.append(command)
            return True
        else:
            self._redo_stack.append(command)
            return False

    def can_undo(self):
        return len(self._undo_stack) > 0

    def can_redo(self):
        return len(self._redo_stack) > 0
