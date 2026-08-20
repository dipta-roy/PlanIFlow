import json
import math
import os
import sys
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd

class ProjectValidator:
    """Validator for project data in JSON and Excel formats"""
    
    MAX_TASKS = 10000 
    MAX_STR_LEN = 250 

    @classmethod
    def get_schema_path(cls) -> str:
        """Resolve schema path safely across dev and frozen PyInstaller environments"""
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            possible_paths = [
                os.path.join(base_dir, 'data_manager', 'project_schema.json'),
                os.path.join(base_dir, 'project_schema.json'),
                os.path.join(os.path.dirname(sys.executable), 'data_manager', 'project_schema.json')
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    return p
            return possible_paths[0]
        else:
            return os.path.join(os.path.dirname(__file__), 'project_schema.json')
    
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
            schema_path = ProjectValidator.get_schema_path()
            with open(schema_path, 'r') as f:
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
            logging.error(f"Schema file not found at {schema_path}")
            return False, ["Validation schema file missing."]
        except ValidationError as e:
            path = " -> ".join(map(str, e.path)) if e.path else "root"
            return False, [f"JSON Validation Error at {path}: {e.message}"]
        except Exception as e:
            logging.error(f"Unexpected error during JSON validation: {e}")
            return False, [f"Unexpected validation error: {str(e)}"]

    @staticmethod
    def _has_cycle(tasks: List[Dict[str, Any]]) -> bool:
        """Check for cyclic dependencies in task dictionary list"""
        adj = {}
        for task in tasks:
            t_id = task.get('id')
            if t_id is None:
                continue
            preds = []
            for pred in task.get('predecessors', []):
                pred_id = pred[0] if isinstance(pred, (list, tuple)) else pred
                preds.append(pred_id)
            adj[t_id] = preds

        visited = set()
        stack = set()

        def visit(u):
            if u in stack:
                return True
            if u in visited:
                return False
            stack.add(u)
            for v in adj.get(u, []):
                if visit(v):
                    return True
            stack.remove(u)
            visited.add(u)
            return False

        for t_id in adj:
            if visit(t_id):
                return True
        return False

    @staticmethod
    def sanitize_string(s: Any) -> str:
        """Sanitize and trim string to MAX_STR_LEN"""
        if s is None or (isinstance(s, float) and math.isnan(s)):
            return ""
        # Convert to string, trim whitespace, and truncate
        s_str = str(s).strip()
        if len(s_str) > ProjectValidator.MAX_STR_LEN:
            s_str = s_str[:ProjectValidator.MAX_STR_LEN]
        return "".join(char for char in s_str if ord(char) >= 32 or char in '\n\r\t')

    @staticmethod
    def _validate_excel_row(row, df_tasks, errors: List[str]):
        import pandas as pd
        task_name = row.get('Task Name', 'Unknown')
        task_id = row.get('Task ID', '?')
        
        if '% Complete' in df_tasks.columns:
            try:
                comp = float(row['% Complete'])
                if not (0 <= comp <= 100):
                    errors.append(f"Task '{task_name}' (ID {task_id}) has invalid completion %: {comp}")
            except (ValueError, TypeError):
                errors.append(f"Task '{task_name}' (ID {task_id}) has non-numeric completion %")
        
        if 'Parent ID' in df_tasks.columns:
            parent_id = row['Parent ID']
            if pd.notna(parent_id) and str(parent_id).strip() != '':
                try:
                    p_id = int(float(parent_id))
                    if not (df_tasks['Task ID'] == p_id).any():
                        errors.append(f"Task '{task_name}' (ID {task_id}) has non-existent parent ID {p_id}")
                except (ValueError, TypeError):
                    errors.append(f"Task '{task_name}' (ID {task_id}) has invalid parent ID format: {parent_id}")

        if 'Schedule Mode' in df_tasks.columns:
            mode = str(row['Schedule Mode']).strip()
            allowed = ['Auto Scheduled', 'Manually Scheduled', 'Auto', 'Manual', 'A', 'M', '(A)', '(M)']
            if mode not in allowed:
                errors.append(f"Task '{task_name}' (ID {task_id}) has invalid Schedule Mode: '{mode}'")

        start_date = row.get('Start Date')
        end_date = row.get('End Date')
        try:
            if pd.notna(start_date) and pd.notna(end_date):
                s_dt = pd.to_datetime(start_date) if isinstance(start_date, str) else start_date
                e_dt = pd.to_datetime(end_date) if isinstance(end_date, str) else end_date
                if s_dt > e_dt:
                    errors.append(f"Task '{task_name}' (ID {task_id}) has start date after end date")
        except Exception:
            pass

        if len(str(task_name)) > ProjectValidator.MAX_STR_LEN:
            errors.append(f"Task name too long (ID {task_id})")
        if 'Notes' in df_tasks.columns:
            notes = row.get('Notes', '')
            if pd.notna(notes) and len(str(notes)) > ProjectValidator.MAX_STR_LEN:
                errors.append(f"Task notes too long (ID {task_id})")

    @staticmethod
    def validate_excel(filepath: str) -> Tuple[bool, List[str]]:
        """Validate an Excel file before import."""
        errors: List[str] = []
        sheets: List[str] = []
        try:
            excel_file = pd.ExcelFile(filepath)
            sheets = excel_file.sheet_names
            if 'Tasks' not in sheets:
                errors.append("Missing required sheet: 'Tasks'")
                return False, errors
                
            df_tasks = pd.read_excel(filepath, sheet_name='Tasks')
            if len(df_tasks) > ProjectValidator.MAX_TASKS:
                errors.append(f"Excel file exceeds maximum allowed tasks ({ProjectValidator.MAX_TASKS})")
                return False, errors
                
            required_cols = ['Task ID', 'Task Name', 'Start Date', 'End Date']
            for col in required_cols:
                if col not in df_tasks.columns:
                    errors.append(f"Missing required column in Tasks sheet: '{col}'")
            if errors:
                return False, errors
                
            if df_tasks['Task ID'].duplicated().any():
                dup_ids = df_tasks[df_tasks['Task ID'].duplicated()]['Task ID'].unique()
                errors.append(f"Duplicate Task IDs found in Excel: {list(dup_ids)}")
                
            for _, row in df_tasks.iterrows():
                ProjectValidator._validate_excel_row(row, df_tasks, errors)

            # 5. Circular Dependency Detection and Predecessor Format Validation for Excel
            tasks_list: List[Dict[str, Any]] = []
            valid_dep_values = ["finish-to-start", "start-to-start", "finish-to-finish", "start-to-finish", "fs", "ss", "ff", "sf"]
            
            for _, row in df_tasks.iterrows():
                task_id = int(row['Task ID'])
                task_name = row.get('Task Name', 'Unknown')
                pred_list = []
                pred_str = str(row.get('Predecessors', '')).strip()
                
                if pred_str and pred_str != 'nan' and pred_str != '':
                    if '(' in pred_str:
                        # New format: "1 (FS), 2 (SS+2d)" or "1 (Finish-to-Start)"
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
                                type_match = re.match(r'^([a-zA-Z\-]+)', content)
                                if type_match:
                                    dep_val = type_match.group(1).strip()
                                    if dep_val.lower() not in valid_dep_values:
                                        errors.append(f"Task '{task_name}' (ID {task_id}) has unknown dependency type: '{dep_val}'")
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
