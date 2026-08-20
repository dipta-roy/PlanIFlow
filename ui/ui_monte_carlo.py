from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSpinBox, QProgressBar,
                             QDialog, QDialogButtonBox, QTextBrowser,
                             QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from data_manager.monte_carlo import MonteCarloSimulator

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


# ---------------------------------------------------------------------------
# Theme Palette (mirrors dashboard palette tokens)
# ---------------------------------------------------------------------------

def _get_risk_palette(dark_mode: bool) -> dict:
    if dark_mode:
        return {
            "bg":            "#232323",
            "card_bg":       "#2d2d2d",
            "card_border":   "#3d3d3d",
            "text":          "#E0E0E0",
            "text_muted":    "#9E9E9E",
            "header_text":   "#FFFFFF",
            "accent":        "#42A5F5",
            "accent_hover":  "#1E88E5",
            "chart_bg":      "#2d2d2d",
            "chart_text":    "#CCCCCC",
            "chart_grid":    "#444444",
            "success":       "#66BB6A",
            "warning":       "#FFA726",
            "danger":        "#EF5350",
            "info":          "#29B6F6",
            "p50_color":     "#42A5F5",
            "p80_color":     "#FFA726",
            "p90_color":     "#EF5350",
            "input_bg":      "#353535",
            "input_border":  "#555555",
        }
    else:
        return {
            "bg":            "#F5F7FA",
            "card_bg":       "#FFFFFF",
            "card_border":   "#E0E4E8",
            "text":          "#37474F",
            "text_muted":    "#78909C",
            "header_text":   "#263238",
            "accent":        "#1E88E5",
            "accent_hover":  "#1565C0",
            "chart_bg":      "#FFFFFF",
            "chart_text":    "#455A64",
            "chart_grid":    "#ECEFF1",
            "success":       "#43A047",
            "warning":       "#FB8C00",
            "danger":        "#E53935",
            "info":          "#039BE5",
            "p50_color":     "#1E88E5",
            "p80_color":     "#FB8C00",
            "p90_color":     "#E53935",
            "input_bg":      "#FFFFFF",
            "input_border":  "#CFD8DC",
        }


# ---------------------------------------------------------------------------
# Help Dialog (unchanged content, updated styling)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Simulation Thread
# ---------------------------------------------------------------------------

class SimulationThread(QThread):
    finished = pyqtSignal(object)
    progress_changed = pyqtSignal(int)

    def __init__(self, simulator, iterations):
        super().__init__()
        self.simulator = simulator
        self.iterations = iterations

    def run(self):
        results = self.simulator.run_simulation(
            self.iterations, progress_callback=self.progress_changed.emit
        )
        self.finished.emit(results)


# ---------------------------------------------------------------------------
# Card Helpers
# ---------------------------------------------------------------------------

def _make_card(palette, extra_style="") -> QFrame:
    """Generic card frame."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {palette['card_bg']};
            border: 1px solid {palette['card_border']};
            border-radius: 8px;
            {extra_style}
        }}
    """)
    return card


def _make_kpi_card(title: str, value: str, accent: str, palette: dict) -> QFrame:
    """Small KPI tile with accent top border."""
    card = QFrame()
    card.setObjectName("kpiCard")
    card.setStyleSheet(f"""
        QFrame#kpiCard {{
            background-color: {palette['card_bg']};
            border: 1px solid {palette['card_border']};
            border-top: 3px solid {accent};
            border-radius: 8px;
            padding: 2px;
        }}
    """)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    card.setMinimumHeight(85)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(4)

    t = QLabel(title)
    t.setStyleSheet(f"color: {palette['text_muted']}; font-size: 11px; font-weight: 500; border: none;")
    layout.addWidget(t)

    v = QLabel(value)
    v.setObjectName("kpiValue")
    v.setStyleSheet(f"color: {palette['header_text']}; font-size: 18px; font-weight: bold; border: none;")
    layout.addWidget(v)

    return card


