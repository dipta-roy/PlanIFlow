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
        # Find the baseline comparison tab index
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "📊 Baseline Comparison":
                self.tabs.setCurrentIndex(i)
                
                # Refresh the comparison data
                if hasattr(self, 'baseline_comparison'):
                    self.baseline_comparison.refresh_baselines()
                break
