
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Tuple
from collections import deque
import copy

from data_manager.models import Task, DependencyType
from calendar_manager.calendar_manager import CalendarManager

class SimulatedTask:
    """Lightweight task object for simulation"""
    def __init__(self, task: Task, calendar_manager: CalendarManager):
        self.id = task.id
        self.name = task.name
        self.is_milestone = task.is_milestone
        self.is_summary = task.is_summary
        self.parent_id = task.parent_id
        self.predecessors = task.predecessors
        
        # Base duration (deterministic)
        self.base_duration_days = task.calculate_duration_days(calendar_manager)
        
        # Simulation state
        self.simulated_duration = 0.0
        self.start_date: datetime = task.start_date
        self.end_date: datetime = task.end_date

        self.mode_duration = float(self.base_duration_days)
        self.min_duration = self.mode_duration * 0.75
        self.max_duration = self.mode_duration * 1.25
        self.critical_driver = None

    def randomize_duration(self):
        """Randomize duration for this iteration"""
        if self.is_milestone or self.is_summary:
            self.simulated_duration = 0.0
        else:
            low = max(0.1, self.min_duration)
            high = max(low, self.max_duration)
            mode = max(low, min(high, self.mode_duration))
            
            self.simulated_duration = random.triangular(low, high, mode)

