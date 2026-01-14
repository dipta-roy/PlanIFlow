"""
Gantt Chart - Creates and updates Gantt chart visualization
Enhanced with hierarchical tasks, dependency types, and status indicators
"""
from typing import List, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from data_manager.manager import DataManager
from data_manager.models import Task, DependencyType
import constants.constants as constants

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
        self.show_summary_tasks = True # New attribute
        self.show_critical_path = False # New attribute for critical path
        self.current_scale = "Days" # Default scale
        self.display_tasks = [] # Cache for ordered tasks
        
        # Color scheme for status indicators
        self.status_colors = constants.GANTT_STATUS_COLORS
        
        # Configure interactive features
        self.fig.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        
        # Tooltip
        self.annotation = None
        
        # Panning variables
        self.panning = False
        self.press_x = None
        self.press_y = None
        
        self._setup_chart()
    
    def _setup_chart(self):
        """Setup chart appearance"""
        self.ax.clear()
        self.annotation = None # Reset annotation after clearing axes
        
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
        
        # Reset critical path flags for all tasks before potential recalculation
        for task in self.tasks:
            task.is_critical = False

        # Calculate critical path if enabled
        if self.show_critical_path and self.data_manager:
            self.data_manager.calculate_critical_path()
            
        display_items = self._get_display_order_with_levels(tasks)
        self.display_tasks = [item[0] for item in display_items]
        display_tasks = self.display_tasks
        
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
        for i, (task, level) in enumerate(display_items):
            indent = "  " * level
            
            # *** ADD MILESTONE INDICATOR ***
            if task.is_milestone:
                label = f"{indent}◆ {task.name}"
            elif task.is_summary:
                label = f"{indent}▶ {task.name}"
            else:
                label = f"{indent}{task.name}"
            
            task_labels.append(label)
        
        # Calculate date range for the chart based on displayed tasks
        if display_tasks:
            min_date = min(task.start_date for task in display_tasks)
            max_date = max(task.end_date for task in display_tasks)
            total_days = (max_date - min_date).days
        else:
            min_date = datetime.now()
            max_date = datetime.now() + timedelta(days=30)
            total_days = 30
        
        # Explicitly set X-axis limits with a small fixed padding (1 day) to prevent shift
        self.ax.set_xlim(mdates.date2num(min_date) - 1, mdates.date2num(max_date) + 1)
        
        # Draw non-working time shading in the background
        self._draw_non_working_time(min_date, max_date)
        
        # Plot bars
        for i, task in enumerate(display_tasks):
            y = y_pos[i]
            
            # Calculate bar dimensions
            start_num = mdates.date2num(task.start_date)
            end_num = mdates.date2num(task.end_date)
            duration = end_num - start_num
            
            # Get status color
            status_color = self.status_colors.get(task.get_status_color(), '#9E9E9E')
            
            # Different rendering for summary vs regular tasks
            if task.is_milestone:
                self._draw_milestone(y, task, task.is_critical)
            elif task.is_summary:
                start_num = mdates.date2num(task.start_date)
                end_num = mdates.date2num(task.end_date)
                duration = end_num - start_num
                status_color = self.status_colors.get(task.get_status_color(), '#9E9E9E')
                self._draw_summary_task(y, start_num, duration, status_color, task, task.is_critical)
            else:
                start_num = mdates.date2num(task.start_date)
                end_num = mdates.date2num(task.end_date)
                duration = end_num - start_num
                status_color = self.status_colors.get(task.get_status_color(), '#9E9E9E')
                self._draw_regular_task(y, start_num, duration, status_color, task, task.is_critical)
            
            # Draw progress overlay
            if task.percent_complete > 0 and not task.is_summary and not task.is_milestone:
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
                                alpha=0.7),
                        clip_on=True, zorder=10)
        
        # Draw dependency arrows AFTER all bars are drawn
        self._draw_dependencies(display_tasks, y_pos)
        
        # Format axes
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(task_labels, fontsize=9)
        
        # Set y-axis limits with some padding
        if y_pos:
            self.ax.set_ylim(min(y_pos) - 1, max(y_pos) + 1) # Add padding above and below
        self.ax.set_xlabel('Timeline', fontsize=11, weight='bold')
        self.ax.set_ylabel('Tasks', fontsize=11, weight='bold')
        self.ax.set_title('Project Gantt Chart', fontsize=13, weight='bold', pad=20)
        
        # Format x-axis dates based on current_scale
        # (min_date, max_date, total_days already calculated above)
        # Dynamic locator and formatter selection
        if self.current_scale == "Hours" and total_days < 7:
            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            self.ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        elif self.current_scale == "Days" and total_days < 90:
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            self.ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        elif self.current_scale == "Week" and total_days < 365:
            self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MONDAY))
            self.ax.xaxis.set_minor_locator(mdates.DayLocator())
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        elif self.current_scale == "Month" and total_days < 365 * 5:
            self.ax.xaxis.set_major_locator(mdates.MonthLocator())
            self.ax.xaxis.set_minor_locator(mdates.DayLocator(interval=7))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        elif self.current_scale == "Year" or total_days >= 365 * 5: # Default to year for very long projects
            self.ax.xaxis.set_major_locator(mdates.YearLocator())
            self.ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        else: # Fallback to AutoDateLocator for other cases or very large spans
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(self.ax.xaxis.get_major_locator()))

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
    
    def _draw_milestone(self, y: float, task: Task, is_critical: bool = False):
        """Draw a milestone as a star icon"""
        # Get milestone date
        milestone_date = mdates.date2num(task.end_date)
        
        # Choose color based on status
        status_color = self.status_colors.get(task.get_status_color(), constants.GANTT_MILESTONE_DEFAULT_COLOR) # Default to gold
        
        # Draw star marker
        self.ax.plot(milestone_date, y, marker='*', markersize=15, \
                     color=status_color, markeredgewidth=0, zorder=3)
        
        if is_critical:
            # Add a red circle around critical milestones
            circle = mpatches.Circle((milestone_date, y), radius=0.4, color='red', fill=False, linewidth=2, zorder=4)
            self.ax.add_patch(circle)
         
    def _get_display_order_with_levels(self, tasks: List[Task]) -> List[tuple]:
        """Get tasks and their levels in hierarchical display order (depth-first), optimized"""
        if not tasks:
            return []
            
        # Build children map once for O(1) lookups
        children_map = {}
        for task in tasks:
            pid = task.parent_id
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(task)
            
        # Pre-sort children by start date
        for pid in children_map:
            children_map[pid].sort(key=lambda t: t.start_date)
            
        display_ordered = []
        
        def add_task_and_children(task: Task, level: int):
            # Only add summary tasks if show_summary_tasks is True
            if not task.is_summary or self.show_summary_tasks:
                display_ordered.append((task, level))
            
            # Recursive depth-first traversal
            children = children_map.get(task.id, [])
            for child in children:
                add_task_and_children(child, level + 1)
        
        # Start from top-level tasks (parent_id is None)
        top_level = children_map.get(None, [])
        for task in top_level:
            add_task_and_children(task, 0)
            
        return display_ordered
    
    def _draw_regular_task(self, y: float, start_num: float, duration: int, 
                          color: str, task: Task, is_critical: bool = False):
        """Draw a regular task bar"""
        # Main task bar with border
        edge_color = constants.GANTT_REGULAR_TASK_LIGHT_EDGE_COLOR if not self.dark_mode else constants.GANTT_REGULAR_TASK_DARK_EDGE_COLOR
        linewidth = constants.GANTT_REGULAR_TASK_DEFAULT_LINEWIDTH
        
        if is_critical:
            edge_color = constants.GANTT_CRITICAL_COLOR
            linewidth = constants.GANTT_REGULAR_TASK_CRITICAL_LINEWIDTH
        
        self.ax.barh(y, duration, left=start_num, 
                    height=0.4, color=color, alpha=0.7,
                    edgecolor=edge_color,
                    linewidth=linewidth)
    
    def _draw_summary_task(self, y: float, start_num: float, duration: int, 
                          color: str, task: Task, is_critical: bool = False):
        """Draw a summary task as a single line"""
        # Draw a single horizontal line
        linewidth = constants.GANTT_SUMMARY_TASK_DEFAULT_LINEWIDTH
        line_color = color
        if is_critical:
            linewidth = constants.GANTT_SUMMARY_TASK_CRITICAL_LINEWIDTH
            line_color = constants.GANTT_CRITICAL_COLOR

        self.ax.plot([start_num, start_num + duration], [y, y], 
                     color=line_color, linewidth=linewidth, solid_capstyle='butt', zorder=2)

    
    def _draw_dependencies(self, display_tasks: List[Task], y_pos: List[int]):
        """Draw dependency arrows with type indicators, optimized lookups"""
        # Create task position and object mapping for O(1) lookups
        task_positions = {task.id: y_pos[i] for i, task in enumerate(display_tasks)}
        task_map = {task.id: task for task in display_tasks}
        
        for i, task in enumerate(display_tasks):
            if not task.predecessors:
                continue
            
            task_y = y_pos[i]
            task_start = mdates.date2num(task.start_date)
            task_end = mdates.date2num(task.end_date)
            
            for pred_id, dep_type_str, lag_days in task.predecessors:
                # Optimized lookup instead of scanning the list
                pred_task = task_map.get(pred_id)
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
        arrow_colors = constants.GANTT_DEPENDENCY_ARROW_COLORS
        
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
                        color=arrow_color, linewidth=constants.GANTT_DEPENDENCY_ARROW_LINEWIDTH, alpha=0.7, linestyle='--')
            self.ax.plot([mid_x, mid_x], [y_from, y_to], 
                        color=arrow_color, linewidth=constants.GANTT_DEPENDENCY_ARROW_LINEWIDTH, alpha=0.7, linestyle='--')
            self.ax.plot([mid_x, x_to], [y_to, y_to], 
                        color=arrow_color, linewidth=constants.GANTT_DEPENDENCY_ARROW_LINEWIDTH, alpha=0.7, linestyle='--')
            
            # Arrow head at the end
            self.ax.annotate('', xy=(x_to, y_to), xytext=(mid_x, y_to),
                           arrowprops=dict(arrowstyle='->', 
                                         color=arrow_color,
                                         lw=constants.GANTT_DEPENDENCY_ARROW_CRITICAL_LINEWIDTH,
                                         alpha=0.8))
        else:
            # Simple straight arrow for same level
            self.ax.annotate('', xy=(x_to, y_to), xytext=(x_from, y_from),
                           arrowprops=dict(arrowstyle='->', 
                                         color=arrow_color,
                                         lw=constants.GANTT_DEPENDENCY_ARROW_LINEWIDTH,
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
                    ha='center', va='center',
                    clip_on=True, zorder=10)
    
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
    
    def _draw_non_working_time(self, min_date: datetime, max_date: datetime):
        """Draw shaded backgrounds for non-working time periods, optimized by merging spans"""
        if not self.data_manager or not self.data_manager.calendar_manager:
            return
        
        calendar = self.data_manager.calendar_manager
        
        # Determine shading color based on theme
        if self.dark_mode:
            shade_color = '#1a1a1a'
            shade_alpha = 0.5
        else:
            shade_color = '#e0e0e0'
            shade_alpha = 0.3
        
        spans = []
        
        # Collect non-working spans based on scale
        if self.current_scale in ["Hours", "Days"]:
            try:
                work_start_parts = calendar.working_hours_start.split(':')
                work_end_parts = calendar.working_hours_end.split(':')
                ws_h, ws_m = int(work_start_parts[0]), int(work_start_parts[1])
                we_h, we_m = int(work_end_parts[0]), int(work_end_parts[1])
            except:
                ws_h, ws_m, we_h, we_m = 8, 0, 16, 0
            
            # Use a slightly wider range to ensure full coverage
            current_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = max_date.replace(hour=23, minute=59, second=59)
            
            while current_date <= end_date:
                if not calendar.is_working_day(current_date):
                    spans.append((mdates.date2num(current_date), 
                                 mdates.date2num(current_date + timedelta(days=1))))
                else:
                    # Before work
                    if ws_h > 0 or ws_m > 0:
                        start = current_date.replace(hour=0, minute=0, second=0)
                        end = current_date.replace(hour=ws_h, minute=ws_m, second=0)
                        spans.append((mdates.date2num(start), mdates.date2num(end)))
                    
                    # After work
                    if we_h < 24 or we_m < 59:
                        start = current_date.replace(hour=we_h, minute=we_m, second=0)
                        end = (current_date + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                        spans.append((mdates.date2num(start), mdates.date2num(end)))
                
                current_date += timedelta(days=1)
        
        elif self.current_scale in ["Week", "Month", "Year"]:
            current_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = max_date.replace(hour=23, minute=59, second=59)
            while current_date <= end_date:
                if current_date.weekday() in [5, 6]:
                    spans.append((mdates.date2num(current_date), 
                                 mdates.date2num(current_date + timedelta(days=1))))
                current_date += timedelta(days=1)

        if not spans:
            return

        # Merge consecutive spans
        spans.sort()
        merged_spans = []
        if spans:
            curr_start, curr_end = spans[0]
            for next_start, next_end in spans[1:]:
                # Use a small epsilon for floating point comparison of date numbers
                if next_start <= curr_end + 1e-9:
                    curr_end = max(curr_end, next_end)
                else:
                    merged_spans.append((curr_start, curr_end))
                    curr_start, curr_end = next_start, next_end
            merged_spans.append((curr_start, curr_end))

        # Draw merged spans
        for start, end in merged_spans:
            self.ax.axvspan(start, end, facecolor=shade_color, alpha=shade_alpha, zorder=0)

    
    def _on_scroll(self, event):
        """Handle zoom on scroll"""
        if event.inaxes != self.ax:
            return
        
        # Get current limits
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # Calculate zoom factor
        zoom_factor = constants.GANTT_ZOOM_IN_FACTOR if event.button == 'down' else constants.GANTT_ZOOM_OUT_FACTOR
        
        # Zoom X axis
        xdata = event.xdata
        new_width = (cur_xlim[1] - cur_xlim[0]) * zoom_factor
        rel_x = (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        
        new_xlim = [xdata - new_width * rel_x,
                    xdata + new_width * (1 - rel_x)]
        
        self.ax.set_xlim(new_xlim)
        
        # Dynamically adjust date formatters and locators after zoom
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(self.ax.xaxis.get_major_locator()))
        self.fig.autofmt_xdate() # Auto-format date labels to prevent overlap
        
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
        display_tasks = self.display_tasks
        y_positions = list(range(len(display_tasks)))
        y_positions.reverse()
        
        # Find closest task
        closest_task = None
        min_distance = float('inf')
        
        for i, task in enumerate(display_tasks):
            y = y_positions[i]
            distance = abs(event.ydata - y)
            
            # Determine vertical hover range based on task type
            if task.is_milestone:
                vertical_hit_range = constants.GANTT_MILESTONE_HIT_RANGE
            elif task.is_summary:
                vertical_hit_range = constants.GANTT_SUMMARY_TASK_HIT_RANGE
            else:
                vertical_hit_range = constants.GANTT_REGULAR_TASK_HIT_RANGE
            
            if abs(event.ydata - y) <= vertical_hit_range and distance < min_distance:
                # Check if x is within task range
                start_num = mdates.date2num(task.start_date)
                end_num = mdates.date2num(task.end_date)
                
                # For milestones, expand the hover area slightly
                if task.is_milestone:
                    hover_end_num = end_num + constants.GANTT_MILESTONE_HOVER_OFFSET # Give it a small width for hovering
                else:
                    hover_end_num = end_num

                if start_num <= event.xdata <= hover_end_num:
                    min_distance = distance
                    closest_task = (task, y)
        
        if closest_task:
            task, y = closest_task
            
            # Create or update annotation
            if self.annotation is None:
                self.annotation = self.ax.annotate(
                    '', xy=(0, 0), xytext=(constants.GANTT_TOOLTIP_OFFSET_X, constants.GANTT_TOOLTIP_OFFSET_Y),
                    textcoords='offset points',
                    bbox=dict(boxstyle=f'round,pad={constants.GANTT_TOOLTIP_PAD}', 
                            facecolor=constants.GANTT_TOOLTIP_LIGHT_BG_COLOR if not self.dark_mode else constants.GANTT_TOOLTIP_DARK_BG_COLOR,
                            edgecolor=constants.GANTT_TOOLTIP_EDGE_COLOR,
                            alpha=constants.GANTT_TOOLTIP_ALPHA,
                            zorder=11), # <--- Add zorder here
                    fontsize=constants.GANTT_TOOLTIP_FONT_SIZE,
                    color=self.text_color
                )
            self.annotation.set_zorder(11) # <--- Also set zorder for the annotation text
            
            # Format tooltip text
            tooltip_text = f"Task: {task.name}\n"
            tooltip_text += f"ID: {task.id}\n"
            tooltip_text += f"Start: {task.start_date.strftime('%Y-%m-%d')}\n"
            tooltip_text += f"End: {task.end_date.strftime('%Y-%m-%d')}\n"
            tooltip_text += f"Duration: {task.duration} days\n"
            if not task.is_milestone:
                tooltip_text += f"Complete: {task.percent_complete}%\n"
            tooltip_text += f"Status: {task.get_status_text()}"
            
            if task.is_summary:
                tooltip_text += "\n[Summary Task]"
            
            if task.assigned_resources:
                resource_texts = [f"{name} ({alloc}%)" for name, alloc in task.assigned_resources]
                tooltip_text += f"\nResources: {', '.join(resource_texts)}"
            
            if task.predecessors:
                pred_list = []
                for pred_id, dep_type, lag_days in task.predecessors:
                    lag_str = ""
                    if lag_days > 0:
                        lag_str = f"+{lag_days}d"
                    elif lag_days < 0:
                        lag_str = f"{lag_days}d"
                    
                    pred_list.append(f"{pred_id}{DependencyType[dep_type].name}{lag_str}")
                tooltip_text += f"\nPredecessors: {', '.join(pred_list)}"
            
            self.annotation.set_text(tooltip_text)
            self.annotation.xy = (event.xdata, y)
            self.annotation.set_visible(True)
            self.draw_idle()
        else:
            if self.annotation:
                self.annotation.set_visible(False)
                self.draw_idle()
    
    def _on_press(self, event):
        """Handle mouse button press for panning"""
        if event.inaxes != self.ax: # Only pan if click is within the axes
            return
        if event.button == 1:  # Left mouse button
            self.panning = True
            self.press_x = event.xdata
            self.press_y = event.ydata

    def _on_release(self, event):
        """Handle mouse button release"""
        self.panning = False
        self.press_x = None
        self.press_y = None

    def _on_motion(self, event):
        """Handle mouse motion for panning"""
        if self.panning and event.inaxes == self.ax:
            if event.xdata is None or event.ydata is None:
                return
            
            dx = event.xdata - self.press_x
            dy = event.ydata - self.press_y
            
            # Update x-axis limits
            cur_xlim = self.ax.get_xlim()
            new_xlim = [cur_xlim[0] - dx, cur_xlim[1] - dx]
            self.ax.set_xlim(new_xlim)
            
            # Update y-axis limits
            cur_ylim = self.ax.get_ylim()
            new_ylim = [cur_ylim[0] - dy, cur_ylim[1] - dy]
            self.ax.set_ylim(new_ylim)
            
            self.draw_idle() # Redraw the canvas efficiently

    def set_dark_mode(self, enabled: bool):
        """Toggle dark mode"""
        self.dark_mode = enabled
        if self.data_manager:
            self.update_chart(self.tasks, self.data_manager)
        else:
            self.update_chart(self.tasks)

    def set_show_summary_tasks(self, show: bool):
        """Set whether to show summary tasks and refresh the chart."""
        if self.show_summary_tasks != show:
            self.show_summary_tasks = show
            if self.data_manager and self.tasks:
                self.update_chart(self.tasks, self.data_manager)

    def set_show_critical_path(self, show: bool):
        """Set whether to show the critical path and refresh the chart."""
        if self.show_critical_path != show:
            self.show_critical_path = show
            if self.data_manager and self.tasks:
                self.update_chart(self.tasks, self.data_manager)
            elif self.tasks:
                self.update_chart(self.tasks)

    def set_axis_scale(self, scale: str):
        """Set the X-axis scale for the Gantt chart and refresh."""
        if self.current_scale != scale:
            self.current_scale = scale
            if self.data_manager and self.tasks:
                self.update_chart(self.tasks, self.data_manager)
            elif self.tasks:
                self.update_chart(self.tasks)

    def save_chart(self, file_path: str):
        """Save the Gantt chart to a file."""
        self.fig.savefig(file_path, bbox_inches='tight')
