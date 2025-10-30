"""
Gantt Chart - Creates and updates Gantt chart visualization
Enhanced with hierarchical tasks, dependency types, and status indicators
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from data_manager import Task, DataManager, DependencyType

class GanttChart(FigureCanvas):
    """Interactive Gantt chart widget with hierarchy and status support"""
    
    def __init__(self, parent=None, dark_mode=False):
        self.fig = Figure(figsize=(14, 8))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        
        self.setParent(parent)
        self.dark_mode = dark_mode
        self.tasks: List[Task] = []
        self.data_manager: Optional[DataManager] = None
        
        # Color scheme for status indicators
        self.status_colors = {
            'red': '#F44336',      # Overdue
            'green': '#4CAF50',    # In Progress
            'grey': '#9E9E9E',     # Upcoming
            'blue': '#2196F3'      # Completed
        }
        
        # Configure interactive features
        self.fig.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        
        # Tooltip
        self.annotation = None
        
        self._setup_chart()
    
    def _setup_chart(self):
        """Setup chart appearance"""
        self.ax.clear()
        
        if self.dark_mode:
            self.fig.patch.set_facecolor('#2b2b2b')
            self.ax.set_facecolor('#2b2b2b')
            self.ax.tick_params(colors='white', which='both')
            self.ax.spines['bottom'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.spines['top'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.title.set_color('white')
            self.text_color = 'white'
            self.grid_color = '#555555'
        else:
            self.fig.patch.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.tick_params(colors='black', which='both')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.spines['top'].set_color('black')
            self.ax.spines['right'].set_color('black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.title.set_color('black')
            self.text_color = 'black'
            self.grid_color = '#d0d0d0'
    
    def update_chart(self, tasks: List[Task], data_manager: DataManager = None):
        """Update Gantt chart with new task data including hierarchy"""
        self.tasks = tasks
        self.data_manager = data_manager
        self._setup_chart()
        
        if not self.tasks:
            self.ax.text(0.5, 0.5, 'No tasks to display', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14,
                        color='gray')
            self.draw()
            return
        
        # Filter out summary tasks or show them differently
        # For now, we'll show all tasks but render summary tasks differently
        display_tasks = self._get_display_order(tasks)
        
        if not display_tasks:
            self.ax.text(0.5, 0.5, 'No tasks to display', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14,
                        color='gray')
            self.draw()
            return
        
        # Prepare data
        y_pos = list(range(len(display_tasks)))
        y_pos.reverse()  # Reverse so first task is at top
        
        # Create task name labels with hierarchy indicators
        
        task_labels = []
        for task in display_tasks:
            level = task.get_level(self.tasks) if self.data_manager else 0
            indent = "  " * level
            
            # *** ADD MILESTONE INDICATOR ***
            if task.is_milestone:
                label = f"{indent}◆ {task.id}: {task.name}"
            elif task.is_summary:
                label = f"{indent}▶ {task.id}: {task.name}"
            else:
                label = f"{indent}{task.id}: {task.name}"
            
            task_labels.append(label)
        
        # Plot bars
        for i, task in enumerate(display_tasks):
            y = y_pos[i]
            
            # Calculate bar dimensions
            start_num = mdates.date2num(task.start_date)
            duration = (task.end_date - task.start_date).days + 1
            
            # Get status color
            status_color = self.status_colors.get(task.get_status_color(), '#9E9E9E')
            
            # Different rendering for summary vs regular tasks
            if task.is_milestone:
                self._draw_milestone(y, task)
            elif task.is_summary:
                start_num = mdates.date2num(task.start_date)
                duration = (task.end_date - task.start_date).days + 1
                status_color = self.status_colors.get(task.get_status_color(), '#9E9E9E')
                self._draw_summary_task(y, start_num, duration, status_color, task)
            else:
                start_num = mdates.date2num(task.start_date)
                duration = (task.end_date - task.start_date).days + 1
                status_color = self.status_colors.get(task.get_status_color(), '#9E9E9E')
                self._draw_regular_task(y, start_num, duration, status_color, task)
            
            # Draw progress overlay
            if task.percent_complete > 0 and not task.is_summary:
                completed_duration = duration * (task.percent_complete / 100)
                self.ax.barh(y, completed_duration, left=start_num,
                           height=0.3, color=status_color, alpha=1.0,
                           edgecolor='none')
            
            # Add percentage text
            mid_date_num = start_num + duration / 2
            percent_text = f'{task.percent_complete}%'
            
            # Use white text on dark backgrounds, black on light backgrounds
            bg_color = status_color
            text_color = self._get_contrast_color(bg_color)
            
            self.ax.text(mid_date_num, y, percent_text,
                        ha='center', va='center', fontsize=8,
                        color=text_color, weight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor=bg_color, 
                                edgecolor='none', 
                                alpha=0.7))
        
        # Draw dependency arrows AFTER all bars are drawn
        self._draw_dependencies(display_tasks, y_pos)
        
        # Format axes
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(task_labels, fontsize=9)
        self.ax.set_xlabel('Timeline', fontsize=11, weight='bold')
        self.ax.set_ylabel('Tasks', fontsize=11, weight='bold')
        self.ax.set_title('Project Gantt Chart', fontsize=13, weight='bold', pad=20)
        
        # Format x-axis dates
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Rotate date labels
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid
        self.ax.grid(True, axis='x', alpha=0.3, color=self.grid_color, linestyle='--')
        
        # Add legend for status colors
        self._add_legend()
        
        # Adjust layout
        self.fig.tight_layout()
        
        # Refresh canvas
        self.draw()
    
    def _draw_milestone(self, y: float, task: Task):
        """Draw a milestone as a diamond marker"""
        from matplotlib.patches import RegularPolygon
        
        # Get milestone date
        milestone_date = mdates.date2num(task.start_date)
        
        # Choose color based on status
        status_color = self.status_colors.get(task.get_status_color(), '#FFD700')
        
        # Draw diamond
        diamond = RegularPolygon(
            (milestone_date, y),
            numVertices=4,
            radius=0.3,
            orientation=np.pi/4,  # Rotate 45 degrees to make diamond
            facecolor=status_color,
            edgecolor='black' if not self.dark_mode else 'white',
            linewidth=2,
            alpha=0.9
        )
        self.ax.add_patch(diamond)
        
        # Add completion percentage next to diamond
        text_color = 'white' if self.dark_mode else 'black'
        self.ax.text(milestone_date + 0.5, y, f'{task.percent_complete}%',
                    ha='left', va='center', fontsize=8,
                    color=text_color, weight='bold')
    
    def _get_display_order(self, tasks: List[Task]) -> List[Task]:
        """Get tasks in hierarchical display order (depth-first)"""
        if not self.data_manager:
            return sorted(tasks, key=lambda t: t.start_date)
        
        display_order = []
        
        def add_task_and_children(task: Task):
            display_order.append(task)
            children = self.data_manager.get_child_tasks(task.id)
            for child in sorted(children, key=lambda t: t.start_date):
                add_task_and_children(child)
        
        # Start with top-level tasks
        top_level = self.data_manager.get_top_level_tasks()
        for task in sorted(top_level, key=lambda t: t.start_date):
            add_task_and_children(task)
        
        return display_order
    
    def _draw_regular_task(self, y: float, start_num: float, duration: int, 
                          color: str, task: Task):
        """Draw a regular task bar"""
        # Main task bar with border
        edge_color = 'black' if not self.dark_mode else 'white'
        
        self.ax.barh(y, duration, left=start_num, 
                    height=0.4, color=color, alpha=0.7,
                    edgecolor=edge_color,
                    linewidth=1.0)
    
    def _draw_summary_task(self, y: float, start_num: float, duration: int, 
                          color: str, task: Task):
        """Draw a summary task bar (thicker with triangular markers)"""
        # Draw main bar (thicker)
        edge_color = 'black' if not self.dark_mode else 'white'
        
        # Summary bar is darker
        import matplotlib.colors as mcolors
        rgb = mcolors.to_rgb(color)
        darker_color = tuple(c * 0.7 for c in rgb)
        
        self.ax.barh(y, duration, left=start_num, 
                    height=0.6, color=darker_color, alpha=0.9,
                    edgecolor=edge_color,
                    linewidth=2.0)
        
        # Add triangular markers at start and end
        from matplotlib.patches import Polygon
        
        # Convert to axis coordinates
        end_num = start_num + duration
        
        # Start triangle (pointing right)
        start_triangle = Polygon([
            (start_num, y - 0.5),
            (start_num, y + 0.5),
            (start_num + duration * 0.02, y)
        ], closed=True, facecolor=edge_color, edgecolor=edge_color, linewidth=1)
        self.ax.add_patch(start_triangle)
        
        # End triangle (pointing left)
        end_triangle = Polygon([
            (end_num, y - 0.5),
            (end_num, y + 0.5),
            (end_num - duration * 0.02, y)
        ], closed=True, facecolor=edge_color, edgecolor=edge_color, linewidth=1)
        self.ax.add_patch(end_triangle)
    
    def _draw_dependencies(self, display_tasks: List[Task], y_pos: List[int]):
        """Draw dependency arrows with type indicators"""
        # Create task position mapping
        task_positions = {task.id: y_pos[i] for i, task in enumerate(display_tasks)}
        
        for i, task in enumerate(display_tasks):
            if not task.predecessors:
                continue
            
            task_y = y_pos[i]
            task_start = mdates.date2num(task.start_date)
            task_end = mdates.date2num(task.end_date)
            
            for pred_id, dep_type_str in task.predecessors:
                # Find predecessor in display list
                pred_task = next((t for t in display_tasks if t.id == pred_id), None)
                if not pred_task:
                    continue
                
                pred_y = task_positions[pred_id]
                pred_start = mdates.date2num(pred_task.start_date)
                pred_end = mdates.date2num(pred_task.end_date)
                
                # Get dependency type
                try:
                    dep_type = DependencyType[dep_type_str]
                except:
                    dep_type = DependencyType.FS
                
                # Draw arrow based on dependency type
                self._draw_dependency_arrow(
                    pred_start, pred_end, pred_y,
                    task_start, task_end, task_y,
                    dep_type
                )
    
    def _draw_dependency_arrow(self, pred_start: float, pred_end: float, pred_y: float,
                              task_start: float, task_end: float, task_y: float,
                              dep_type: DependencyType):
        """Draw a single dependency arrow with appropriate style"""
        # Arrow colors by type
        arrow_colors = {
            DependencyType.FS: '#D32F2F',  # Red
            DependencyType.SS: '#1976D2',  # Blue
            DependencyType.FF: '#388E3C',  # Green
            DependencyType.SF: '#F57C00'   # Orange
        }
        
        arrow_color = arrow_colors.get(dep_type, '#D32F2F')
        
        # Determine arrow start and end points based on dependency type
        if dep_type == DependencyType.FS:
            # Finish-to-Start: from predecessor end to task start
            x_from = pred_end
            x_to = task_start
        elif dep_type == DependencyType.SS:
            # Start-to-Start: from predecessor start to task start
            x_from = pred_start
            x_to = task_start
        elif dep_type == DependencyType.FF:
            # Finish-to-Finish: from predecessor end to task end
            x_from = pred_end
            x_to = task_end
        else:  # SF
            # Start-to-Finish: from predecessor start to task end
            x_from = pred_start
            x_to = task_end
        
        # Draw multi-segment arrow for better visibility
        y_from = pred_y
        y_to = task_y
        
        # Calculate control points for curved arrow
        mid_x = (x_from + x_to) / 2
        
        # If tasks are on different levels, use a stepped arrow
        if abs(y_from - y_to) > 0.5:
            # Three-segment arrow: horizontal, vertical, horizontal
            self.ax.plot([x_from, mid_x], [y_from, y_from], 
                        color=arrow_color, linewidth=1.5, alpha=0.7, linestyle='--')
            self.ax.plot([mid_x, mid_x], [y_from, y_to], 
                        color=arrow_color, linewidth=1.5, alpha=0.7, linestyle='--')
            self.ax.plot([mid_x, x_to], [y_to, y_to], 
                        color=arrow_color, linewidth=1.5, alpha=0.7, linestyle='--')
            
            # Arrow head at the end
            self.ax.annotate('', xy=(x_to, y_to), xytext=(mid_x, y_to),
                           arrowprops=dict(arrowstyle='->', 
                                         color=arrow_color,
                                         lw=2,
                                         alpha=0.8))
        else:
            # Simple straight arrow for same level
            self.ax.annotate('', xy=(x_to, y_to), xytext=(x_from, y_from),
                           arrowprops=dict(arrowstyle='->', 
                                         color=arrow_color,
                                         lw=1.5,
                                         alpha=0.7,
                                         linestyle='--'))
        
        # Add dependency type label at midpoint
        label_x = mid_x
        label_y = (y_from + y_to) / 2
        
        # Small label showing dependency type
        self.ax.text(label_x, label_y, dep_type.name,
                    fontsize=7, color=arrow_color,
                    bbox=dict(boxstyle='round,pad=0.2', 
                            facecolor='white' if not self.dark_mode else '#2b2b2b',
                            edgecolor=arrow_color,
                            alpha=0.8),
                    ha='center', va='center')
    
    def _add_legend(self):
        """Add status color legend"""
        legend_elements = [
            mpatches.Patch(facecolor=self.status_colors['red'], 
                          edgecolor='black', label='Overdue'),
            mpatches.Patch(facecolor=self.status_colors['green'], 
                          edgecolor='black', label='In Progress'),
            mpatches.Patch(facecolor=self.status_colors['grey'], 
                          edgecolor='black', label='Upcoming'),
            mpatches.Patch(facecolor=self.status_colors['blue'], 
                          edgecolor='black', label='Completed'),
        ]
        
        # Add dependency type indicators
        from matplotlib.lines import Line2D
        
        dep_legend = [
            Line2D([0], [0], color='#D32F2F', lw=2, linestyle='--', label='FS'),
            Line2D([0], [0], color='#1976D2', lw=2, linestyle='--', label='SS'),
            Line2D([0], [0], color='#388E3C', lw=2, linestyle='--', label='FF'),
            Line2D([0], [0], color='#F57C00', lw=2, linestyle='--', label='SF'),
        ]
        
        all_elements = legend_elements + dep_legend
        
        legend = self.ax.legend(handles=all_elements, 
                               loc='upper left',
                               bbox_to_anchor=(1.01, 1),
                               fontsize=8,
                               title='Status & Dependencies',
                               title_fontsize=9,
                               framealpha=0.9)
        
        if self.dark_mode:
            legend.get_frame().set_facecolor('#2b2b2b')
            legend.get_frame().set_edgecolor('white')
            for text in legend.get_texts():
                text.set_color('white')
            legend.get_title().set_color('white')
    
    def _get_contrast_color(self, bg_color: str) -> str:
        """Get contrasting text color (black or white) based on background"""
        import matplotlib.colors as mcolors
        
        # Convert to RGB
        rgb = mcolors.to_rgb(bg_color)
        
        # Calculate luminance
        luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        
        # Return black for light backgrounds, white for dark
        return 'white' if luminance < 0.5 else 'black'
    
    def _on_scroll(self, event):
        """Handle zoom on scroll"""
        if event.inaxes != self.ax:
            return
        
        # Get current limits
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # Calculate zoom factor
        zoom_factor = 1.1 if event.button == 'down' else 0.9
        
        # Zoom X axis
        xdata = event.xdata
        new_width = (cur_xlim[1] - cur_xlim[0]) * zoom_factor
        rel_x = (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        
        new_xlim = [xdata - new_width * rel_x,
                    xdata + new_width * (1 - rel_x)]
        
        self.ax.set_xlim(new_xlim)
        
        # Also zoom Y axis slightly
        ydata = event.ydata
        if ydata is not None:
            new_height = (cur_ylim[1] - cur_ylim[0]) * zoom_factor
            rel_y = (ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])
            
            new_ylim = [ydata - new_height * rel_y,
                        ydata + new_height * (1 - rel_y)]
            
            self.ax.set_ylim(new_ylim)
        
        self.draw()
    
    def _on_hover(self, event):
        """Show tooltip on hover"""
        if event.inaxes != self.ax or not self.tasks:
            if self.annotation:
                self.annotation.set_visible(False)
                self.draw_idle()
            return
        
        # Find task under cursor
        if event.ydata is None:
            return
        
        # Get display tasks in same order as chart
        display_tasks = self._get_display_order(self.tasks)
        y_positions = list(range(len(display_tasks)))
        y_positions.reverse()
        
        # Find closest task
        closest_task = None
        min_distance = float('inf')
        
        for i, task in enumerate(display_tasks):
            y = y_positions[i]
            distance = abs(event.ydata - y)
            
            if distance < 0.5 and distance < min_distance:
                # Check if x is within task range
                start_num = mdates.date2num(task.start_date)
                end_num = mdates.date2num(task.end_date)
                
                if start_num <= event.xdata <= end_num:
                    min_distance = distance
                    closest_task = (task, y)
        
        if closest_task:
            task, y = closest_task
            
            # Create or update annotation
            if self.annotation is None:
                self.annotation = self.ax.annotate(
                    '', xy=(0, 0), xytext=(20, 20),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', 
                            facecolor='yellow' if not self.dark_mode else '#444444',
                            edgecolor='black',
                            alpha=0.95),
                    fontsize=9,
                    color=self.text_color
                )
            
            # Format tooltip text
            tooltip_text = f"Task: {task.name}\n"
            tooltip_text += f"ID: {task.id}\n"
            tooltip_text += f"Start: {task.start_date.strftime('%Y-%m-%d')}\n"
            tooltip_text += f"End: {task.end_date.strftime('%Y-%m-%d')}\n"
            tooltip_text += f"Duration: {task.duration} days\n"
            tooltip_text += f"Complete: {task.percent_complete}%\n"
            tooltip_text += f"Status: {task.get_status_text()}"
            
            if task.is_summary:
                tooltip_text += "\n[Summary Task]"
            
            if task.assigned_resources:
                tooltip_text += f"\nResources: {', '.join(task.assigned_resources)}"
            
            if task.predecessors:
                pred_info = ', '.join([
                    f"{pid} ({DependencyType[dt].name})" 
                    for pid, dt in task.predecessors
                ])
                tooltip_text += f"\nPredecessors: {pred_info}"
            
            self.annotation.set_text(tooltip_text)
            self.annotation.xy = (event.xdata, y)
            self.annotation.set_visible(True)
            self.draw_idle()
        else:
            if self.annotation:
                self.annotation.set_visible(False)
                self.draw_idle()
    
    def set_dark_mode(self, enabled: bool):
        """Toggle dark mode"""
        self.dark_mode = enabled
        if self.data_manager:
            self.update_chart(self.tasks, self.data_manager)
        else:
            self.update_chart(self.tasks)