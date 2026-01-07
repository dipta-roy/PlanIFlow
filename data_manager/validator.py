import json
import os
import sys
import logging
from typing import Dict, Any, List, Tuple

class ProjectValidator:
    """Validator for project data in JSON and Excel formats"""
    
    if getattr(sys, 'frozen', False):
        # Running in a frozen bundle (cx_Freeze / PyInstaller)
        # We expect data_manager/project_schema.json relative to the executable dir
        # or the lib dir depending on how it was packed.
        # With our current setup, it is in {INSTALL_DIR}/data_manager/project_schema.json
        base_dir = os.path.dirname(sys.executable)
        SCHEMA_PATH = os.path.join(base_dir, 'data_manager', 'project_schema.json')
    else:
        # Running in normal Python environment
        SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'project_schema.json')

    MAX_TASKS = 10000  # Security limit to prevent DoS
    MAX_STR_LEN = 250  # Limit for names and notes
    
    @staticmethod
    def validate_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate JSON data against the project schema.
        Returns (success: bool, errors: list of strings)
        """
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            logging.error("jsonschema library not found. JSON validation skipped.")
            return True, [] # Assume valid if we can't check, to avoid blocking user

        try:
            with open(ProjectValidator.SCHEMA_PATH, 'r') as f:
                schema = json.load(f)
            
            validate(instance=data, schema=schema)
            
            # Additional semantic validation
            errors = []
            
            project_data = data.get('project_data', {})
            tasks = project_data.get('tasks', [])
            resources = project_data.get('resources', [])
            
            # 0. Check project name length
            if len(data.get('project_name', '')) > ProjectValidator.MAX_STR_LEN:
                errors.append(f"Project name exceeds {ProjectValidator.MAX_STR_LEN} characters")

            # 0.1 Check task count limit
            if len(tasks) > ProjectValidator.MAX_TASKS:
                errors.append(f"Project exceeds maximum allowed tasks ({ProjectValidator.MAX_TASKS})")
                return False, errors

            # 1. Check if parent_ids exist
            task_ids = {t['id'] for t in tasks}
            
            for task in tasks:
                parent_id = task.get('parent_id')
                if parent_id is not None and parent_id not in task_ids:
                    errors.append(f"Task '{task['name']}' (ID {task['id']}) has non-existent parent ID {parent_id}")
                
                # 2. Check if predecessors exist
                for pred in task.get('predecessors', []):
                    pred_id = pred[0] if isinstance(pred, (list, tuple)) else pred
                    if pred_id not in task_ids:
                        errors.append(f"Task '{task['name']}' (ID {task['id']}) has non-existent predecessor ID {pred_id}")

                # 3. Check name and notes length
                if len(task.get('name', '')) > ProjectValidator.MAX_STR_LEN:
                    errors.append(f"Task name too long in ID {task.get('id', '?')}")
                if len(task.get('notes', '')) > ProjectValidator.MAX_STR_LEN:
                    errors.append(f"Task notes too long in ID {task.get('id', '?')}")

                # 4. Check date logic
                try:
                    # These are strings in JSON, need to parse them to compare
                    # Note: We don't have the DataManager's date format here, 
                    # but we can try common ones or just isoformat if it's from our app
                    from dateutil.parser import parse
                    start = parse(task['start_date'])
                    end = parse(task['end_date'])
                    if start > end:
                        errors.append(f"Task '{task['name']}' (ID {task['id']}) has start date after end date")
                except Exception:
                    # If parsing fails, the schema validation might have already caught it or it will be caught during import
                    pass

            # 5. Check for cyclic dependencies
            if ProjectValidator._has_cycle(tasks):
                errors.append("Project contains circular dependencies")

            # 6. Check resource names length
            for resource in resources:
                if len(resource.get('name', '')) > ProjectValidator.MAX_STR_LEN:
                    errors.append(f"Resource name '{resource.get('name', '')}' too long")

            # 7. Check assigned resources exist and allocations are valid
            resource_names = {r.get('name') for r in resources}
            for task in tasks:
                for res in task.get('assigned_resources', []):
                    res_name = res[0]
                    if res_name not in resource_names:
                        errors.append(f"Task '{task.get('name')}' (ID {task.get('id')}) has unlisted resource: '{res_name}'")

            # 8. Validate next_task_id
            next_id = project_data.get('next_task_id')
            if next_id is not None and task_ids and next_id <= max(task_ids):
                errors.append(f"next_task_id ({next_id}) must be greater than current maximum task ID ({max(task_ids)})")

            if errors:
                return False, errors
                
            return True, []
            
        except FileNotFoundError:
            logging.error(f"Schema file not found at {ProjectValidator.SCHEMA_PATH}")
            return False, ["Validation schema file missing."]
        except ValidationError as e:
            # ValidationError is now locally imported, so we need to handle it carefully
            # or use a generic exception if we can't import it.
            # Actually, if it's not imported, we already returned above.
            path = " -> ".join(map(str, e.path)) if e.path else "root"
            return False, [f"JSON Validation Error at {path}: {e.message}"]
        except Exception as e:
            logging.error(f"Unexpected error during JSON validation: {e}")
            return False, [f"Unexpected validation error: {str(e)}"]

    @staticmethod
    def _has_cycle(tasks: List[Dict[str, Any]]) -> bool:
        """Detect circular dependencies in a list of task dicts"""
        adj = {t['id']: [] for t in tasks}
        for t in tasks:
            for pred in t.get('predecessors', []):
                pred_id = pred[0] if isinstance(pred, (list, tuple)) else pred
                if pred_id in adj:
                    adj[t['id']].append(pred_id)
        
        visited = set()
        stack = set()
        
        def visit(u):
            if u in stack: return True
            if u in visited: return False
            stack.add(u)
            for v in adj.get(u, []):
                if visit(v): return True
            stack.remove(u)
            visited.add(u)
            return False
            
        for t_id in adj:
            if visit(t_id): return True
        return False

    @staticmethod
    def sanitize_string(s: Any) -> str:
        """Sanitize and trim string to MAX_STR_LEN"""
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return ""
        # Convert to string, trim whitespace, and truncate
        s_str = str(s).strip()
        if len(s_str) > ProjectValidator.MAX_STR_LEN:
            s_str = s_str[:ProjectValidator.MAX_STR_LEN]
        
        # Simple character sanitization: remove potential control characters
        # We can expand this if specific special characters are problematic
        return "".join(char for char in s_str if ord(char) >= 32 or char in '\n\r\t')

    @staticmethod
    def validate_excel(filepath: str) -> Tuple[bool, List[str]]:
        """
        Validate an Excel file before import.
        """
        import pandas as pd
        errors = []
        
        try:
            excel_file = pd.ExcelFile(filepath)
            sheets = excel_file.sheet_names
            
            if 'Tasks' not in sheets:
                errors.append("Missing required sheet: 'Tasks'")
            
            if errors:
                return False, errors
                
            df_tasks = pd.read_excel(filepath, sheet_name='Tasks')
            
            if len(df_tasks) > ProjectValidator.MAX_TASKS:
                errors.append(f"Excel file exceeds maximum allowed tasks ({ProjectValidator.MAX_TASKS})")
                return False, errors
                
            # 1. Validate Tasks Dataframe Columns
            required_cols = ['Task ID', 'Task Name', 'Start Date', 'End Date']
            for col in required_cols:
                if col not in df_tasks.columns:
                    errors.append(f"Missing required column in Tasks sheet: '{col}'")
            
            if errors:
                return False, errors
                
            # 2. Check for unique IDs
            if df_tasks['Task ID'].duplicated().any():
                dup_ids = df_tasks[df_tasks['Task ID'].duplicated()]['Task ID'].unique()
                errors.append(f"Duplicate Task IDs found in Excel: {list(dup_ids)}")
                
            # 3. Basic data integrity
            for _, row in df_tasks.iterrows():
                task_name = row.get('Task Name', 'Unknown')
                task_id = row.get('Task ID', '?')
                
                # Validate completion percentage if exists
                if '% Complete' in df_tasks.columns:
                    try:
                        comp = float(row['% Complete'])
                        if not (0 <= comp <= 100):
                            errors.append(f"Task '{task_name}' (ID {task_id}) has invalid completion %: {comp}")
                    except (ValueError, TypeError):
                        errors.append(f"Task '{task_name}' (ID {task_id}) has non-numeric completion %")
                
                # Hierarchy validation (Parent ID exists)
                if 'Parent ID' in df_tasks.columns:
                    parent_id = row['Parent ID']
                    if pd.notna(parent_id) and str(parent_id).strip() != '':
                        try:
                            parent_id_int = int(float(parent_id))
                            if not (df_tasks['Task ID'] == parent_id_int).any():
                                errors.append(f"Task '{task_name}' (ID {task_id}) has non-existent parent ID {parent_id_int}")
                        except (ValueError, TypeError):
                            errors.append(f"Task '{task_name}' (ID {task_id}) has invalid parent ID format: {parent_id}")

                # Validate Schedule Mode if exists
                if 'Schedule Mode' in df_tasks.columns:
                    mode = str(row['Schedule Mode'])
                    if mode not in ['Auto Scheduled', 'Manually Scheduled']:
                        errors.append(f"Task '{task_name}' (ID {task_id}) has invalid Schedule Mode: '{mode}'")

                # 4. Logical validation
                start_date = row.get('Start Date')
                end_date = row.get('End Date')
                
                # Check date logic
                try:
                    # In Excel, these might already be datetime objects or strings
                    if pd.notna(start_date) and pd.notna(end_date):
                        # Ensure they are comparable
                        if isinstance(start_date, str):
                            start_date = pd.to_datetime(start_date)
                        if isinstance(end_date, str):
                            end_date = pd.to_datetime(end_date)
                            
                        if start_date > end_date:
                            errors.append(f"Task '{task_name}' (ID {task_id}) has start date after end date")
                except:
                    pass

                # Check name length (DoS protection)
                if len(str(task_name)) > ProjectValidator.MAX_STR_LEN:
                    errors.append(f"Task name too long (ID {task_id})")
                
                # Check notes length
                if 'Notes' in df_tasks.columns:
                    notes = row.get('Notes', '')
                    if pd.notna(notes) and len(str(notes)) > ProjectValidator.MAX_STR_LEN:
                        errors.append(f"Task notes too long (ID {task_id})")

            # 5. Circular Dependency Detection and Predecessor Format Validation for Excel
            tasks_list = []
            valid_dep_values = ["Finish-to-Start", "Start-to-Start", "Finish-to-Finish", "Start-to-Finish", "FS", "SS", "FF", "SF"]
            
            for _, row in df_tasks.iterrows():
                task_id = int(row['Task ID'])
                task_name = row.get('Task Name', 'Unknown')
                pred_list = []
                pred_str = str(row.get('Predecessors', '')).strip()
                
                if pred_str and pred_str != 'nan' and pred_str != '':
                    if '(' in pred_str:
                        # New format: "1 (FS), 2 (SS+2d)"
                        import re
                        for item in pred_str.split(','):
                            item = item.strip()
                            # Match ID and then what's in parentheses
                            match = re.match(r'(\d+)\s*\((.*?)\)', item)
                            if match:
                                p_id = int(match.group(1))
                                pred_list.append(p_id)
                                content = match.group(2).strip()
                                
                                # Extract type and lag
                                type_match = re.match(r'^([A-Z\-]+)', content)
                                if type_match:
                                    dep_val = type_match.group(1).strip()
                                    # We don't necessarily need to check if it's in valid_dep_values here 
                                    # because the import logic handles fallbacks, but let's be strict if we want "validation"
                                else:
                                    errors.append(f"Task '{task_name}' (ID {task_id}) has invalid dependency type format: '{item}'")
                            else:
                                # Try matching just ID if no parentheses (fallback)
                                match_id = re.match(r'^(\d+)$', item)
                                if match_id:
                                    pred_list.append(int(match_id.group(1)))
                                else:
                                    errors.append(f"Task '{task_name}' (ID {task_id}) has invalid predecessor format: '{item}'")
                    else:
                        # Old format: "1,2,3"
                        for p in pred_str.split(','):
                            p = p.strip()
                            if p:
                                try:
                                    pred_list.append(int(p))
                                except ValueError:
                                    errors.append(f"Task '{task_name}' (ID {task_id}) has non-numeric predecessor ID: '{p}'")
                
            # 5.1 Check if all predecessor IDs exist
            task_ids_set = {t['id'] for t in tasks_list}
            for t in tasks_list:
                for p_id in t['predecessors']:
                    if p_id not in task_ids_set:
                        # Find task name for error message
                        t_name = next((row.get('Task Name', 'Unknown') for _, row in df_tasks.iterrows() if int(row['Task ID']) == t['id']), 'Unknown')
                        errors.append(f"Task '{t_name}' (ID {t['id']}) has non-existent predecessor ID: {p_id}")

            if ProjectValidator._has_cycle(tasks_list):
                errors.append("Excel file contains circular dependencies between tasks")

            # 6. Resource validation
            if 'Resources' in sheets:
                df_res = pd.read_excel(filepath, sheet_name='Resources')
                res_col = 'Resource Name' if 'Resource Name' in df_res.columns else 'Resource'
                if res_col in df_res.columns:
                    for _, row in df_res.iterrows():
                        res_name = row.get(res_col, '')
                        if pd.notna(res_name):
                            if len(str(res_name)) > ProjectValidator.MAX_STR_LEN:
                                errors.append(f"Resource name too long: {res_name}")
                            # Check billing rate if exists
                            if 'Billing Rate' in df_res.columns:
                                try:
                                    rate = float(row['Billing Rate'])
                                    if rate < 0:
                                        errors.append(f"Negative billing rate for resource: {res_name}")
                                except (ValueError, TypeError):
                                    pass

            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Error reading Excel file: {str(e)}"]
