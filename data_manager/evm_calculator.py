import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from data_manager.models import Task, Resource, Baseline, TaskSnapshot
from settings_manager.settings_manager import DurationUnit

class EVMCalculator:
    """
    Earned Value Management (EVM) Calculator for PlanIFlow.
    Mirrors Microsoft Project's basic EVM metrics.
    """
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def calculate_metrics(self, baseline_name: str, status_date: datetime = None) -> pd.DataFrame:
        """
        Calculate EVM metrics for all tasks based on a specific baseline.
        
        Args:
            baseline_name: Name of the baseline to use for PV calculations.
            status_date: The date at which to calculate progress (defaults to today).
            
        Returns:
            pandas.DataFrame with columns: Task, WBS, PV, EV, AC, CV, SV, CPI, SPI, BAC, EAC, VAC.
        """
        if status_date is None:
            status_date = datetime.now()
            
        baseline = self.data_manager.get_baseline(baseline_name)
        if not baseline:
            return pd.DataFrame()
            
        tasks = self.data_manager.get_all_tasks()
        resources = {r.name: r for r in self.data_manager.get_all_resources()}
        calendar = self.data_manager.calendar_manager
        
        results = []
        
        for task in tasks:
            # We include both individual tasks and calculate summaries based on their children
            # Microsoft Project shows EVM for both.
            
            snapshot = baseline.get_task_snapshot(task.id)
            
            # 1. Budgeted Cost (BAC) - Total planned cost for the task
            # If snapshot exists, use its duration. Otherwise, skip or warn.
            if not snapshot:
                continue
                
            bac = self._calculate_bac(task, snapshot, resources, calendar)
            
            # 2. Planned Value (PV) - Value of work that should be done by status_date
            pv = self._calculate_pv(snapshot, bac, status_date, calendar)
            
            # 3. Earned Value (EV) - Value of work actually performed
            ev = (task.percent_complete / 100.0) * bac
            
            # 4. Actual Cost (AC) - Cost incurred for work performed
            ac = self._calculate_ac(task, resources, status_date, calendar)
            
            # 5. Variances
            cv = ev - ac
            sv = ev - pv
            
            # 6. Indices (handle division by zero)
            cpi = ev / ac if ac > 0 else (1.0 if ev > 0 else 1.0)
            spi = ev / pv if pv > 0 else (1.0 if ev > 0 else 1.0)
            
            # 7. Forecasts
            # EAC = AC + (BAC - EV) / CPI = BAC / CPI
            eac = bac / cpi if cpi > 0 else bac
            vac = bac - eac
            
            results.append({
                'Task ID': task.id,
                'WBS': task.wbs or '',
                'Task': task.name,
                'PV': pv,
                'EV': ev,
                'AC': ac,
                'BAC': bac,
                'CV': cv,
                'SV': sv,
                'CPI': cpi,
                'SPI': spi,
                'EAC': eac,
                'VAC': vac,
                'is_summary': task.is_summary
            })
            
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results)
        return df

    def _calculate_bac(self, task: Task, snapshot: TaskSnapshot, resources: Dict[str, Resource], calendar) -> float:
        """Calculate Budgeted Cost at Completion (BAC) based on baseline duration."""
        # Baseline duration in hours
        if calendar:
            # TaskSnapshot stores duration in project units (days or hours)
            # We need standard working hours
            hours = calendar.calculate_working_hours(snapshot.start_date, snapshot.end_date)
        else:
            # Fallback if no calendar
            hours = snapshot.duration * 8.0 # Assume 8h/day
            
        total_rate = 0.0
        # Use current resource assignments for the rate
        for r_name, allocation in task.assigned_resources:
            res = resources.get(r_name)
            if res:
                total_rate += (allocation / 100.0) * res.billing_rate
                
        return hours * total_rate

    def _calculate_pv(self, snapshot: TaskSnapshot, bac: float, status_date: datetime, calendar) -> float:
        """Calculate Planned Value (PV) at a given status date."""
        if status_date <= snapshot.start_date:
            return 0.0
        if status_date >= snapshot.end_date:
            return bac
            
        # Planned progress = (Time passed) / (Total duration)
        if calendar:
            total_hours = calendar.calculate_working_hours(snapshot.start_date, snapshot.end_date)
            passed_hours = calendar.calculate_working_hours(snapshot.start_date, status_date)
        else:
            total_days = (snapshot.end_date - snapshot.start_date).days or 1
            passed_days = (status_date - snapshot.start_date).days
            total_hours, passed_hours = total_days, passed_days

        planned_progress = passed_hours / total_hours if total_hours > 0 else 1.0
        return planned_progress * bac

    def _calculate_ac(self, task: Task, resources: Dict[str, Resource], status_date: datetime, calendar) -> float:
        """Calculate Actual Cost (AC) as the cost of resources for time elapsed or work done."""
        # Since we don't have separate 'Actual Work' field, we estimate AC based on elapsed time
        # but capped by progress if the task is behind, or extending if it's over?
        # Actually, MS Project basic AC follows actual hours.
        # Let's use: AC = Actual Hours Spent * Rate
        
        if status_date <= task.start_date:
            return 0.0
            
        # Actual hours spent so far
        if calendar:
            # We assume work is done up to status_date OR task completion
            end_calc = min(status_date, task.end_date)
            # If task is 100% complete, use actual end date (which is current end_date)
            if task.percent_complete == 100:
                end_calc = task.end_date
            
            hours_spent = calendar.calculate_working_hours(task.start_date, end_calc)
        else:
            end_calc = min(status_date, task.end_date)
            hours_spent = (end_calc - task.start_date).days * 8.0
            
        total_rate = 0.0
        for r_name, allocation in task.assigned_resources:
            res = resources.get(r_name)
            if res:
                total_rate += (allocation / 100.0) * res.billing_rate
                
        return max(0.0, hours_spent * total_rate)

    def get_summary_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate aggregated project-level EVM metrics."""
        if df.empty:
            return {}
            
        # Filter out summary tasks to avoid double counting if only leaf tasks are provided,
        # but usually summary tasks represent the roll-up. 
        # In our case, we calculate per task. Summing non-summary tasks gives project total.
        leaf_tasks = df[~df['is_summary']]
        
        pv_total = leaf_tasks['PV'].sum()
        ev_total = leaf_tasks['EV'].sum()
        ac_total = leaf_tasks['AC'].sum()
        bac_total = leaf_tasks['BAC'].sum()
        
        cv = ev_total - ac_total
        sv = ev_total - pv_total
        cpi = ev_total / ac_total if ac_total > 0 else (1.0 if ev_total > 0 else 1.0)
        spi = ev_total / pv_total if pv_total > 0 else (1.0 if ev_total > 0 else 1.0)
        
        eac = bac_total / cpi if cpi > 0 else bac_total
        vac = bac_total - eac
        
        return {
            'PV': pv_total,
            'EV': ev_total,
            'AC': ac_total,
            'BAC': bac_total,
            'CV': cv,
            'SV': sv,
            'CPI': cpi,
            'SPI': spi,
            'EAC': eac,
            'VAC': vac
        }