class MonteCarloSimulator:
    def __init__(self, tasks: List[Task], calendar_manager: CalendarManager):
        self.original_tasks = tasks
        self.calendar_manager = calendar_manager
        self._sim_tasks: Dict[int, SimulatedTask] = {}
        self._children_map: Dict[int, List[int]] = {}
        self._successors_map: Dict[int, List[int]] = {}
        
    def _initialize_simulation(self):
        """Prepare tasks for simulation"""
        self._sim_tasks = {t.id: SimulatedTask(t, self.calendar_manager) for t in self.original_tasks}
        
        self._children_map = {}
        self._successors_map = {}
        
        for t in self.original_tasks:
            # Build children map
            if t.parent_id is not None:
                if t.parent_id not in self._children_map:
                    self._children_map[t.parent_id] = []
                self._children_map[t.parent_id].append(t.id)
            
            # Build successors map (for faster lookup than scanning all tasks)
            for pred_id, _, _ in t.predecessors:
                if pred_id not in self._successors_map:
                    self._successors_map[pred_id] = []
                self._successors_map[pred_id].append(t.id)

    def run_simulation(self, iterations: int = 1000) -> Dict[str, Any]:
        """Run the Monte Carlo simulation"""
        self._initialize_simulation()
        
        results = {
            'completion_dates': [],
            'critical_tasks': {} # Counter for tasks on critical path
        }
        
        for i in range(iterations):
            self._run_single_iteration(results)
            
        return self._analyze_results(results, iterations)

    def _run_single_iteration(self, results: Dict):
        """Execute one simulation pass"""
        
        # 1. Randomize Durations
        for task in self._sim_tasks.values():
            task.randomize_duration()
        in_degree = {uid: 0 for uid in self._sim_tasks}
        graph = {uid: [] for uid in self._sim_tasks}
        
        for uid, task in self._sim_tasks.items():
            for pred_id, _, _ in task.predecessors:
                if pred_id in self._sim_tasks:
                    graph[pred_id].append(uid)
                    in_degree[uid] += 1
        
        # Queue for topo sort
        queue = deque([uid for uid, deg in in_degree.items() if deg == 0])
        topo_order = []
        
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        if len(topo_order) < len(self._sim_tasks):
            # Fallback: add remaining tasks
            remain = [uid for uid in self._sim_tasks if uid not in topo_order]
            topo_order.extend(remain)
            
        # 3. Calculate Dates in Topo Order
        project_start = self.original_tasks[0].start_date if self.original_tasks else datetime.now() 
       
        for uid in topo_order:
            task = self._sim_tasks[uid]
            self._calculate_task_dates(task)
            pass
        levels = []
        for uid, task in self._sim_tasks.items():
            # Calculate level (inefficient but safe)
            lvl = 0
            pid = task.parent_id
            while pid is not None and pid in self._sim_tasks:
                lvl += 1
                pid = self._sim_tasks[pid].parent_id
            levels.append((lvl, uid))
            
        # Sort levels descending (deepest first)
        levels.sort(key=lambda x: x[0], reverse=True)
        
        for _, uid in levels:
            task = self._sim_tasks[uid]
            if task.is_summary:
                self._update_summary_from_children(task)
                
        # 5. Record Project Finish
        # Find latest end date among all tasks (or just top level)
        if not self._sim_tasks:
            return
            
        max_end = max(t.end_date for t in self._sim_tasks.values())
        results['completion_dates'].append(max_end)
        
        # Track Critical Path
        # Find tasks that finish at max_end (candidates for critical path end)
        candidates = [t for t in self._sim_tasks.values() if t.end_date == max_end]
        
        visited = set()
        for cand in candidates:
            curr = cand
            while curr:
                if curr.id in visited:
                    break
                visited.add(curr.id)
                
                if curr.id not in results['critical_tasks']:
                    results['critical_tasks'][curr.id] = 0
                results['critical_tasks'][curr.id] += 1
                
                # Backtrack
                if curr.critical_driver is not None and curr.critical_driver in self._sim_tasks:
                   curr = self._sim_tasks[curr.critical_driver]
                else:
                   curr = None

    def _calculate_task_dates(self, task: SimulatedTask):
        """Calculate start and end dates based on predecessors"""
        if not task.predecessors:
            duration_days = int(round(task.simulated_duration))
            if duration_days < 0: duration_days = 0
            if task.is_milestone:
                task.end_date = task.start_date
            else:
                task.end_date = self.calendar_manager.add_working_days(
                    task.start_date, max(0, duration_days - 1)
                ) 
            return

        # Has predecessors
        latest_start = None
        latest_end = None # For FF/SF
        
        for pred_id, dep_type_str, lag_days in task.predecessors:
            if pred_id not in self._sim_tasks:
                continue
            pred = self._sim_tasks[pred_id]
            dep_type = DependencyType[dep_type_str]
            lag = timedelta(days=lag_days)
            
            if dep_type == DependencyType.FS:
                try:
                    constraint_start = self.calendar_manager.add_working_days(pred.end_date, lag_days)
                    if not pred.is_milestone:
                         constraint_start = self.calendar_manager.add_working_days(constraint_start, 1)

                    if latest_start is None or constraint_start > latest_start:
                        latest_start = constraint_start
                        task.critical_driver = pred.id
                except:
                    pass

        # Apply Start
        if latest_start:
            task.start_date = latest_start
        
        # Apply Duration -> End
        if task.is_milestone:
            task.end_date = task.start_date
        elif not task.is_summary:
            duration_days = int(round(task.simulated_duration))
            # Subtract 1 because start date is inclusive
            days_to_add = max(0, duration_days - 1)
            task.end_date = self.calendar_manager.add_working_days(task.start_date, days_to_add)

    def _update_summary_from_children(self, summary_task: SimulatedTask):
        children_ids = self._children_map.get(summary_task.id, [])
        if not children_ids:
            return
            
        children = [self._sim_tasks[cid] for cid in children_ids]
        
        start_dates = [c.start_date for c in children]
        end_dates = [c.end_date for c in children]
        
        if start_dates:
            summary_task.start_date = min(start_dates)
        if end_dates:
            summary_task.end_date = max(end_dates)

    def _analyze_results(self, results: Dict, iterations: int) -> Dict[str, Any]:
        dates = sorted(results['completion_dates'])
        if not dates:
            return {}
            
        min_date = dates[0]
        max_date = dates[-1]
        
        # P50, P80, P90
        p50_idx = int(0.50 * iterations)
        p80_idx = int(0.80 * iterations)
        p90_idx = int(0.90 * iterations)
        
        # Clamp indices
        p50_idx = min(p50_idx, len(dates)-1)
        p80_idx = min(p80_idx, len(dates)-1)
        p90_idx = min(p90_idx, len(dates)-1)
        
        p50_date = dates[p50_idx]
        p80_date = dates[p80_idx]
        p90_date = dates[p90_idx]

        timestamps = [d.timestamp() for d in dates]
        mean_ts = statistics.mean(timestamps)
        try:
            stdev_ts = statistics.stdev(timestamps)
            stdev_days = stdev_ts / (24 * 3600)
        except:
            stdev_days = 0
            
        mean_date = datetime.fromtimestamp(mean_ts)
        
        # Stats text construction
        
        return {
            'iterations': iterations,
            'min_date': min_date,
            'max_date': max_date,
            'p50_date': p50_date,
            'p80_date': p80_date,
            'p90_date': p90_date,
            'mean_date': mean_date,
            'stdev_days': stdev_days,
            'critical_tasks': results['critical_tasks']
        }
