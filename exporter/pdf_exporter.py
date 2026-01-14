
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
import os
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from ui.gantt_chart import GanttChart
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PIL import Image as PILImage
import base64
import io
import constants.constants as constants
from constants.app_images import LOGO_BASE64
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from data_manager.temp_manager import TempFileManager
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors as rl_colors

class PDFExporter:
    def __init__(self, project_data, file_path, calendar_manager):
        self.project_data = project_data
        self.file_path = file_path
        self.calendar_manager = calendar_manager
        self.styles = getSampleStyleSheet()
        # Set levels for Table of Contents
        self.styles['h1'].level = 0
        self.styles['h2'].level = 1
        self.styles['h3'].level = 2
        self.story = []
        
        self.logo_data=base64.b64decode(LOGO_BASE64)
        self.logo_img = io.BytesIO(self.logo_data)
        self.currency_symbol = self._get_safe_currency_symbol()

    def _get_safe_currency_symbol(self):
        """Returns a currency symbol that is safe for standard PDF fonts."""
        currency = self.project_data.settings.currency
        symbol = currency.symbol
        # Standard PDF fonts like Helvetica don't support many symbols like Rupee (₹).
        # Fallback to currency code for known problematic symbols in these fonts.
        problematic_codes = ['INR', 'TRY', 'RUB', 'KRW', 'AED', 'SAR']
        if currency.code in problematic_codes:
            return f"{currency.code} "
        return symbol

    def _get_base_table_style(self):
        """Returns a base TableStyle with common styling for all tables."""
        return TableStyle([
            ('GRID', (0, 0), (-1, -1), constants.PDF_TABLE_GRID_LINE_WIDTH, constants.PDF_TABLE_GRID_COLOR),
            ('FONTNAME', (0, 0), (-1, -1), constants.PDF_TABLE_FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), constants.PDF_TABLE_FONT_SIZE),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), constants.PDF_TABLE_PADDING_TOP),
            ('BOTTOMPADDING', (0, 0), (-1, -1), constants.PDF_TABLE_PADDING_BOTTOM),
        ])


    def _header(self, canvas, doc):
        canvas.saveState()
        
        #logo
        logo = Image(io.BytesIO(self.logo_data), width =0.8*inch, height=0.8*inch)
        logo.wrapOn(canvas, 0,0)
        logo.drawOn(canvas, 0.7*inch, doc.pagesize[1] - 0.9*inch)
        
        #project name(center)
        project_name = self.project_data.project_name or "Untitled Project"
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(
            doc.pagesize[0] /2,
            doc.pagesize[1] - 0.7*inch,
            project_name
        )
            
        #Page Number (right)
        page_num = f"Page {doc.page}"
        canvas.drawCentredString(
            doc.pagesize[0] - 0.7*inch,
            doc.pagesize[1] - 0.7*inch,
            page_num
        )
        
        #thin line under header
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(
            0.7*inch,
            doc.pagesize[1] - 1*inch,
            doc.pagesize[0] - 0.7*inch,
            doc.pagesize[1] - 1*inch
        )
        canvas.restoreState()
        
    def export(self):
        doc = SimpleDocTemplate(
            self.file_path, 
            pagesize=landscape(letter),
            topMargin = constants.PDF_TOP_MARGIN,
            bottomMargin = constants.PDF_BOTTOM_MARGIN,
            leftMargin = constants.PDF_LEFT_MARGIN,
            rightMargin = constants.PDF_RIGHT_MARGIN
        )
        self.temp_image_paths = [] # Initialize list to store temp image paths
        self.build_story() # Build the rest of the story
        
        doc.build(self.story, onFirstPage=lambda c, d: None, onLaterPages=self._header)
        
        # Proactive cleanup (redundant but good practice)
        for path in self.temp_image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass

    def _render_gantt_chart_to_image(self, show_critical_path: bool, filename: str) -> str:
        """Renders the Gantt chart to a temporary image file."""
        app = QApplication.instance()
        if not app:
            app = QApplication([]) # Create a QApp if one doesn't exist

        gantt_widget = GanttChart(dark_mode=False) # Assuming light mode for PDF export
        gantt_widget.data_manager = self.project_data # Assign data_manager
        gantt_widget.calendar_manager = self.calendar_manager # Assign calendar_manager
        gantt_widget.set_show_critical_path(show_critical_path)
        gantt_widget.set_show_summary_tasks(True) # Always show summary tasks in PDF for completeness

        # Update chart to ensure it's drawn
        gantt_widget.update_chart(self.project_data.get_all_tasks(), self.project_data)

        # Set a much higher resolution for better quality and detail
        render_width = constants.PDF_RENDER_WIDTH
        render_height = constants.PDF_RENDER_HEIGHT
        gantt_widget.setFixedSize(QSize(render_width, render_height))

        # Render to QPixmap
        pixmap = gantt_widget.grab()
        
        # Save to temporary file
        temp_image_path = TempFileManager.get_temp_path(suffix=".png", prefix="gantt_")
        self.temp_image_paths.append(temp_image_path)
        pixmap.save(temp_image_path, "PNG")
        
        return temp_image_path

    def add_gantt_chart(self):
        self.story.append(Paragraph("Gantt Chart (with Critical Path)", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))
        
        # Render Gantt chart with critical path
        critical_path_image_path = self._render_gantt_chart_to_image(True, "gantt_critical_path.png")
        pil_image = PILImage.open(critical_path_image_path)
        img_width, img_height = pil_image.size
        pil_image.close()

        img = Image(critical_path_image_path)
        # Use landscape width with 0.5" margins for maximum chart size
        img.drawWidth = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN
        img.drawHeight = img.drawWidth * (img_height / img_width) # Maintain aspect ratio
        self.story.append(img)
        self.story.append(Spacer(1, 0.15 * inch))
        
        self.story.append(PageBreak())
        
        self.story.append(Paragraph("Gantt Chart (without Critical Path)", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        # Render Gantt chart without critical path
        non_critical_path_image_path = self._render_gantt_chart_to_image(False, "gantt_non_critical_path.png")
        pil_image = PILImage.open(non_critical_path_image_path)
        img_width, img_height = pil_image.size
        pil_image.close()

        img = Image(non_critical_path_image_path)
        # Use landscape width with 0.5" margins for maximum chart size
        img.drawWidth = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN
        img.drawHeight = img.drawWidth * (img_height / img_width) # Maintain aspect ratio
        self.story.append(img)
        self.story.append(Spacer(1, 0.2 * inch))

        self.story.append(PageBreak())

    def build_story(self):
        self.add_title_page()
        self.add_project_details()
        self.add_task_details()
        self.add_gantt_chart()
        self.add_resource_and_cost_details()
        self.add_monthly_expense_breakdown()
        self.add_holiday_details()

    def add_holiday_details(self):
        """Add project-level holidays to the PDF report."""
        if not self.calendar_manager or not self.calendar_manager.custom_holidays:
            return

        self.story.append(Paragraph("Project Holidays", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))
        
        info_text = "The following dates are designated as project-wide non-working days."
        self.story.append(Paragraph(info_text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.1 * inch))

        # Create custom style for holiday table cells to be consistent with other tables
        holiday_cell_style = self.styles['Normal'].clone('holiday_cell_style')
        holiday_cell_style.fontSize = constants.PDF_TABLE_FONT_SIZE
        holiday_cell_style.fontName = constants.PDF_TABLE_FONT_NAME
        holiday_cell_style.leading = constants.PDF_TABLE_FONT_SIZE + 2
        holiday_cell_style.alignment = TA_LEFT

        # Holidays Table headers
        data = [["Holiday Name", "Start Date", "End Date", "Recurring", "Comment"]]
        
        for h in self.calendar_manager.custom_holidays:
            recurring_text = "Yes" if h.get('is_recurring') else "No"
            data.append([
                Paragraph(h.get('name', 'Holiday'), holiday_cell_style),
                Paragraph(h.get('start_date', ''), holiday_cell_style),
                Paragraph(h.get('end_date', ''), holiday_cell_style),
                Paragraph(recurring_text, holiday_cell_style),
                Paragraph(h.get('comment', ''), holiday_cell_style)
            ])

        # Calculate column widths
        usable_width = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN
        col_widths = [
            usable_width * 0.2,  # Name
            usable_width * 0.15, # Start
            usable_width * 0.15, # End
            usable_width * 0.1,  # Recurring
            usable_width * 0.4   # Comment
        ]

        table = Table(data, colWidths=col_widths)
        
        style = self._get_base_table_style()
        style.add('BACKGROUND', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_BG_COLOR)
        style.add('TEXTCOLOR', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        style.add('FONTNAME', (0, 0), (-1, 0), constants.PDF_TABLE_FONT_NAME_BOLD)
        style.add('ROWBACKGROUNDS', (0, 1), (-1, -1),
                  [constants.PDF_TABLE_BODY_BG_COLOR_ODD, constants.PDF_TABLE_BODY_BG_COLOR_EVEN])
        
        table.setStyle(style)
        self.story.append(table)
        self.story.append(Spacer(1, 0.2 * inch))
        self.story.append(PageBreak())

    def add_monthly_expense_breakdown(self):
        self.story.append(Paragraph("Monthly/Daily Expense Breakdown", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        breakdown_data = self.project_data.get_cost_breakdown_data()
        headers = breakdown_data['headers']
        rows = breakdown_data['rows']

        if not rows:
            self.story.append(Paragraph("No cost breakdown data available.", self.styles['Normal']))
            self.story.append(PageBreak())
            return

        if not headers:
            self.story.append(Paragraph("No breakdown headers available.", self.styles['Normal']))
            self.story.append(PageBreak())
            return

        # Sanitize symbols in rows (replace raw symbol with safe symbol)
        raw_symbol = self.project_data.settings.currency.symbol
        safe_rows = []
        for row in rows:
            safe_row = []
            for cell in row:
                cell_str = str(cell)
                if raw_symbol in cell_str:
                    cell_str = cell_str.replace(raw_symbol, self.currency_symbol)
                safe_row.append(cell_str)
            safe_rows.append(safe_row)

        # Create header style for wrapping
        header_style = self.styles['Normal'].clone('breakdown_header_style')
        header_style.textColor = constants.PDF_TABLE_HEADER_TEXT_COLOR
        header_style.alignment = TA_CENTER  # Use TA_CENTER constant instead of string
        header_style.fontName = constants.PDF_TABLE_FONT_NAME_BOLD
        header_style.fontSize = constants.PDF_TABLE_HEADER_FONT_SIZE
        
        # Wrap headers in Paragraph objects to allow word wrapping
        wrapped_headers = [Paragraph(h, header_style) for h in headers]

        # Create cell style for wrapping content
        cell_style = self.styles['Normal'].clone('cell_style')
        cell_style.alignment = TA_CENTER  # Use TA_CENTER constant instead of string
        cell_style.fontName = constants.PDF_TABLE_FONT_NAME
        cell_style.fontSize = constants.PDF_TABLE_FONT_SIZE

        # Wrap row content in Paragraph objects
        wrapped_rows = []
        for row in safe_rows:
            wrapped_row = [Paragraph(str(cell), cell_style) for cell in row]
            wrapped_rows.append(wrapped_row)

        table_data = [wrapped_headers] + wrapped_rows

        if not table_data:
            self.story.append(Paragraph("No breakdown data available to create table.", self.styles['Normal']))
            self.story.append(PageBreak())
            return

        # Calculate column widths dynamically with maximum width
        # Period column: fixed width
        # Total column: fixed width
        # Resource columns: distribute remaining width
        usable_width = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN # Use margins
        
        # Fixed width for 'Period' and 'Total' columns
        period_col_width = constants.PDF_PERIOD_COL_WIDTH
        total_col_width = constants.PDF_TOTAL_COL_WIDTH
        
        remaining_width = usable_width - period_col_width - total_col_width
        
        num_resource_cols = len(headers) - 2 # Exclude 'Period' and 'Total'
        
        if num_resource_cols > 0:
            resource_col_width = remaining_width / num_resource_cols
        else:
            resource_col_width = 0 # No resource columns

        col_widths = [period_col_width, total_col_width] + [resource_col_width] * num_resource_cols
        
        table = Table(table_data, colWidths=col_widths)
        
        style = self._get_base_table_style()
        style.add('BACKGROUND', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_BG_COLOR)
        style.add('TEXTCOLOR', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        style.add('ALIGN', (0, 0), (-1, -1), 'CENTER')
        style.add('BOTTOMPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_BOTTOM)
        style.add('TOPPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_TOP)
        style.add('ROWBACKGROUNDS', (0, 1), (-1, -1),
                  [constants.PDF_TABLE_BODY_BG_COLOR_ODD, constants.PDF_TABLE_BODY_BG_COLOR_EVEN])
        
        table.setStyle(style)
        self.story.append(table)
        self.story.append(PageBreak())

    def add_title_page(self):
        # Use a custom style for centering
        centered_style = self.styles['Normal']
        centered_style.alignment = TA_CENTER

        # Decode base64 logo and save to a temporary file
        logo_data = base64.b64decode(LOGO_BASE64)
        temp_logo_path = TempFileManager.get_temp_path(suffix=".png", prefix="logo_")
        with open(temp_logo_path, "wb") as f:
            f.write(logo_data)
        self.temp_image_paths.append(temp_logo_path)

        # Adjust width and height for better presentation
        img = Image(temp_logo_path, width=2.5*inch, height=2.5*inch)
        img.hAlign = 'CENTER'
        self.story.append(img)
        self.story.append(Spacer(1, 0.2*inch))
        
        # Add application name below logo with larger font

        app_name_style = ParagraphStyle(
            'AppName',
            parent=self.styles['Heading1'],
            fontSize=constants.PDF_FONT_SIZE_LARGE,
            leading=constants.PDF_LEADING_LARGE,
            alignment=TA_CENTER,
            textColor=constants.PDF_COLOR_PROFESSIONAL_BLUE,
            fontName=constants.PDF_FONT_HELVETICA_BOLD
        )
        self.story.append(Paragraph(constants.APP_NAME, app_name_style))
        self.story.append(Spacer(1, 0.3*inch))

        title_style = self.styles['Title']
        title_style.alignment = TA_CENTER
        self.story.append(Paragraph(str(self.project_data.project_name), title_style))
        self.story.append(Spacer(1, 0.2*inch))
        self.story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", centered_style))
        self.story.append(PageBreak())


    def add_project_details(self):
        self.story.append(Paragraph("Project Details", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))
        
        project_start = self.project_data.get_project_start_date()
        project_end = self.project_data.get_project_end_date()

        data = [
            ["Project Metric", "Value"],
            ["Project Name:", self.project_data.project_name],
            ["Start Date:", project_start.strftime('%Y-%m-%d') if project_start else "N/A"],
            ["End Date:", project_end.strftime('%Y-%m-%d') if project_end else "N/A"],
            ["Total Tasks:", str(len(self.project_data.tasks))],
            ["Overall Completion:", f"{self.project_data.get_overall_completion():.1f}%"],
            ["Currency:", self.project_data.settings.currency.name],
            ["Total Project Cost:", f"{self.currency_symbol}{sum(data.get('total_amount', 0.0) for data in self.project_data.get_resource_allocation().values()):.2f}"],
        ]

        # Use maximum width for project details table
        usable_width = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN
        table = Table(data, colWidths=[2.5*inch, usable_width - 2.5*inch])
        
        style = self._get_base_table_style()
        style.add('BACKGROUND', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_BG_COLOR)
        style.add('TEXTCOLOR', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('FONTNAME', (0, 0), (-1, 0), constants.PDF_TABLE_FONT_NAME_BOLD)
        style.add('FONTSIZE', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_FONT_SIZE)
        style.add('BOTTOMPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_BOTTOM)
        style.add('TOPPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_TOP)
        style.add('ROWBACKGROUNDS', (0, 1), (-1, -1),
                  [constants.PDF_TABLE_BODY_BG_COLOR_ODD, constants.PDF_TABLE_BODY_BG_COLOR_EVEN])
        table.setStyle(style)
        self.story.append(table)
        
        #Task Details
        self.story.append(Spacer(1, 0.2 * inch))

        # Task Status Breakdown
        self.story.append(Paragraph("Task Status Breakdown:", self.styles['h3']))
        status_counts = {"Overdue": 0, "In Progress": 0, "Upcoming": 0, "Completed": 0}
        for task in self.project_data.tasks:
            if not task.is_summary:
                status_counts[task.get_status_text()] += 1
        
        status_data = [["Status", "Count"]]
        for status, count in status_counts.items():
            status_data.append([status, str(count)])
        
        status_table = Table(status_data)
        
        status_style = self._get_base_table_style()
        status_style.add('BACKGROUND', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_BG_COLOR)
        status_style.add('TEXTCOLOR', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        status_style.add('ALIGN', (0, 0), (-1, -1), 'CENTER')
        status_style.add('FONTNAME', (0, 0), (-1, 0), constants.PDF_TABLE_FONT_NAME_BOLD)
        status_style.add('FONTSIZE', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_FONT_SIZE)
        status_style.add('BOTTOMPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_BOTTOM)
        status_style.add('TOPPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_TOP)
        status_style.add('ROWBACKGROUNDS', (0, 1), (-1, -1),
                         [constants.PDF_TABLE_BODY_BG_COLOR_ODD, constants.PDF_TABLE_BODY_BG_COLOR_EVEN])
        status_table.setStyle(status_style)
        self.story.append(status_table)
        self.story.append(Spacer(1, 0.2 * inch))

        self.story.append(PageBreak())
        

    def add_task_details(self):
       
        self.story.append(Paragraph("Task Details", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        if not self.project_data.tasks:
            self.story.append(Paragraph("No tasks defined.", self.styles['Normal']))
            self.story.append(PageBreak())
            return

        # Create custom styles
        task_style = self.styles['Normal'].clone('task_style')
        task_style.fontSize = constants.PDF_TABLE_FONT_SIZE
        task_style.leading = constants.PDF_LEADING_SMALL
        task_style.fontName = constants.PDF_TABLE_FONT_NAME
        task_style.alignment = TA_LEFT  # Explicitly set alignment
        
        header_style = self.styles['Normal'].clone('header_style')
        header_style.fontSize = constants.PDF_TABLE_HEADER_FONT_SIZE
        header_style.leading = constants.PDF_LEADING_MEDIUM
        header_style.textColor = constants.PDF_TABLE_HEADER_TEXT_COLOR
        header_style.alignment = TA_CENTER
        header_style.fontName = constants.PDF_TABLE_FONT_NAME_BOLD
        
        # Create headers with Paragraph objects for wrapping
        headers = [
            Paragraph("<b>ID</b>", header_style),
            Paragraph("<b>WBS</b>", header_style),
            Paragraph("<b>Task Name</b>", header_style),
            Paragraph("<b>Duration</b>", header_style),
            Paragraph("<b>Start Date</b>", header_style),
            Paragraph("<b>End Date</b>", header_style),
            Paragraph("<b>Dependencies</b>", header_style),
            Paragraph("<b>Resources</b>", header_style),
            Paragraph("<b>%</b>", header_style),
            Paragraph("<b>Status</b>", header_style),
            Paragraph("<b>Notes</b>", header_style),
        ]
        
        table_data = [headers]
        task_bg_colors = []  # Store background colors for each task row

        # Helper function to flatten tasks with indentation
        def flatten_tasks(task_list, level=0):
            for task in task_list:
                indent = "&nbsp;" * level
                display_name = f"{indent}{task.name}"
                
                # Map custom font families to ReportLab's built-in fonts
                font_family = getattr(task, 'font_family', 'Arial')
                is_bold = getattr(task, 'font_bold', False)
                is_italic = getattr(task, 'font_italic', False)
                is_underline = getattr(task, 'font_underline', False)
                
                # Map to ReportLab font names
                font_map = {
                    'Arial': 'Helvetica',
                    'Helvetica': 'Helvetica',
                    'Times New Roman': 'Times-Roman',
                    'Times': 'Times-Roman',
                    'Courier New': 'Courier',
                    'Courier': 'Courier'
                }
                
                base_font = font_map.get(font_family, 'Helvetica')
                
                # Construct font name with bold/italic modifiers
                if is_bold and is_italic:
                    if base_font == 'Helvetica':
                        font_name = 'Helvetica-BoldOblique'
                    elif base_font == 'Times-Roman':
                        font_name = 'Times-BoldItalic'
                    elif base_font == 'Courier':
                        font_name = 'Courier-BoldOblique'
                    else:
                        font_name = 'Helvetica-BoldOblique'
                elif is_bold:
                    if base_font == 'Helvetica':
                        font_name = 'Helvetica-Bold'
                    elif base_font == 'Times-Roman':
                        font_name = 'Times-Bold'
                    elif base_font == 'Courier':
                        font_name = 'Courier-Bold'
                    else:
                        font_name = 'Helvetica-Bold'
                elif is_italic:
                    if base_font == 'Helvetica':
                        font_name = 'Helvetica-Oblique'
                    elif base_font == 'Times-Roman':
                        font_name = 'Times-Italic'
                    elif base_font == 'Courier':
                        font_name = 'Courier-Oblique'
                    else:
                        font_name = 'Helvetica-Oblique'
                else:
                    font_name = base_font
                
                # Use standard report font size for consistency across all tables
                task_font_size = constants.PDF_TABLE_FONT_SIZE

                # Create custom styles for this specific task
                custom_task_style_left = ParagraphStyle(
                    f'task_style_left_{task.id}',
                    parent=task_style,
                    fontName=font_name,
                    fontSize=task_font_size,
                    leading=task_font_size + 2,
                    textColor=rl_colors.HexColor(getattr(task, 'font_color', '#000000')),
                    alignment=TA_LEFT
                )
                custom_task_style_center = ParagraphStyle(
                    f'task_style_center_{task.id}',
                    parent=task_style,
                    fontName=font_name,
                    fontSize=task_font_size,
                    leading=task_font_size + 2,
                    textColor=rl_colors.HexColor(getattr(task, 'font_color', '#000000')),
                    alignment=TA_CENTER
                )
                
                # Apply underline using HTML tag if needed
                if is_underline:
                    formatted_display_name = f"<u>{display_name}</u>"
                else:
                    formatted_display_name = display_name
                
                # Wrap task name in Paragraph with custom style
                task_name_para = Paragraph(formatted_display_name, custom_task_style_left)
                
                # Store background color for this task
                bg_color = getattr(task, 'background_color', '#FFFFFF')
                task_bg_colors.append(bg_color)
                
                # Format duration
                duration = task.get_duration(
                    self.project_data.settings.duration_unit, 
                    self.calendar_manager
                )
                duration_unit = self.project_data.settings.duration_unit.value
                duration_text = f"{duration:.1f} {duration_unit}" if duration > 0 else "0 days"
                
                # Format dependencies
                deps_list = []
                for pred_id, dep_type, lag in task.predecessors:
                    lag_str = f"+{lag}d" if lag > 0 else (f"{lag}d" if lag < 0 else "")
                    deps_list.append(f"{pred_id}{dep_type}{lag_str}")
                dependencies = Paragraph(", ".join(deps_list) if deps_list else "-", custom_task_style_left)
                
                # Format resources
                res_list = []
                for res_name, allocation in task.assigned_resources:
                    res_list.append(f"{res_name} ({allocation}%)")
                resources = Paragraph(", ".join(res_list) if res_list else "-", custom_task_style_left)
                
                # Status
                status_text = Paragraph(task.get_status_text(), custom_task_style_center)
                
                # Format notes with word wrapping
                notes_text = task.notes if task.notes else "-"
                notes_para = Paragraph(notes_text, custom_task_style_left)

                table_data.append([
                    Paragraph(str(task.id), custom_task_style_center),
                    Paragraph(task.wbs if task.wbs else "", custom_task_style_center),
                    task_name_para,
                    Paragraph(duration_text, custom_task_style_center),
                    Paragraph(task.start_date.strftime('%Y-%m-%d'), custom_task_style_center),
                    Paragraph(task.end_date.strftime('%Y-%m-%d'), custom_task_style_center),
                    dependencies,
                    resources,
                    Paragraph(f"{task.percent_complete}%", custom_task_style_center),
                    status_text,
                    notes_para
                ])
                
                children = self.project_data.get_child_tasks(task.id)
                if children:
                    flatten_tasks(children, level + 1)

        top_level_tasks = self.project_data.get_top_level_tasks()
        flatten_tasks(top_level_tasks)

        # Calculate column widths dynamically - use maximum width with margins
        # Landscape letter is 11\" tall x 8.5\" wide, so landscape(letter)[0] = 11 inches
        usable_width = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN
        
        # Define fixed column widths
        id_width = 0.35*inch
        wbs_width = 0.5*inch
        duration_width = 0.65*inch
        start_date_width = 0.85*inch
        end_date_width = 0.85*inch
        percent_width = 0.5*inch
        status_width = 0.8*inch
        
        # Calculate total fixed width
        fixed_width = id_width + wbs_width + duration_width + start_date_width + end_date_width + percent_width + status_width
        
        # Remaining width for flexible columns (Task Name, Dependencies, Resources, Notes)
        remaining_width = usable_width - fixed_width
        
        col_widths = [
            id_width,                       # ID
            wbs_width,                      # WBS
            remaining_width * 0.25,         # Task Name (25% of remaining)
            duration_width,                 # Duration
            start_date_width,               # Start Date
            end_date_width,                 # End Date
            remaining_width * 0.25,         # Dependencies (25% of remaining)
            remaining_width * 0.2,          # Resources (20% of remaining)
            percent_width,                  # % Complete
            status_width,                   # Status
            remaining_width * 0.3,          # Notes (30% of remaining)
        ]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        
        style = self._get_base_table_style()
        # Header styling
        style.add('BACKGROUND', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_BG_COLOR)
        style.add('TEXTCOLOR', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        style.add('FONTNAME', (0, 0), (-1, 0), constants.PDF_TABLE_FONT_NAME_BOLD)
        style.add('FONTSIZE', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_FONT_SIZE)
        style.add('BOTTOMPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_BOTTOM)
        style.add('TOPPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_TOP)
        
        # Data rows styling
        style.add('ALIGN', (0, 1), (1, -1), 'CENTER')  # Center ID and WBS
        style.add('ALIGN', (3, 1), (5, -1), 'CENTER')  # Center Duration and Dates
        style.add('ALIGN', (8, 1), (9, -1), 'CENTER')  # Center % and Status
        style.add('ALIGN', (2, 1), (2, -1), 'LEFT')   # Task Name
        style.add('ALIGN', (6, 1), (6, -1), 'LEFT')   # Predecessor
        style.add('ALIGN', (7, 1), (7, -1), 'LEFT')   # Resource
        style.add('ALIGN', (10, 1), (10, -1), 'LEFT')  # Notes
        style.add('VALIGN', (10, 1), (10, -1), 'TOP')  # Notes align to top for better readability
        
        # Row backgrounds - alternating colors
        style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), 
                 [constants.PDF_TABLE_BODY_BG_COLOR_ODD, constants.PDF_TABLE_BODY_BG_COLOR_EVEN])
        
        # Apply custom background colors to task name cells
        for idx, bg_color in enumerate(task_bg_colors):
            if bg_color and bg_color != '#FFFFFF':  # Only apply if not default white
                row_idx = idx + 1  # +1 because row 0 is the header
                try:
                    hex_color = rl_colors.HexColor(bg_color)
                    style.add('BACKGROUND', (2, row_idx), (2, row_idx), hex_color)
                except:
                    pass  # Skip if color is invalid
        
        table.setStyle(style)
        
        self.story.append(table)
        self.story.append(PageBreak())

    def add_resource_and_cost_details(self):
        self.story.append(Paragraph("Resource and Cost Details", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        if not self.project_data.resources:
            self.story.append(Paragraph("No resources defined.", self.styles['Normal']))
            self.story.append(PageBreak())
            return

        # Create custom style for resource names with proper wrapping
        resource_style = self.styles['Normal'].clone('resource_style')
        resource_style.fontSize = constants.PDF_TABLE_FONT_SIZE
        resource_style.leading = constants.PDF_LEADING_MEDIUM
        resource_style.fontName = constants.PDF_TABLE_FONT_NAME
        resource_style.alignment = TA_LEFT  # Explicitly set alignment
        
        allocation = self.project_data.get_resource_allocation()
        total_project_cost = sum(data.get('total_amount', 0.0) for data in allocation.values())

        symbol = self.currency_symbol
        data = [[f"Resource Name", "Max Hours/Day", f"Billing Rate ({symbol})", "Total Hours Allocated", f"Total Cost ({symbol})"]]
        for resource in self.project_data.resources:
            resource_name = resource.name
            details = allocation.get(resource_name, {})
            
            # Wrap resource name in Paragraph for text wrapping
            resource_name_para = Paragraph(resource_name, resource_style)
            
            symbol = self.currency_symbol
            data.append([
                resource_name_para,
                str(resource.max_hours_per_day),
                f"{symbol}{resource.billing_rate:.2f}",
                f"{details.get('total_hours', 0.0):.1f} hours",
                f"{symbol}{details.get('total_amount', 0.0):.2f}"
            ])
        
        # Add total row
        symbol = self.currency_symbol
        total_label = Paragraph("<b>Total Project Cost:</b>", resource_style)
        data.append(["", "", "", total_label, f"{symbol}{total_project_cost:.2f}"])

        # Calculate column widths dynamically - use maximum width
        usable_width = landscape(letter)[0] - constants.PDF_LEFT_MARGIN - constants.PDF_RIGHT_MARGIN
        col_widths = [
            usable_width * 0.3,  # Resource Name - 30%
            usable_width * 0.15, # Max Hours/Day - 15%
            usable_width * 0.15, # Billing Rate - 15%
            usable_width * 0.2,  # Total Hours - 20%
            usable_width * 0.2   # Total Cost - 20%
        ]
        
        table = Table(data, colWidths=col_widths)
        
        style = self._get_base_table_style()
        style.add('BACKGROUND', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_BG_COLOR)  # Green header
        style.add('TEXTCOLOR', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        style.add('ALIGN', (0, 0), (-1, 0), 'CENTER')
        style.add('FONTNAME', (0, 0), (-1, 0), constants.PDF_TABLE_FONT_NAME_BOLD)
        style.add('FONTSIZE', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_FONT_SIZE)
        style.add('BOTTOMPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_BOTTOM)
        style.add('TOPPADDING', (0, 0), (-1, 0), constants.PDF_TABLE_HEADER_PADDING_TOP)

        # Row alignment rules
        style.add('ALIGN', (0, 1), (0, -1), 'LEFT')   # Resource name stays left
        style.add('ALIGN', (1, 1), (-1, -1), 'CENTER')

        style.add('ROWBACKGROUNDS', (0, 1), (-1, -2),
                 [constants.PDF_TABLE_BODY_BG_COLOR_ODD, constants.PDF_TABLE_BODY_BG_COLOR_EVEN])

        # Total row styling
        style.add('BACKGROUND', (0, -1), (-1, -1), constants.PDF_TABLE_HEADER_BG_COLOR)
        style.add('TEXTCOLOR', (0, -1), (-1, -1), constants.PDF_TABLE_HEADER_TEXT_COLOR)
        style.add('FONTNAME', (0, -1), (-1, -1), constants.PDF_TABLE_FONT_NAME_BOLD)
        style.add('FONTSIZE', (0, -1), (-1, -1), constants.PDF_TABLE_HEADER_FONT_SIZE)

        table.setStyle(style)
        self.story.append(table)
        self.story.append(PageBreak())