# ---------------------------------------------------------------------------
# Main Monte Carlo Tab
# ---------------------------------------------------------------------------

class MonteCarloTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.dark_mode = False
        self._last_results = None
        self.init_ui()

    def set_dark_mode(self, dark_mode: bool):
        """Refresh Monte Carlo risk view when dark mode changes"""
        self.dark_mode = dark_mode
        self.init_ui()
        if self._last_results:
            self.display_results(self._last_results)

    def init_ui(self):
        dark_mode = getattr(self, 'dark_mode', getattr(self.parent(), 'dark_mode', False) if self.parent() else False)
        pal = _get_risk_palette(dark_mode)
        self._palette = pal

        if self.layout() is not None:
            outer = self.layout()
            while outer.count():
                item = outer.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        else:
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {pal['bg']}; }}")

        container = QWidget()
        container.setStyleSheet(f"background-color: {pal['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        outer.addWidget(scroll)
        scroll.setWidget(container)


        # ── Header Card ──────────────────────────────────────────────
        header = _make_card(pal)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        title_row = QHBoxLayout()
        title_lbl = QLabel("🎲  Monte Carlo Risk Analysis")
        title_lbl.setStyleSheet(
            f"color: {pal['header_text']}; font-size: 20px; font-weight: bold; border: none;"
        )
        desc_lbl = QLabel(
            "Simulate thousands of schedule scenarios to forecast completion dates "
            "and identify the biggest risk drivers."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {pal['text_muted']}; font-size: 12px; border: none; margin-top: 4px;")

        title_row.addWidget(title_lbl)
        title_row.addStretch()

        # Help button (small, secondary)
        self.help_btn = QPushButton("ℹ  About")
        self.help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {pal['accent']};
                font-weight: 600;
                padding: 5px 12px;
                border: 1px solid {pal['accent']};
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {pal['accent']};
                color: white;
            }}
        """)
        self.help_btn.clicked.connect(self.show_help)
        title_row.addWidget(self.help_btn)

        header_layout.addLayout(title_row)
        header_layout.addWidget(desc_lbl)
        layout.addWidget(header)

        # ── Controls Card ────────────────────────────────────────────
        ctrl_card = _make_card(pal)
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(12)

        iter_lbl = QLabel("Iterations:")
        iter_lbl.setStyleSheet(f"color: {pal['text']}; font-size: 12px; font-weight: 600; border: none;")
        ctrl_layout.addWidget(iter_lbl)

        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(100, 10000)
        self.iterations_spin.setValue(1000)
        self.iterations_spin.setSingleStep(100)
        self.iterations_spin.setFixedWidth(120)
        self.iterations_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {pal['input_bg']};
                color: {pal['text']};
                border: 1px solid {pal['input_border']};
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 13px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                width: 16px;
            }}
        """)
        ctrl_layout.addWidget(self.iterations_spin)

        self.run_btn = QPushButton("▶  Run Analysis")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {pal['accent']};
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
                border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {pal['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {pal['card_border']};
                color: {pal['text_muted']};
            }}
        """)
        self.run_btn.clicked.connect(self.run_simulation)
        ctrl_layout.addWidget(self.run_btn)

        ctrl_layout.addStretch()

        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            f"color: {pal['text_muted']}; font-size: 11px; font-style: italic; border: none;"
        )
        ctrl_layout.addWidget(self.status_label)

        layout.addWidget(ctrl_card)

        # ── Progress Bar ─────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: {pal['card_border']};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {pal['accent']};
                border-radius: 2px;
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # ── KPI Summary Row (hidden until results) ───────────────────
        self.kpi_row_widget = QWidget()
        self.kpi_row_widget.setStyleSheet(f"background-color: {pal['bg']}; border: none;")
        self.kpi_row = QHBoxLayout(self.kpi_row_widget)
        self.kpi_row.setContentsMargins(0, 0, 0, 0)
        self.kpi_row.setSpacing(12)
        self.kpi_row_widget.setVisible(False)
        layout.addWidget(self.kpi_row_widget)

        # ── Chart Card (hidden until results) ─────────────────────────
        self.chart_card = _make_card(pal)
        self.chart_card_layout = QVBoxLayout(self.chart_card)
        self.chart_card_layout.setContentsMargins(14, 12, 14, 12)
        self.chart_card_layout.setSpacing(4)

        chart_title = QLabel("📊 Schedule Completion Distribution")
        chart_title.setStyleSheet(
            f"color: {pal['text']}; font-size: 12px; font-weight: bold; border: none;"
        )
        self.chart_card_layout.addWidget(chart_title)

        chart_desc = QLabel(
            "Each bar shows how many simulations finished on that date. "
            "Taller bars = more likely completion dates. "
            "Dashed lines mark P50 (50% chance), P80 (80%), and P90 (90%) confidence levels."
        )
        chart_desc.setWordWrap(True)
        chart_desc.setStyleSheet(
            f"color: {pal['text_muted']}; font-size: 10px; border: none; padding-bottom: 4px;"
        )
        self.chart_card_layout.addWidget(chart_desc)

        self.histogram_figure = Figure(figsize=(8, 3), dpi=100)
        self.histogram_figure.patch.set_facecolor(pal['chart_bg'])
        self.histogram_canvas = FigureCanvas(self.histogram_figure)
        self.histogram_canvas.setStyleSheet("border: none;")
        self.chart_card_layout.addWidget(self.histogram_canvas)

        self.chart_card.setVisible(False)
        layout.addWidget(self.chart_card)

        # ── Results Cards Area ────────────────────────────────────────
        self.results_area = QWidget()
        self.results_area.setStyleSheet(f"background-color: {pal['bg']}; border: none;")
        self.results_layout = QVBoxLayout(self.results_area)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)
        self.results_area.setVisible(False)
        layout.addWidget(self.results_area)

        # Placeholder message
        self.placeholder = QLabel(
            "Configure the number of iterations and click Run Analysis to begin the Monte Carlo simulation."
        )
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet(
            f"color: {pal['text_muted']}; font-size: 13px; font-style: italic; "
            f"padding: 40px; border: none;"
        )
        layout.addWidget(self.placeholder)

        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def show_help(self):
        dialog = MonteCarloHelpDialog(self)
        dialog.exec()

    def run_simulation(self):
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Running simulation…")
        self.placeholder.setVisible(False)

        tasks = self.data_manager.get_all_tasks()
        if not tasks:
            self.status_label.setText("⚠ No tasks to simulate.")
            self.run_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.placeholder.setText("No tasks available. Add tasks to your project first.")
            self.placeholder.setVisible(True)
            return

        simulator = MonteCarloSimulator(tasks, self.data_manager.calendar_manager)
        self.sim_thread = SimulationThread(simulator, self.iterations_spin.value())
        self.sim_thread.progress_changed.connect(self.progress_bar.setValue)
        self.sim_thread.finished.connect(self.on_simulation_finished)
        self.sim_thread.start()

    def clear_view(self):
        """Clear all inputs and results."""
        self.iterations_spin.setValue(1000)
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.status_label.setText("Ready")
        self.kpi_row_widget.setVisible(False)
        self.chart_card.setVisible(False)
        self.results_area.setVisible(False)
        self.placeholder.setText(
            "Configure the number of iterations and click Run Analysis to begin."
        )
        self.placeholder.setVisible(True)
        self._last_results = None

    def on_simulation_finished(self, results):
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._last_results = results
        self.display_results(results)

    # ------------------------------------------------------------------
    # Results Display
    # ------------------------------------------------------------------

    def display_results(self, results):
        dark_mode = getattr(self.parent(), 'dark_mode', False) if self.parent() else False
        pal = _get_risk_palette(dark_mode)
        self._palette = pal

        if not results:
            self.status_label.setText("❌ Simulation failed or no valid dates found.")
            self.placeholder.setText("Simulation failed. Check project data and try again.")
            self.placeholder.setVisible(True)
            return

        def fmt(d):
            return d.strftime("%d %b %Y") if d else "N/A"

        self.status_label.setText(
            f"✅ Completed {results.get('iterations', 0):,} iterations"
        )
        self.placeholder.setVisible(False)

        # ── KPI Summary Cards ────────────────────────────────────────
        # Clear old KPIs
        while self.kpi_row.count():
            item = self.kpi_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        kpis = [
            ("Iterations",     f"{results.get('iterations', 0):,}",        pal['info']),
            ("P50 (Median)",   fmt(results.get('p50_date')),               pal['p50_color']),
            ("P80 (80% Conf)", fmt(results.get('p80_date')),               pal['p80_color']),
            ("P90 (90% Conf)", fmt(results.get('p90_date')),               pal['p90_color']),
            ("Std Deviation",  f"{results.get('stdev_days', 0):.1f} days", pal['text_muted']),
        ]
        for title, val, accent in kpis:
            self.kpi_row.addWidget(_make_kpi_card(title, val, accent, pal))

        self.kpi_row_widget.setVisible(True)

        # ── Histogram Chart ──────────────────────────────────────────
        self._draw_histogram(results, pal)
        self.chart_card.setVisible(True)

        # ── Detail Cards ─────────────────────────────────────────────
        # Clear old cards
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Confidence Table Card
        self.results_layout.addWidget(
            self._build_confidence_card(results, pal)
        )

        # Risk Drivers Card
        self.results_layout.addWidget(
            self._build_risk_drivers_card(results, pal)
        )

        # Summary Card
        self.results_layout.addWidget(
            self._build_summary_card(results, pal)
        )

        self.results_area.setVisible(True)

    # ------------------------------------------------------------------
    # Histogram
    # ------------------------------------------------------------------

    def _draw_histogram(self, results, pal):
        fig = self.histogram_figure
        fig.clear()
        fig.patch.set_facecolor(pal['chart_bg'])

        ax = fig.add_subplot(111)
        ax.set_facecolor(pal['chart_bg'])

        dates = sorted(results.get('completion_dates', []))
        if not dates or len(dates) < 2:
            ax.text(0.5, 0.5, "Insufficient data for histogram",
                    ha='center', va='center', color=pal['text_muted'],
                    transform=ax.transAxes, fontsize=11)
            ax.set_xticks([])
            ax.set_yticks([])
            self.histogram_canvas.draw()
            return

        # Convert to matplotlib date numbers
        date_nums = mdates.date2num(dates)
        n_bins = min(25, max(10, len(set(dates)) // 2))

        n, bins, patches = ax.hist(
            date_nums, bins=n_bins, color=pal['accent'],
            alpha=0.7, edgecolor=pal['chart_bg'], linewidth=0.5, zorder=3
        )

        # Mark P50, P80, P90 lines
        for pkey, label, color, ls in [
            ('p50_date', 'P50', pal['p50_color'], '--'),
            ('p80_date', 'P80', pal['p80_color'], '--'),
            ('p90_date', 'P90', pal['p90_color'], '--'),
        ]:
            d = results.get(pkey)
            if d:
                dn = mdates.date2num(d)
                ax.axvline(dn, color=color, linestyle=ls, linewidth=1.5,
                           label=f"{label}: {d.strftime('%d %b %Y')}", zorder=5)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.tick_params(axis='x', rotation=35, labelsize=7, colors=pal['chart_text'])
        ax.tick_params(axis='y', labelsize=8, colors=pal['chart_text'])
        ax.set_xlabel('Projected Completion Date', fontsize=9, color=pal['chart_text'])
        ax.set_ylabel('Number of Simulations', fontsize=9, color=pal['chart_text'])
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=pal['chart_grid'])
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_color(pal['chart_grid'])

        ax.legend(fontsize=8, framealpha=0.6, loc='upper right',
                  labelcolor=pal['chart_text'])

        fig.tight_layout()
        self.histogram_canvas.draw()

    # ------------------------------------------------------------------
    # Card Builders
    # ------------------------------------------------------------------

    def _build_confidence_card(self, results, pal) -> QFrame:
        """Confidence table rendered as styled HTML."""
        card = _make_card(pal)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        title = QLabel("📋  Confidence Table")
        title.setStyleSheet(
            f"color: {pal['text']}; font-size: 13px; font-weight: bold; border: none;"
        )
        layout.addWidget(title)

        def fmt(d):
            return d.strftime("%d %b %Y") if d else "N/A"

        rows_html = ""
        table_data = [
            ("P50 – Median",       results.get('p50_date'), "Most likely timeline",          pal['p50_color']),
            ("P80 – Conservative", results.get('p80_date'), "Safer stakeholder commitment",  pal['p80_color']),
            ("P90 – Risk-Buffered",results.get('p90_date'), "High-confidence delivery date", pal['p90_color']),
        ]
        for label, date, note, color in table_data:
            rows_html += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid {pal['card_border']};">
                    <span style="color: {color}; font-weight: bold;">●</span>&nbsp; {label}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid {pal['card_border']}; font-weight: bold;">
                    {fmt(date)}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid {pal['card_border']}; color: {pal['text_muted']};">
                    {note}
                </td>
            </tr>"""

        html = f"""
        <table style="width: 100%; border-collapse: collapse; color: {pal['text']}; font-size: 12px;">
            <tr style="background-color: {pal['card_border']};">
                <th style="padding: 8px 12px; text-align: left;">Confidence Level</th>
                <th style="padding: 8px 12px; text-align: left;">Predicted Completion</th>
                <th style="padding: 8px 12px; text-align: left;">Notes</th>
            </tr>
            {rows_html}
        </table>
        """

        table_label = QLabel(html)
        table_label.setStyleSheet("border: none;")
        table_label.setWordWrap(True)
        layout.addWidget(table_label)

        # Extra stats
        stats_row = QHBoxLayout()
        for label, val in [
            ("Duration Range",
             f"{results.get('min_date', datetime.now()).strftime('%d %b %Y')} → "
             f"{results.get('max_date', datetime.now()).strftime('%d %b %Y')}"),
            ("Mean Date", fmt(results.get('mean_date'))),
            ("Std Dev", f"{results.get('stdev_days', 0):.1f} days"),
        ]:
            stat = QLabel(f"<b>{label}:</b> {val}")
            stat.setStyleSheet(
                f"color: {pal['text_muted']}; font-size: 11px; border: none; padding: 4px 0;"
            )
            stats_row.addWidget(stat)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        return card

    def _build_risk_drivers_card(self, results, pal) -> QFrame:
        """Top risk drivers rendered as styled rows."""
        card = _make_card(pal)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        title = QLabel("⚠  Top Risk Drivers")
        title.setStyleSheet(
            f"color: {pal['text']}; font-size: 13px; font-weight: bold; border: none;"
        )
        layout.addWidget(title)

        critical_counts = results.get('critical_tasks', {})
        iterations = results.get('iterations', 1)

        if not critical_counts:
            empty = QLabel("No critical path data available.")
            empty.setStyleSheet(
                f"color: {pal['text_muted']}; font-style: italic; border: none; padding: 8px;"
            )
            layout.addWidget(empty)
            return card

        # Filter to work tasks only
        sorted_risks = sorted(critical_counts.items(), key=lambda x: x[1], reverse=True)
        filtered = []
        for task_id, count in sorted_risks:
            task = self.data_manager.get_task(task_id)
            if task and not task.is_summary and not task.is_milestone:
                filtered.append((task_id, count, task))

        top_risks = filtered[:6]

        if not top_risks:
            empty = QLabel("No specific risk drivers identified among work tasks.")
            empty.setStyleSheet(
                f"color: {pal['text_muted']}; font-style: italic; border: none; padding: 8px;"
            )
            layout.addWidget(empty)
            return card

        # Build rows
        for i, (task_id, count, task) in enumerate(top_risks):
            pct = (count / iterations) * 100
            name = task.name if len(task.name) <= 45 else task.name[:42] + "…"

            # Severity color
            if pct > 80:
                sev_color = pal['danger']
                sev_label = "Critical"
            elif pct > 50:
                sev_color = pal['warning']
                sev_label = "High"
            else:
                sev_color = pal['info']
                sev_label = "Medium"

            # Bar width proportional to percentage
            bar_pct = min(int(pct), 100)

            row_html = f"""
            <div style="padding: 8px 0; border-bottom: 1px solid {pal['card_border']};">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span style="color: {pal['text']}; font-size: 12px; font-weight: 600;">
                        {i+1}. {name}
                    </span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="color: {sev_color}; font-weight: bold; font-size: 13px; margin-right: 8px;">
                        {pct:.1f}%
                    </span>
                    <span style="color: {pal['text_muted']}; font-size: 11px;">
                        on critical path &nbsp;·&nbsp;
                    </span>
                    <span style="color: {sev_color}; font-size: 11px; font-weight: 600;">
                        {sev_label}
                    </span>
                </div>
            </div>
            """

            row_label = QLabel(row_html)
            row_label.setStyleSheet("border: none;")
            row_label.setWordWrap(True)
            layout.addWidget(row_label)

            # Visual bar
            bar_frame = QFrame()
            bar_frame.setFixedHeight(4)
            bar_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {pal['card_border']};
                    border-radius: 2px;
                    border: none;
                }}
            """)
            bar_inner = QFrame(bar_frame)
            bar_width = max(bar_pct * 3, 4)  # scale bar
            bar_inner.setFixedHeight(4)
            bar_inner.setFixedWidth(bar_width)
            bar_inner.setStyleSheet(f"""
                QFrame {{
                    background-color: {sev_color};
                    border-radius: 2px;
                    border: none;
                }}
            """)
            layout.addWidget(bar_frame)

        return card

    def _build_summary_card(self, results, pal) -> QFrame:
        """Textual summary card."""
        card = _make_card(pal)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        title = QLabel("📝  Summary")
        title.setStyleSheet(
            f"color: {pal['text']}; font-size: 13px; font-weight: bold; border: none;"
        )
        layout.addWidget(title)

        def fmt(d):
            return d.strftime("%d %b %Y") if d else "N/A"

        lines = []
        lines.append(
            f"Based on <b>{results.get('iterations', 0):,}</b> simulation runs, "
            f"the project has a <b>50% chance</b> of completing by "
            f"<b style='color:{pal['p50_color']}'>{fmt(results.get('p50_date'))}</b>."
        )
        lines.append(
            f"For an <b>80% confidence</b> commitment, plan toward "
            f"<b style='color:{pal['p80_color']}'>{fmt(results.get('p80_date'))}</b>."
        )

        stdev = results.get('stdev_days', 0)
        if stdev > 5:
            lines.append(
                f"<br>⚠ <b style='color:{pal['warning']}'>High variance detected</b> "
                f"(σ = {stdev:.1f} days) — the schedule has significant uncertainty. "
                f"Focus on the top risk drivers to reduce this."
            )
        elif stdev > 0:
            lines.append(
                f"<br>✅ <b style='color:{pal['success']}'>Low variance</b> "
                f"(σ = {stdev:.1f} days) — the schedule is relatively stable."
            )

        body = QLabel("<br>".join(lines))
        body.setWordWrap(True)
        body.setStyleSheet(
            f"color: {pal['text']}; font-size: 12px; line-height: 1.5; border: none; padding: 4px 0;"
        )
        layout.addWidget(body)

        return card
