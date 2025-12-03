from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from datetime import datetime
import os
import logging
import json
from exporter.exporter import Exporter
from exporter.pdf_exporter import PDFExporter

class FileOperationsMixin:
    """Mixin for file operations in MainWindow"""
    
    def _new_project(self):
        """Create new project"""
        reply = QMessageBox.question(self, "New Project", 
                                    "Create a new project? Unsaved changes will be lost.",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_all()
            self.current_file = None
            self._update_all_views()
            self.status_label.setText("New project created")
            self._remove_last_project_path()

    def _close_project(self):
        """Close current project"""
        reply = QMessageBox.question(self, "Close Project", 
                                    "Close the current project? Unsaved changes will be lost.",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_all()
            self.current_file = None
            self._update_all_views()
            self.status_label.setText("Project closed")
            self._remove_last_project_path()
    
    def _rename_project(self):
        """Rename current project"""
        text, ok = QInputDialog.getText(self, "Rename Project", 
                                       "Enter new project name:",
                                       text=self.data_manager.project_name)
        
        if ok and text:
            self.data_manager.project_name = text
            self._update_all_views()
            self.status_label.setText(f"Project renamed to '{text}'")
    
    def _open_project(self):
        """Open existing project"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Project Files (*.json)"
        )
        
        if file_path:
            data_manager, calendar_manager, success = Exporter.import_from_json(file_path)
            
            if success:
                self.data_manager = data_manager
                self.data_manager.calendar_manager = calendar_manager
                self.calendar_manager = calendar_manager
                self.current_file = file_path
                self._update_all_views()
                self._expand_all_tasks()
                self.status_label.setText(f"Opened: {self.data_manager.project_name}")
                self._save_last_project_path(file_path)
            else:
                QMessageBox.critical(self, "Error", "Failed to open project file.")
    
    def _save_project(self):
        """Save current project"""
        if self.current_file:
            if Exporter.export_to_json(self.data_manager, self.calendar_manager, self.current_file):
                self.last_save_time = datetime.now()
                self.save_time_label.setText(f"Last saved: {self.last_save_time.strftime('%H:%M:%S')}")
                self.status_label.setText("Project saved")
            else:
                QMessageBox.critical(self, "Error", "Failed to save project.")
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Save project with new name"""
        # Suggest filename based on project name
        suggested_name = self.data_manager.project_name.replace(" ", "_") + ".json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", suggested_name, "Project Files (*.json)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            
            if Exporter.export_to_json(self.data_manager, self.calendar_manager, file_path):
                self.current_file = file_path
                self.last_save_time = datetime.now()
                self.save_time_label.setText(f"Last saved: {self.last_save_time.strftime('%H:%M:%S')}")
                self.status_label.setText(f"Saved as: {self.data_manager.project_name}")
                self._save_last_project_path(file_path)
            else:
                QMessageBox.critical(self, "Error", "Failed to save project.")
    
    def _import_excel(self):
        """Import project from Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import from Excel", "", "Excel Files (*.xlsx)"
        )
        
        if file_path:
            data_manager, success = Exporter.import_from_excel(file_path)
            
            if success:
                self.data_manager = data_manager
                self.data_manager.calendar_manager = self.calendar_manager
                self._update_all_views()
                self.status_label.setText("Imported from Excel")
            else:
                QMessageBox.critical(self, "Error", "Failed to import Excel file.")
    
    def _export_excel(self):
        """Export project to Excel"""
        # Suggest filename based on project name
        suggested_name = self.data_manager.project_name.replace(" ", "_") + ".xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", suggested_name, "Excel Files (*.xlsx)"
        )
        
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            
            if Exporter.export_to_excel(self.data_manager, file_path):
                self.status_label.setText("Exported to Excel")
                QMessageBox.information(self, "Success", 
                                      f"Project exported successfully to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export to Excel.")

    def _export_pdf(self):
        """Export project to PDF"""
        suggested_name = self.data_manager.project_name.replace(" ", "_") + ".pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to PDF", suggested_name, "PDF Files (*.pdf)"
        )
        
        if file_path:
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'
            
            try:
                exporter = PDFExporter(self.data_manager, file_path, self.calendar_manager)
                exporter.export()
                self.status_label.setText("Exported to PDF")
                QMessageBox.information(self, "Success", 
                                      f"Project exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export to PDF: {e}")
    
    # Utility Methods
    def _save_last_project_path(self, path: str):
        """Save last opened project path"""
        try:
            with open('.last_project', 'w') as f:
                f.write(path)
        except IOError as e:
            logging.error(f"Failed to save last project path: {e}")
    
    def _remove_last_project_path(self):
        """Remove the last opened project path file"""
        try:
            if os.path.exists('.last_project'):
                os.remove('.last_project')
        except IOError as e:
            logging.error(f"Failed to remove last project path: {e}")
    
    def _try_load_last_project(self):
        """Try to load last opened project"""
        try:
            if os.path.exists('.last_project'):
                with open('.last_project', 'r') as f:
                    path = f.read().strip()
                
                if os.path.exists(path):
                    data_manager, calendar_manager, success = Exporter.import_from_json(path)
                    if success:
                        self.data_manager = data_manager
                        self.data_manager.calendar_manager = calendar_manager
                        self.calendar_manager = calendar_manager
                        self.current_file = path
                        self._update_all_views()
                        self._expand_all_tasks()
                        self.status_label.setText(f"Loaded: {self.data_manager.project_name}")
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load last project: {e}")
