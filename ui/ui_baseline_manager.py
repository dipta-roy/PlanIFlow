"""
Baseline Operations Mixin - Baseline management methods for MainWindow
"""

from ui.ui_baseline_dialog import BaselineDialog

class BaselineOperationsMixin:
    """Mixin for baseline-related operations"""
    
    def _manage_baselines(self):
        """Show baseline management dialog"""
        dialog = BaselineDialog(self.data_manager, self)
        dialog.exec()
        
        # Refresh baseline comparison tab if it exists
        if hasattr(self, 'baseline_comparison'):
            self.baseline_comparison.refresh_baselines()
    
    def _show_baseline_comparison(self):
        """Switch to baseline comparison tab"""
        if hasattr(self, 'baseline_comparison'):
            index = self.tabs.indexOf(self.baseline_comparison)
            if index != -1:
                self.tabs.setCurrentIndex(index)
                self.baseline_comparison.refresh_baselines()
                return

        # Fallback search if widget instance index is not found directly
        for i in range(self.tabs.count()):
            if "Baseline Comparison" in self.tabs.tabText(i):
                self.tabs.setCurrentIndex(i)
                if hasattr(self, 'baseline_comparison'):
                    self.baseline_comparison.refresh_baselines()
                break
