from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QSpinBox, QProgressBar, QGroupBox,
                             QDialog, QDialogButtonBox, QTextBrowser)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from data_manager.monte_carlo import MonteCarloSimulator

class MonteCarloHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Monte Carlo Risk Analysis")
        self.resize(600, 700)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml("""
            <h1>Monte Carlo Risk Analysis</h1>
            
            <h2>Description</h2>
            <p>
            Monte Carlo Simulation is a mathematical technique used to estimate the possible outcomes of an uncertain event. 
            In project management, it helps predict the likelihood of completing a project on time by accounting for 
            schedule risks and task duration uncertainties.
            </p>
            
            <h2>Usage</h2>
            <ol>
                <li><b>Set Iterations:</b> Choose the number of simulation runs (default 1000). More iterations provide smoother statistical results but take longer.</li>
                <li><b>Run Analysis:</b> Click the "Run Analysis" button to start the simulation.</li>
                <li><b>Interpret Results:</b> Review the <i>Forecast</i> timestamps, <i>Confidence Table</i>, and <i>Risk Drivers</i>.</li>
            </ol>
            
            <h2>Methodology</h2>
            <p>
            The simulation performs the following steps for each iteration:
            </p>
            <ul>
                <li><b>Random Sampling:</b> For every task, a duration is randomly selected from a designated probability distribution. 
                We use a <b>Triangular Distribution</b> based on Optimistic (-25%), Most Likely (Current), and Pessimistic (+25%) estimates.</li>
                
                <li><b>Critical Path Calculation:</b> The project schedule is recalculated using these random durations, respecting all task dependencies and calendar constraints.
                The total project duration and the specific tasks on the critical path are recorded.</li>
                
                <li><b>Aggregation:</b> After thousands of such "virtual projects" are run, the results are aggregated to form a probability distribution of the completion date.</li>
            </ul>
            
            <h3>Key Concepts</h3>
            <ul>
                <li><b>P50 (Median):</b> The date by which there is a 50% chance the project will be completed. It is the "coin flip" date.</li>
                <li><b>P80 (Low Risk):</b> The date by which there is an 80% chance of completion. This is a safer bet for managing stakeholder expectations.</li>
                <li><b>P90 (Review Risk):</b> The date by which there is a 90% chance of completion. Missing this date is statistically unlikely unless major unknown risks occur.</li>
                <li><b>Critical Risk Drivers:</b> These are the specific work tasks that most frequently appear on the critical path during the simulation. 
                Focusing management attention on these tasks yields the highest return for schedule security.</li>
            </ul>
        """)
        layout.addWidget(text_browser)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

class SimulationThread(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, simulator, iterations):
        super().__init__()
        self.simulator = simulator
        self.iterations = iterations
        
    def run(self):
        results = self.simulator.run_simulation(self.iterations)
        self.finished.emit(results)

class MonteCarloTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_group = QGroupBox("Simulation Settings")
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Iterations:"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(100, 10000)
        self.iterations_spin.setValue(1000)
        self.iterations_spin.setSingleStep(100)
        controls_layout.addWidget(self.iterations_spin)
        
        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.clicked.connect(self.run_simulation)
        controls_layout.addWidget(self.run_btn)
        
        self.help_btn = QPushButton("About Monte Carlo")
        self.help_btn.setFixedWidth(150)
        self.help_btn.setToolTip("About Monte Carlo Analysis")
        self.help_btn.clicked.connect(self.show_help)
        controls_layout.addWidget(self.help_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results
        results_group = QGroupBox("Forecast Results")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        # Use a monospace font for nice table alignment
        font = self.results_text.font()
        font.setFamily("Consolas")
        font.setStyleHint(font.StyleHint.Monospace)
        self.results_text.setFont(font)
        
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
    def show_help(self):
        """Show the help dialog"""
        dialog = MonteCarloHelpDialog(self)
        dialog.exec()
        
    def run_simulation(self):
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        self.results_text.clear()
        self.results_text.setText("Running simulation... Please wait.")
        
        # Prepare simulator (using current tasks)
        tasks = self.data_manager.get_all_tasks()
        if not tasks:
             self.results_text.setText("No tasks to simulate.")
             self.run_btn.setEnabled(True)
             self.progress_bar.setVisible(False)
             return

        simulator = MonteCarloSimulator(tasks, self.data_manager.calendar_manager)
        
        self.thread = SimulationThread(simulator, self.iterations_spin.value())
        self.thread.finished.connect(self.on_simulation_finished)
        self.thread.start()
        
    def on_simulation_finished(self, results):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.display_results(results)
        
    def display_results(self, results):
        if not results:
            self.results_text.setText("Simulation failed or no valid dates found.")
            return
            
        def fmt(d):
            return d.strftime("%Y-%m-%d") if d else "N/A"
            
        report = []
        report.append("Monte Carlo Forecast Results")
        report.append("=" * 40)
        report.append(f"Iterations run: {results.get('iterations', 0)}")
        
        report.append(f"Duration Range: {fmt(results.get('min_date'))} to {fmt(results.get('max_date'))}")
        report.append("")
        
        report.append("Statistical Forecast:")
        report.append(f"P50 (Median):    {fmt(results.get('p50_date'))}")
        report.append(f"P80 (80% Conf):  {fmt(results.get('p80_date'))}")
        report.append(f"P90 (90% Conf):  {fmt(results.get('p90_date'))}")
        report.append(f"Mean Date:       {fmt(results.get('mean_date'))}")
        report.append(f"Std Deviation:   {results.get('stdev_days', 0):.2f} days")
        report.append("")

        report.append("Confidence Table:")
        report.append("-" * 75)
        report.append(f"{'Confidence':<20} | {'Predicted Completion Date':<25} | {'Notes'}")
        report.append("-" * 75)
        report.append(f"{'50 percent (P50)':<20} | {fmt(results.get('p50_date')):<25} | Most likely timeline")
        report.append(f"{'80 percent (P80)':<20} | {fmt(results.get('p80_date')):<25} | More conservative planning")
        report.append(f"{'90 percent (P90)':<20} | {fmt(results.get('p90_date')):<25} | Risk-buffered delivery")
        report.append("-" * 75)
        report.append("")
        
        report.append("Top Risk Drivers (Ranked):")
        report.append("-" * 75)
        report.append(f"{'Task Name':<40} | {'Freq':<8} | {'Reason'}")
        report.append("-" * 75)
        
        critical_counts = results.get('critical_tasks', {})
        if critical_counts:
            # Sort by frequency
            sorted_risks = sorted(critical_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Filter to show only actual work tasks (exclude summaries and milestones)
            filtered_risks = []
            for task_id, count in sorted_risks:
                task = self.data_manager.get_task(task_id)
                if task and not task.is_summary and not task.is_milestone:
                    filtered_risks.append((task_id, count))
            
            top_risks = filtered_risks[:5]
            
            iterations = results.get('iterations', 1)
            
            for task_id, count in top_risks:
                task = self.data_manager.get_task(task_id)
                if not task: continue
                
                name = task.name
                # Truncate name if too long
                if len(name) > 38: name = name[:35] + "..."
                
                pct = (count / iterations) * 100
                
                reason = "Frequent critical path"
                if pct > 50: reason = "Dominates schedule"
                if pct > 80: reason = "Critical Bottleneck"
                
                report.append(f"{name:<40} | {pct:>5.1f}% | {reason}")
            
            if not top_risks:
                 report.append("No specific risk drivers identified (work tasks).")
        else:
            report.append("No specific risk drivers identified.")
            
        report.append("-" * 75)
        report.append("")
        
        # ASCII Histogram
        dates = sorted(results.get('completion_dates', []))
        if dates:
            report.append("Completion Date Distribution:")
            report.append("-" * 75)
            
            # Create buckets
            min_ts = dates[0].timestamp()
            max_ts = dates[-1].timestamp()
            duration = max_ts - min_ts
            
            if duration == 0:
                report.append(f"{fmt(dates[0])}: {'#' * 50} (100%)")
            else:
                num_buckets = 10
                bucket_size = duration / num_buckets
                buckets = [0] * num_buckets
                
                for d in dates:
                    idx = int((d.timestamp() - min_ts) / bucket_size)
                    if idx >= num_buckets: idx = num_buckets - 1
                    buckets[idx] += 1
                
                max_freq = max(buckets)
                scale = 50.0 / max_freq if max_freq > 0 else 1
                
                start_ts = min_ts
                for i in range(num_buckets):
                    freq = buckets[i]
                    bar_len = int(freq * scale)
                    
                    # Label is the start date of the bucket
                    bucket_date = datetime.fromtimestamp(start_ts).strftime("%m-%d")
                    bar = '#' * bar_len
                    if freq > 0:
                        report.append(f"{bucket_date:<6} | {bar:<50} ({freq})")
                    start_ts += bucket_size
                    
        report.append("-" * 75)
        report.append("")
        
        report.append("Summary:")
        report.append(f"Based on the simulation, there is a reasonable likelihood of completing the project by {fmt(results.get('p50_date'))} (P50).")
        report.append(f"However, to be 80% confident, planning toward {fmt(results.get('p80_date'))} is safer.")
        if results.get('stdev_days', 0) > 5:
             report.append("High variance indicates significant schedule risk.")
        
        self.results_text.setText("\n".join(report))
