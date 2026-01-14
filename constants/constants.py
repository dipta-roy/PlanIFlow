"""
Project-wide constants.
"""

from data_manager.models import DependencyType
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- General Application Constants ---
APP_NAME = "PlanIFlow"
VERSION = "2.4.0"
AUTHOR = "Dipta Roy"
ABOUT_TEXT = "PlanIFlow is a project planning and management tool designed to help you organize tasks, resources, and schedules effectively."

# --- Auto-Update Constants ---
REPO_OWNER = "dipta-roy"
REPO_NAME = "PlanIFlow"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"


# --- UI General Constants ---
ICON_SIZE = 14 # Default icon size for certain UI elements

# --- UI Specific Constants (e.g., Task Tree, Status Filters) ---
CIRCLE_SIZE = 10
LEFT_PADDING = 8
TEXT_SHIFT = 15

STATUS_ALL = "All"
STATUS_OVERDUE = "Overdue"
STATUS_IN_PROGRESS = "In Progress"
STATUS_UPCOMING = "Upcoming"
STATUS_COMPLETED = "Completed"

# --- Gantt Chart Constants ---
GANTT_STATUS_COLORS = {
    'red': '#F44336',      # Overdue
    'green': '#4CAF50',    # In Progress
    'grey': '#9E9E9E',     # Upcoming
    'blue': '#2196F3'      # Completed
}
GANTT_MILESTONE_DEFAULT_COLOR = '#FFD700' # Gold color for milestones

GANTT_DEPENDENCY_ARROW_COLORS = {
    DependencyType.FS: '#D32F2F',  # Red
    DependencyType.SS: '#1976D2',  # Blue
    DependencyType.FF: '#388E3C',  # Green
    DependencyType.SF: '#F57C00'   # Orange
}

GANTT_REGULAR_TASK_DEFAULT_LINEWIDTH = 1.0
GANTT_REGULAR_TASK_CRITICAL_LINEWIDTH = 2.5
GANTT_REGULAR_TASK_LIGHT_EDGE_COLOR = 'black'
GANTT_REGULAR_TASK_DARK_EDGE_COLOR = 'white'
GANTT_CRITICAL_COLOR = 'red' # Universal color for critical path elements

GANTT_SUMMARY_TASK_DEFAULT_LINEWIDTH = 4
GANTT_SUMMARY_TASK_CRITICAL_LINEWIDTH = 6

GANTT_DEPENDENCY_ARROW_LINEWIDTH = 1.5
GANTT_DEPENDENCY_ARROW_CRITICAL_LINEWIDTH = 2.0 # For arrow head or critical dependencies

GANTT_ZOOM_IN_FACTOR = 1.1
GANTT_ZOOM_OUT_FACTOR = 0.9

# Gantt Chart Hover/Tooltip Constants
GANTT_MILESTONE_HIT_RANGE = 0.5
GANTT_SUMMARY_TASK_HIT_RANGE = 0.3
GANTT_REGULAR_TASK_HIT_RANGE = 0.2
GANTT_MILESTONE_HOVER_OFFSET = 0.5

GANTT_TOOLTIP_OFFSET_X = 20
GANTT_TOOLTIP_OFFSET_Y = 20
GANTT_TOOLTIP_PAD = 0.5
GANTT_TOOLTIP_LIGHT_BG_COLOR = 'yellow'
GANTT_TOOLTIP_DARK_BG_COLOR = '#444444'
GANTT_TOOLTIP_EDGE_COLOR = 'black'
GANTT_TOOLTIP_ALPHA = 0.95
GANTT_TOOLTIP_FONT_SIZE = 9

# --- PDF Exporter Layout Constants ---
PDF_RENDER_WIDTH = 2400  # Resolution for rendering Gantt chart images for PDF
PDF_RENDER_HEIGHT = 1200

# Margins for PDF document
PDF_TOP_MARGIN = 1.0 * inch
PDF_BOTTOM_MARGIN = 0.1 * inch
PDF_LEFT_MARGIN = 0.1 * inch
PDF_RIGHT_MARGIN = 0.1 * inch

# Column widths for specific tables in PDF
PDF_PERIOD_COL_WIDTH = 1.0 * inch
PDF_TOTAL_COL_WIDTH = 0.8 * inch

# --- PDF Exporter Style Constants ---
PDF_FONT_SIZE_SMALL = 8
PDF_FONT_SIZE_MEDIUM = 9
PDF_FONT_SIZE_LARGE = 20
PDF_LEADING_SMALL = 10
PDF_LEADING_MEDIUM = 11
PDF_LEADING_LARGE = 24

PDF_COLOR_WHITESMOKE = colors.whitesmoke
PDF_COLOR_BLACK = colors.black
PDF_COLOR_PROFESSIONAL_BLUE = colors.HexColor('#2E86AB')
PDF_FONT_HELVETICA_BOLD = 'Helvetica-Bold'

# --- PDF Exporter Table Style Constants ---
PDF_TABLE_HEADER_BG_COLOR = colors.HexColor('#1976D2') # Dark Blue
PDF_TABLE_HEADER_TEXT_COLOR = colors.whitesmoke
PDF_TABLE_BODY_BG_COLOR_ODD = colors.HexColor('#E3F2FD') # Light Blue
PDF_TABLE_BODY_BG_COLOR_EVEN = colors.HexColor('#BBDEFB') # Slightly darker Light Blue
PDF_TABLE_GRID_COLOR = colors.HexColor('#90CAF9') # Light Blue Grid
PDF_TABLE_GRID_LINE_WIDTH = 0.5
PDF_TABLE_FONT_NAME = 'Helvetica'
PDF_TABLE_FONT_NAME_BOLD = 'Helvetica-Bold'
PDF_TABLE_FONT_SIZE = 9
PDF_TABLE_HEADER_FONT_SIZE = 10
PDF_TABLE_PADDING_TOP = 4
PDF_TABLE_PADDING_BOTTOM = 4
PDF_TABLE_HEADER_PADDING_TOP = 6
PDF_TABLE_HEADER_PADDING_BOTTOM = 6
PDF_ALIGN_LEFT = 0 # Constant for alignment (TA_LEFT)

# --- Error Handling Constants ---
ERROR_TITLE = "Application Error"
ERROR_GENERIC_MESSAGE = "An unexpected error occurred. The application will continue to run, but some functionality may be affected."
ERROR_FILE_OPERATION_FAILED = "File operation failed. Please check the file path and permissions."
ERROR_SAVE_FAILED = "Failed to save the project. Please try again."
ERROR_LOAD_FAILED = "Failed to load the project. The file might be corrupted or in an incompatible format."