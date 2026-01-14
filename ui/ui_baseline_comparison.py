"""
Baseline Comparison Tab - Compare current project state against baselines
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QTreeWidget, QTreeWidgetItem, QPushButton,
                             QGroupBox, QFormLayout, QMessageBox, QFileDialog, 
                             QStyledItemDelegate, QStyleOptionViewItem, QStyle)
from PyQt6.QtGui import QColor, QBrush, QPainter
from PyQt6.QtCore import Qt, QModelIndex

import pandas as pd

class BaselineStatusDelegate(QStyledItemDelegate):
    """Delegate to draw status indicator circle"""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # Draw background
        painter.fillRect(option.rect, option.palette.base())
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            # Respect row background color if set
            bg_brush = index.data(Qt.ItemDataRole.BackgroundRole)
            if bg_brush and bg_brush != QBrush():
                 painter.fillRect(option.rect, bg_brush)
        
        status = index.data(Qt.ItemDataRole.UserRole)
        if not status:
            return
            
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Color mapping
        color_map = {
            'late': QColor(244, 67, 54),     # Red
            'early': QColor(76, 175, 80),    # Green
            'on-track': QColor(33, 150, 243), # Blue
            'new': QColor(156, 39, 176),     # Purple
            'deleted': QColor(158, 158, 158) # Grey
        }
        
        color = color_map.get(status, QColor(128, 128, 128))
        
        # Draw circle centered
        size = 12
        rect = option.rect
        x = rect.x() + (rect.width() - size) // 2
        y = rect.y() + (rect.height() - size) // 2
        
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x, y, size, size)
        
        painter.restore()

class BaselineComparisonTab(QWidget):
    """Tab for comparing current project against baselines"""
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_comparison = None
        
        self._create_ui()
        self.refresh_baselines()
    
    def showEvent(self, event):
        """Refresh baselines when tab becomes visible"""
        super().showEvent(event)
        self.refresh_baselines()
    
    def _create_ui(self):
        """Create the comparison tab UI"""
        layout = QVBoxLayout(self)
        
        # Header and baseline selector
        header_layout = QHBoxLayout()
        
        header_layout.addWidget(QLabel("<h3>Baseline Comparison</h3>"))
        header_layout.addStretch()
        
        header_layout.addWidget(QLabel("Select Baseline:"))
        self.baseline_combo = QComboBox()
        self.baseline_combo.currentTextChanged.connect(self._on_baseline_selected)
        header_layout.addWidget(self.baseline_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_baselines)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export to Excel")
        export_btn.clicked.connect(self._export_comparison)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Summary statistics - Professional Card Layout
        self.summary_group = QGroupBox("📊 Comparison Summary")
        self.summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #D0D0D0;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 8px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #37474F;
            }
        """)
        summary_main_layout = QVBoxLayout(self.summary_group)
        summary_main_layout.setSpacing(5)
        
        # Baseline Info Header
        info_widget = QWidget()
        info_widget.setStyleSheet("""
            QWidget {
                background-color: #37474F;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(10, 2, 10, 2)
        
        baseline_info_label = QLabel("📅 Baseline Date:")
        baseline_info_label.setStyleSheet("font-weight: bold; color: white; font-size: 10pt;")
        self.baseline_date_label = QLabel("-")
        self.baseline_date_label.setStyleSheet("color: white; font-weight: 600; font-size: 10pt;")
        
        info_layout.addWidget(baseline_info_label)
        info_layout.addWidget(self.baseline_date_label)
        info_layout.addStretch()
        
        summary_main_layout.addWidget(info_widget)
        
        # Status Metrics - Consistent Card Layout
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)
        
        # Helper function to create consistent metric cards
        def create_metric_card(title, icon):
            card = QWidget()
            card.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 6px;
                }
            """)
            card.setFixedHeight(60)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(5, 2, 5, 2)
            card_layout.setSpacing(0)
            
            # Icon and title row
            header_layout = QHBoxLayout()
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 12pt; background: transparent;")
            
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: 600; color: #546E7A; font-size: 9pt; background: transparent;")
            
            header_layout.addWidget(icon_label)
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            
            card_layout.addLayout(header_layout)
            
            # Value label
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold; font-size: 20pt; color: #37474F; background: transparent;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(value_label)
            
            return card, value_label
        
        # Create metric cards with consistent styling
        total_card, self.total_tasks_label = create_metric_card("Total", "📋")
        on_track_card, self.on_track_label = create_metric_card("On Track", "✓")
        late_card, self.late_label = create_metric_card("Late", "⚠")
        early_card, self.early_label = create_metric_card("Early", "⚡")
        new_card, self.new_tasks_label = create_metric_card("New", "➕")
        deleted_card, self.deleted_tasks_label = create_metric_card("Deleted", "✖")
        
        # Add variance cards to the same row
        duration_card, self.avg_duration_var_label = create_metric_card("Avg Dur. Var", "📏")
        completion_card, self.avg_completion_var_label = create_metric_card("Avg Comp. Var", "📊")
        
        status_layout.addWidget(total_card)
        status_layout.addWidget(on_track_card)
        status_layout.addWidget(late_card)
        status_layout.addWidget(early_card)
        status_layout.addWidget(new_card)
        status_layout.addWidget(deleted_card)
        status_layout.addWidget(duration_card)
        status_layout.addWidget(completion_card)
        
        summary_main_layout.addWidget(status_container)
        
        layout.addWidget(self.summary_group)
        
        # Comparison tree
        tree_label = QLabel("<b>Task-by-Task Comparison</b>")
        layout.addWidget(tree_label)
        
        self.comparison_tree = QTreeWidget()
        self.comparison_tree.setHeaderLabels([
            "Status", "Task", "WBS",  # Added Status column
            "Current Start", "Baseline Start", "Start Var (days)",
            "Current End", "Baseline End", "End Var (days)",
            "Current Duration", "Baseline Duration", "Duration Var",
            "Current %", "Baseline %", "% Var"
        ])

        # Add tooltips to headers
        header = self.comparison_tree.headerItem()
        tooltips = [
            "Status Indicator",
            "Name of the task",
            "Work Breakdown Structure code",
            "The currently planned start date of the task",
            "The start date of the task in the selected baseline",
            "The variance in the start date, in days (Current - Baseline)",
            "The currently planned end date of the task",
            "The end date of the task in the selected baseline",
            "The variance in the end date, in days (Current - Baseline)",
            "The currently planned duration of the task",
            "The duration of the task in the selected baseline",
            "The variance in duration (Current - Baseline)",
            "The current percentage of completion for the task",
            "The percentage of completion for the task in the selected baseline",
            "The variance in the percentage of completion (Current - Baseline)"
        ]
        for i, tooltip in enumerate(tooltips):
            header.setToolTip(i, tooltip)
        
        # Set column widths
        self.comparison_tree.setColumnWidth(0, 50) # Status column width
        for i in range(1, self.comparison_tree.columnCount()):
            self.comparison_tree.setColumnWidth(i, 120)
        
        self.comparison_tree.setAlternatingRowColors(False) # Disable to allow custom colors to show
        
        # Set custom delegate for Status column
        self.status_delegate = BaselineStatusDelegate()
        self.comparison_tree.setItemDelegateForColumn(0, self.status_delegate)
        
        layout.addWidget(self.comparison_tree)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("<b>Legend:</b>"))
        
        late_label = QLabel("● Late/Over") # Using circle symbol to match indicator
        late_label.setStyleSheet("color: #D32F2F; font-weight: bold;")
        legend_layout.addWidget(late_label)
        
        early_label = QLabel("● Early/Under")
        early_label.setStyleSheet("color: #388E3C; font-weight: bold;")
        legend_layout.addWidget(early_label)
        
        on_track_label = QLabel("● On Track")
        on_track_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        legend_layout.addWidget(on_track_label)
        
        new_label = QLabel("● New Task")
        new_label.setStyleSheet("color: #9C27B0; font-weight: bold;")
        legend_layout.addWidget(new_label)
        
        deleted_label = QLabel("● Deleted Task")
        deleted_label.setStyleSheet("color: #9E9E9E; font-weight: bold;")
        legend_layout.addWidget(deleted_label)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
    
    def refresh_baselines(self):
        """Refresh the baseline dropdown"""
        current_text = self.baseline_combo.currentText()
        self.baseline_combo.clear()
        
        baselines = self.data_manager.get_all_baselines()
        
        if not baselines:
            self.baseline_combo.addItem("No baselines available")
            self._clear_comparison()
            return
        
        for baseline in baselines:
            self.baseline_combo.addItem(baseline.name)
        
        # Try to restore previous selection
        if current_text:
            index = self.baseline_combo.findText(current_text)
            if index >= 0:
                self.baseline_combo.setCurrentIndex(index)
    
    def _on_baseline_selected(self, baseline_name):
        """Handle baseline selection"""
        if not baseline_name or baseline_name == "No baselines available":
            self._clear_comparison()
            return
        
        # Get comparison data
        comparison_data = self.data_manager.get_baseline_comparison(baseline_name)
        
        if not comparison_data:
            self._clear_comparison()
            return
        
        self.current_comparison = comparison_data
        self._update_summary(comparison_data['summary'], comparison_data['baseline_date'])
        self._update_comparison_tree(comparison_data['comparisons'])
    
    
    def _update_summary(self, summary, baseline_date):
        """Update summary statistics"""
        # Define consistent value label style
        value_style = "font-weight: bold; font-size: 20pt; color: #37474F; background: transparent;"
        
        self.baseline_date_label.setText(baseline_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        self.total_tasks_label.setText(str(summary['total_tasks']))
        self.total_tasks_label.setStyleSheet(value_style)
        
        self.on_track_label.setText(str(summary['tasks_on_track']))
        self.on_track_label.setStyleSheet(value_style)
        
        # Update late/early counts
        late_count = summary['tasks_late']
        self.late_label.setText(str(late_count))
        self.late_label.setStyleSheet(value_style)
        
        early_count = summary['tasks_early']
        self.early_label.setText(str(early_count))
        self.early_label.setStyleSheet(value_style)
        
        self.new_tasks_label.setText(str(summary['tasks_new']))
        self.new_tasks_label.setStyleSheet(value_style)
        
        self.deleted_tasks_label.setText(str(summary['tasks_deleted']))
        self.deleted_tasks_label.setStyleSheet(value_style)
        
        # Format variances - simple numeric format
        duration_var = summary['avg_duration_variance']
        self.avg_duration_var_label.setText(f"{duration_var:.1f}")
        self.avg_duration_var_label.setStyleSheet(value_style)
        
        completion_var = summary['avg_completion_variance']
        self.avg_completion_var_label.setText(f"{completion_var:.1f}")
        self.avg_completion_var_label.setStyleSheet(value_style)
    
    def _update_comparison_tree(self, comparisons):
        """Update the comparison tree with task data"""
        self.comparison_tree.clear()
        
        for comp in comparisons:
            item = QTreeWidgetItem()
            
            # Status Data (Column 0) - Store status string for delegate
            status = comp['end_status']
            item.setData(0, Qt.ItemDataRole.UserRole, status)

            # Task name and WBS (Shifted to 1 and 2)
            item.setText(1, comp['task_name'])
            item.setText(2, comp['wbs'])
            
            # Determine row color based on status
            if status == 'late':
                color = QColor(255, 235, 238)  # Light red
            elif status == 'early':
                color = QColor(232, 245, 233)  # Light green
            elif status == 'on-track':
                color = QColor(227, 242, 253)  # Light blue
            elif status == 'new':
                color = QColor(243, 229, 245)  # Light purple
            elif status == 'deleted':
                color = QColor(245, 245, 245)  # Light gray
            else:
                color = QColor(255, 255, 255)  # White
            
            # Set background for all columns
            # Set background for all columns and force black text for readability
            for col in range(self.comparison_tree.columnCount()):
                item.setBackground(col, QBrush(color))
                item.setForeground(col, QBrush(QColor("black")))
            
            # Start dates and variance (Shifted +1)
            if comp['current_start']:
                item.setText(3, comp['current_start'].strftime('%Y-%m-%d'))
            else:
                item.setText(3, "-")
            
            if comp['baseline_start']:
                item.setText(4, comp['baseline_start'].strftime('%Y-%m-%d'))
            else:
                item.setText(4, "-")
            
            if comp['start_variance_days'] is not None:
                var_text = f"{comp['start_variance_days']:+d}"
                item.setText(5, var_text)
                if comp['start_variance_days'] > 0:
                    item.setForeground(5, QBrush(QColor(211, 47, 47)))  # Red
                elif comp['start_variance_days'] < 0:
                    item.setForeground(5, QBrush(QColor(56, 142, 60)))  # Green
            else:
                item.setText(5, "-")
            
            # End dates and variance (Shifted +1)
            if comp['current_end']:
                item.setText(6, comp['current_end'].strftime('%Y-%m-%d'))
            else:
                item.setText(6, "-")
            
            if comp['baseline_end']:
                item.setText(7, comp['baseline_end'].strftime('%Y-%m-%d'))
            else:
                item.setText(7, "-")
            
            if comp['end_variance_days'] is not None:
                var_text = f"{comp['end_variance_days']:+d}"
                item.setText(8, var_text)
                if comp['end_variance_days'] > 0:
                    item.setForeground(8, QBrush(QColor(211, 47, 47)))  # Red
                elif comp['end_variance_days'] < 0:
                    item.setForeground(8, QBrush(QColor(56, 142, 60)))  # Green
            else:
                item.setText(8, "-")
            
            # Duration and variance (Shifted +1)
            if comp['current_duration'] is not None:
                item.setText(9, f"{comp['current_duration']:.1f}")
            else:
                item.setText(9, "-")
            
            if comp['baseline_duration'] is not None:
                item.setText(10, f"{comp['baseline_duration']:.1f}")
            else:
                item.setText(10, "-")
            
            if comp['duration_variance'] is not None:
                var_text = f"{comp['duration_variance']:+.1f}"
                item.setText(11, var_text)
                if comp['duration_variance'] > 0:
                    item.setForeground(11, QBrush(QColor(211, 47, 47)))  # Red
                elif comp['duration_variance'] < 0:
                    item.setForeground(11, QBrush(QColor(56, 142, 60)))  # Green
            else:
                item.setText(11, "-")
            
            # Completion and variance (Shifted +1)
            if comp['current_complete'] is not None:
                item.setText(12, f"{comp['current_complete']}%")
            else:
                item.setText(12, "-")
            
            if comp['baseline_complete'] is not None:
                item.setText(13, f"{comp['baseline_complete']}%")
            else:
                item.setText(13, "-")
            
            if comp['completion_variance'] is not None:
                var_text = f"{comp['completion_variance']:+d}%"
                item.setText(14, var_text)
                if comp['completion_variance'] < 0:
                    item.setForeground(14, QBrush(QColor(211, 47, 47)))  # Red (behind schedule)
                elif comp['completion_variance'] > 0:
                    item.setForeground(14, QBrush(QColor(56, 142, 60)))  # Green (ahead of schedule)
            else:
                item.setText(14, "-")
            
            self.comparison_tree.addTopLevelItem(item)
        
        # Expand all items
        self.comparison_tree.expandAll()
    
    def _clear_comparison(self):
        """Clear the comparison display"""
        self.current_comparison = None
        self.comparison_tree.clear()
        
        self.baseline_date_label.setText("-")
        self.total_tasks_label.setText("-")
        self.on_track_label.setText("-")
        self.late_label.setText("-")
        self.early_label.setText("-")
        self.new_tasks_label.setText("-")
        self.deleted_tasks_label.setText("-")
        self.avg_duration_var_label.setText("-")
        self.avg_completion_var_label.setText("-")
        
        # Restore consistent style even when cleared
        value_style = "font-weight: bold; font-size: 20pt; color: #37474F; background: transparent;"
        self.late_label.setStyleSheet(value_style)
        self.early_label.setStyleSheet(value_style)
        self.avg_duration_var_label.setStyleSheet(value_style)
        self.avg_completion_var_label.setStyleSheet(value_style)
    
    def _export_comparison(self):
        """Export baseline comparison to Excel"""
        if not self.current_comparison:
            QMessageBox.warning(self, "No Comparison", 
                              "Please select a baseline to compare before exporting.")
            return
        
        # Get file path from user
        baseline_name = self.current_comparison['baseline_name']
        suggested_name = f"Baseline_Comparison_{baseline_name}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Baseline Comparison", suggested_name, "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'
        
        try:
            # Prepare comparison data
            comparison_data = []
            for comp in self.current_comparison['comparisons']:
                comparison_data.append({
                    'Task ID': comp['task_id'],
                    'Task Name': comp['task_name'],
                    'WBS': comp['wbs'],
                    'Current Start': comp['current_start'].strftime('%Y-%m-%d') if comp['current_start'] else '-',
                    'Baseline Start': comp['baseline_start'].strftime('%Y-%m-%d') if comp['baseline_start'] else '-',
                    'Start Variance (days)': comp['start_variance_days'] if comp['start_variance_days'] is not None else '-',
                    'Current End': comp['current_end'].strftime('%Y-%m-%d') if comp['current_end'] else '-',
                    'Baseline End': comp['baseline_end'].strftime('%Y-%m-%d') if comp['baseline_end'] else '-',
                    'End Variance (days)': comp['end_variance_days'] if comp['end_variance_days'] is not None else '-',
                    'Current Duration': f"{comp['current_duration']:.1f}" if comp['current_duration'] is not None else '-',
                    'Baseline Duration': f"{comp['baseline_duration']:.1f}" if comp['baseline_duration'] is not None else '-',
                    'Duration Variance': f"{comp['duration_variance']:+.1f}" if comp['duration_variance'] is not None else '-',
                    'Current % Complete': f"{comp['current_complete']}%" if comp['current_complete'] is not None else '-',
                    'Baseline % Complete': f"{comp['baseline_complete']}%" if comp['baseline_complete'] is not None else '-',
                    '% Complete Variance': f"{comp['completion_variance']:+d}%" if comp['completion_variance'] is not None else '-',
                    'Status': comp['end_status']
                })
            
            # Prepare summary data
            summary = self.current_comparison['summary']
            summary_data = {
                'Metric': [
                    'Baseline Name',
                    'Baseline Date',
                    'Total Tasks',
                    'Tasks On Track',
                    'Tasks Late',
                    'Tasks Early',
                    'New Tasks',
                    'Deleted Tasks',
                    'Avg Duration Variance',
                    'Avg Completion Variance'
                ],
                'Value': [
                    baseline_name,
                    self.current_comparison['baseline_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    summary['total_tasks'],
                    summary['tasks_on_track'],
                    summary['tasks_late'],
                    summary['tasks_early'],
                    summary['tasks_new'],
                    summary['tasks_deleted'],
                    f"{summary['avg_duration_variance']:+.2f}",
                    f"{summary['avg_completion_variance']:+.1f}%"
                ]
            }
            
            # Write to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Write summary
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Write comparison
                df_comparison = pd.DataFrame(comparison_data)
                df_comparison.to_excel(writer, sheet_name='Comparison', index=False)
                
                # Format sheets
                workbook = writer.book
                
                # Format summary sheet
                summary_sheet = writer.sheets['Summary']
                for col in summary_sheet.columns:
                    max_length = max(len(str(cell.value)) for cell in col)
                    summary_sheet.column_dimensions[col[0].column_letter].width = max_length + 2
                
                # Format comparison sheet
                comparison_sheet = writer.sheets['Comparison']
                for col in comparison_sheet.columns:
                    max_length = max(len(str(cell.value)) for cell in col)
                    comparison_sheet.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Success")
            msg_box.setText(f"Baseline comparison exported successfully to:\n{file_path}")
            msg_box.setIcon(QMessageBox.Icon.Information)
            
            open_button = msg_box.addButton("Open File", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton(QMessageBox.StandardButton.Ok)
            
            msg_box.exec()
            
            if msg_box.clickedButton() == open_button:
                import os
                os.startfile(file_path)
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", 
                               f"Failed to export baseline comparison:\n{str(e)}")
