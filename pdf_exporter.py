
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
import os
from datetime import datetime
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from datetime import datetime
from gantt_chart import GanttChart

from reportlab.lib.pagesizes import letter, landscape

# Import PyQt6 for Gantt chart rendering
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize, Qt

# Import PIL for image dimension retrieval
from PIL import Image as PILImage

import base64
import io

# Base64 encoded logo.ico
from app_images import LOGO_BASE64

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

    def export(self):
        doc = SimpleDocTemplate(self.file_path, pagesize=landscape(letter))
        self.temp_image_paths = [] # Initialize list to store temp image paths
        


        self.build_story() # Build the rest of the story



        doc.build(self.story)
        
        # Clean up temporary image files after PDF is built
        for path in self.temp_image_paths:
            if os.path.exists(path):
                os.remove(path)

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
        render_width = 2400
        render_height = 1200
        gantt_widget.setFixedSize(QSize(render_width, render_height))

        # Render to QPixmap
        pixmap = gantt_widget.grab()
        
        # Save to temporary file
        temp_image_path = os.path.join(os.path.dirname(self.file_path), filename)
        self.temp_image_paths.append(temp_image_path) # Store path for later cleanup
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
        img.drawWidth = landscape(letter)[0] - 1*inch
        img.drawHeight = img.drawWidth * (img_height / img_width) # Maintain aspect ratio
        self.story.append(img)
        self.story.append(Spacer(1, 0.15 * inch))

        self.story.append(Paragraph("Gantt Chart (without Critical Path)", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        # Render Gantt chart without critical path
        non_critical_path_image_path = self._render_gantt_chart_to_image(False, "gantt_non_critical_path.png")
        pil_image = PILImage.open(non_critical_path_image_path)
        img_width, img_height = pil_image.size
        pil_image.close()

        img = Image(non_critical_path_image_path)
        # Use landscape width with 0.5" margins for maximum chart size
        img.drawWidth = landscape(letter)[0] - 1*inch
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
        self.add_current_status()

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

        # Create header style for wrapping
        header_style = self.styles['Normal'].clone('header_style')
        header_style.textColor = colors.whitesmoke
        header_style.alignment = 1 # CENTER
        header_style.fontName = 'Helvetica-Bold'
        
        # Wrap headers in Paragraph objects to allow word wrapping
        wrapped_headers = [Paragraph(h, header_style) for h in headers]

        # Create cell style for wrapping content
        cell_style = self.styles['Normal'].clone('cell_style')
        cell_style.alignment = 1 # CENTER

        # Wrap row content in Paragraph objects
        wrapped_rows = []
        for row in rows:
            wrapped_row = [Paragraph(str(cell), cell_style) for cell in row]
            wrapped_rows.append(wrapped_row)

        table_data = [wrapped_headers] + wrapped_rows

        # Calculate column widths dynamically with maximum width
        # Period column: fixed width
        # Total column: fixed width
        # Resource columns: distribute remaining width
        usable_width = landscape(letter)[0] - 1 * inch # Use 0.5" margins
        
        # Fixed width for 'Period' and 'Total' columns
        period_col_width = 1.0 * inch # Slightly reduced
        total_col_width = 0.8 * inch  # Slightly reduced
        
        remaining_width = usable_width - period_col_width - total_col_width
        
        num_resource_cols = len(headers) - 2 # Exclude 'Period' and 'Total'
        
        if num_resource_cols > 0:
            resource_col_width = remaining_width / num_resource_cols
        else:
            resource_col_width = 0 # No resource columns

        col_widths = [period_col_width, total_col_width] + [resource_col_width] * num_resource_cols
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')), # Green header
            # TEXTCOLOR for headers is handled by Paragraph style
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            # FONTNAME for headers is handled by Paragraph style
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E9')), # Light green rows
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        self.story.append(table)
        self.story.append(PageBreak())

    def add_title_page(self):
        # Use a custom style for centering
        centered_style = self.styles['Normal']
        centered_style.alignment = 1 # TA_CENTER

        # Decode base64 logo and save to a temporary file
        logo_data = base64.b64decode(LOGO_BASE64)
        temp_logo_path = os.path.join(os.path.dirname(self.file_path), "temp_logo.ico")
        with open(temp_logo_path, "wb") as f:
            f.write(logo_data)
        self.temp_image_paths.append(temp_logo_path) # Add to cleanup list

        # Adjust width and height for better presentation
        img = Image(temp_logo_path, width=2.5*inch, height=2.5*inch)
        img.hAlign = 'CENTER'
        self.story.append(img)
        self.story.append(Spacer(1, 0.2*inch))

        self.story.append(Spacer(1, 0.5*inch))
        title_style = self.styles['Title']
        title_style.alignment = 1 # TA_CENTER
        self.story.append(Paragraph(self.project_data.project_name, title_style))
        self.story.append(Spacer(1, 0.2*inch))
        self.story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", centered_style))
        self.story.append(PageBreak())


    def add_project_details(self):
        self.story.append(Paragraph("Project Details", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))
        
        project_start = self.project_data.get_project_start_date()
        project_end = self.project_data.get_project_end_date()

        data = [
            ["Metric", "Value"],
            ["Project Name:", self.project_data.project_name],
            ["Start Date:", project_start.strftime('%Y-%m-%d') if project_start else "N/A"],
            ["End Date:", project_end.strftime('%Y-%m-%d') if project_end else "N/A"],
            ["Total Tasks:", str(len(self.project_data.tasks))],
            ["Overall Completion:", f"{self.project_data.get_overall_completion():.1f}%"],
        ]

        # Use maximum width for project details table
        usable_width = landscape(letter)[0] - 1*inch
        table = Table(data, colWidths=[2.5*inch, usable_width - 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        self.story.append(table)
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
        task_style.fontSize = 8
        task_style.leading = 10
        
        header_style = self.styles['Normal'].clone('header_style')
        header_style.fontSize = 9
        header_style.leading = 11
        header_style.textColor = colors.whitesmoke
        header_style.alignment = 1  # Center
        
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
        ]
        
        table_data = [headers]

        # Helper function to flatten tasks with indentation
        def flatten_tasks(task_list, level=0):
            for task in task_list:
                indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level
                display_name = f"{indent}{task.name}"
                
                # Wrap task name in Paragraph
                task_name_para = Paragraph(display_name, task_style)
                
                # Format duration
                duration = task.get_duration(
                    self.project_data.settings.duration_unit, 
                    self.calendar_manager
                )
                duration_unit = self.project_data.settings.duration_unit.value
                duration_text = f"{duration:.1f} {duration_unit}" if duration > 0 else "0"
                
                # Format dependencies
                deps_list = []
                for pred_id, dep_type, lag in task.predecessors:
                    lag_str = f"+{lag}d" if lag > 0 else (f"{lag}d" if lag < 0 else "")
                    deps_list.append(f"{pred_id}{dep_type}{lag_str}")
                dependencies = Paragraph(", ".join(deps_list) if deps_list else "-", task_style)
                
                # Format resources
                res_list = []
                for res_name, allocation in task.assigned_resources:
                    res_list.append(f"{res_name} ({allocation}%)")
                resources = Paragraph(", ".join(res_list) if res_list else "-", task_style)
                
                # Status
                status_text = task.get_status_text()

                table_data.append([
                    str(task.id),
                    task.wbs if task.wbs else "",
                    task_name_para,
                    duration_text,
                    task.start_date.strftime('%Y-%m-%d'),
                    task.end_date.strftime('%Y-%m-%d'),
                    dependencies,
                    resources,
                    f"{task.percent_complete}%",
                    status_text
                ])
                
                children = self.project_data.get_child_tasks(task.id)
                if children:
                    flatten_tasks(children, level + 1)

        top_level_tasks = self.project_data.get_top_level_tasks()
        flatten_tasks(top_level_tasks)

        # Calculate column widths dynamically - use smaller margins for task table
        # Landscape letter is 11" tall x 8.5" wide, so landscape(letter)[0] = 11 inches
        # Use 0.25 inch margins on each side for maximum table width
        usable_width = landscape(letter)[0] - 0.5 * inch  # 10 inches total width
        
        col_widths = [
            0.35*inch,                          # ID
            0.5*inch,                           # WBS
            (usable_width - 6.3*inch) * 0.35,   # Task Name (35% of remaining)
            0.65*inch,                          # Duration
            0.85*inch,                          # Start Date
            0.85*inch,                          # End Date
            (usable_width - 6.3*inch) * 0.35,   # Dependencies (35% of remaining)
            (usable_width - 6.3*inch) * 0.3,    # Resources (30% of remaining)
            0.5*inch,                           # % Complete
            0.6*inch,                           # Status
        ]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Data rows styling
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # Center ID and WBS
            ('ALIGN', (3, 1), (5, -1), 'CENTER'),  # Center Duration and Dates
            ('ALIGN', (8, 1), (9, -1), 'CENTER'),  # Center % and Status
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            
            # Row backgrounds - alternating colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.HexColor('#E3F2FD'), colors.HexColor('#BBDEFB')]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90CAF9')),
            
            # Font size for data
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        self.story.append(table)
        self.story.append(PageBreak())

    def add_current_status(self):
        self.story.append(Paragraph("Current Status", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        # Overall Completion
        overall_completion = self.project_data.get_overall_completion()
        self.story.append(Paragraph(f"Overall Project Completion: <b>{overall_completion:.1f}%</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1 * inch))

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
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC107')), # Amber header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF8E1')), # Light amber rows
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        self.story.append(status_table)
        self.story.append(Spacer(1, 0.2 * inch))

        self.story.append(PageBreak())



    def add_resource_and_cost_details(self):
        self.story.append(Paragraph("Resource and Cost Details", self.styles['h2']))
        self.story.append(Spacer(1, 0.1 * inch))

        if not self.project_data.resources:
            self.story.append(Paragraph("No resources defined.", self.styles['Normal']))
            self.story.append(PageBreak())
            return

        # Create custom style for resource names with proper wrapping
        resource_style = self.styles['Normal']
        resource_style.fontSize = 9
        resource_style.leading = 11
        
        allocation = self.project_data.get_resource_allocation()
        total_project_cost = sum(data.get('total_amount', 0.0) for data in allocation.values())

        data = [["Resource Name", "Max Hours/Day", "Billing Rate", "Total Hours Allocated", "Total Cost"]]
        for resource in self.project_data.resources:
            resource_name = resource.name
            details = allocation.get(resource_name, {})
            
            # Wrap resource name in Paragraph for text wrapping
            resource_name_para = Paragraph(resource_name, resource_style)
            
            data.append([
                resource_name_para,
                str(resource.max_hours_per_day),
                f"${resource.billing_rate:.2f}",
                f"{details.get('total_hours', 0.0):.1f} hours",
                f"${details.get('total_amount', 0.0):.2f}"
            ])
        
        # Add total row
        total_label = Paragraph("<b>Total Project Cost:</b>", resource_style)
        data.append(["", "", "", total_label, f"<b>${total_project_cost:.2f}</b>"])

        # Calculate column widths dynamically - use maximum width
        usable_width = landscape(letter)[0] - 1 * inch  # 0.5\" margins
        col_widths = [
            usable_width * 0.3,  # Resource Name - 30%
            usable_width * 0.15, # Max Hours/Day - 15%
            usable_width * 0.15, # Billing Rate - 15%
            usable_width * 0.2,  # Total Hours - 20%
            usable_width * 0.2   # Total Cost - 20%
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),  # Material Green header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center all except resource name
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#E8F5E9')),  # Light green rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor('#E8F5E9'), colors.HexColor('#C8E6C9')]),  # Alternating rows
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#81C784')),  # Lighter grid lines
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#66BB6A')),  # Green for total row
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('WORDWRAP', (0, 1), (0, -1), 'LTR'),  # Enable word wrap for resource names
        ]))
        self.story.append(table)
        self.story.append(PageBreak())
