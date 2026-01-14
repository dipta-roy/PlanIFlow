# 📊 PlanIFlow - Project Planner

![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Framework](https://img.shields.io/badge/Framework-PyQt6-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

PlanIFlow is an **Offline-First**, standalone desktop application for project planning and management, offering features similar to professional project management tools. It operates primarily offline, with optional network connectivity solely for secure updates.

## 📝 Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Running the Application](#running-the-application)
  - [Using Standalone Executables](#using-standalone-executables)
- [Usage](#usage)
  - [Creating a New Project](#creating-a-new-project)
  - [Adding Tasks and Resources](#adding-tasks-and-resources)
  - [Managing Tasks](#managing-tasks)
  - [Resource Exception Days](#resource-exception-days)
  - [Kanban Board](#kanban-board)
  - [Gantt Chart](#gantt-chart)
  - [Dashboard](#dashboard)
  - [Importing and Exporting Data](#importing-and-exporting-data)
  - [Project Baselining](#project-baselining)
- [Monte Carlo Risk Analysis](#monte-carlo-risk-analysis)
- [Screenshots](#screenshots)
- [Shortcuts](#shortcuts)
- [Batch Scripts](#batch-scripts)
- [Building from Source](#building-from-source)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Security and Distribution](#security-and-distribution)
- [Secure Auto-Update System](#secure-auto-update-system)
- [Acknowledgments](#acknowledgments)

## ✨ Features

- **Offline-First Architecture**: Your data stays on your machine. Network is used only for updates.
- **Modular UI Architecture**: A well-organized and extensible user interface, making it easier to navigate and manage project elements.
- **Project Settings Management**: Dedicated interface for configuring project-specific settings and preferences.
- **Task Management**: Create, edit, delete tasks with dependencies (FS, SS, FF, SF + Lag).
- **Hierarchical Tasks**: Create summary tasks and sub-tasks.
- **Inline Editing**: Directly edit task properties within the table for quick modifications.
- **Context Menus**: Right-click on tasks for quick access to actions like edit, delete, indent, and outdent.
- **Task Filtering**: Search and filter by resource, status, or name.
- **Calendar Management**: Custom work hours and recurring holidays (automatically applied within the project timeline).
- **Resource Management**: Allocate resources, track utilization, and manage billing rates.
- **Resource Allocation Tracking**: Detect over-allocation.
- **Resource Exception**: Resources can now have exception days (holidays/leaves) that exclude them from work on specific dates.
- **Multi-Currency Support**: Global setting for project-wide currency (USD, EUR, GBP, etc.) reflected in dashboard, resource management, and all exports.
- **Project Baselining**: Create up to 11 project snapshots. Compare current progress against baselines to track schedule and cost variances.
- **Monte Carlo Risk Analysis**: Accurately forecast completion dates and identify high-risk tasks through statistical simulations.
- **Duration Unit Selection**: Switch between 'Days' and 'Hours' for granular task planning.
- **Standard Dependency Notation**: Support for FS, SS, FF, SF relationships with custom lag/lead times.
- **Dynamic Gantt Charts**: Real-time visualization of your project timeline with zoom and interactive tooltips.
- **Rich Export Capabilities**: Professional reports in Excel, PDF, and JSON formats.
- **Undo/Redo Support**: Full history for all project modifications.
- **Interactive Kanban Board**: Visual task management with drag-and-drop cards organized by status (To Do, In Progress, Delayed, Blocked, Completed). Includes task-level and resource-level filtering.
- **Secure Auto-Update**: Hassle-free updates with SHA-256 integrity verification.
- **Earned Value Management (EVM)**: Track project performance using industry-standard metrics (CPI, SPI, EV, PV, AC). Includes health summaries and Excel export.
- **Smart Project Diagnosis**: One-click analysis combining Risk, Schedule, and Cost health checks into a unified status report.
- **Dark Mode**: Fully supported dark theme for reduced eye strain.

## 🛠️ Technologies Used

- Python
- PyQt6
- Pandas
- Matplotlib
- Openpyxl
- Reportlab
- Numpy
- Pillow
- cx_Freeze
- Jsonschema
- Python-dateutil
- Requests (Updater only)

## Architecture Overview

The application follows a modular architecture, separating data management, UI, and business logic into distinct components.
- **Core**: Python + PyQt6
- **Data**: In-memory Pandas DataFrames, persisted to JSON/Excel.
- **Security**: Strict input validation, no database server, no telemetry.
- **Network**: Restricted to `updater.py` for GitHub Releases checks.

## 🚀 Getting Started

### Prerequisites

- Windows Operating System
- Python 3.11 or higher

### Running the Application

#### Windows:

Once the installation is complete, you can run the application by executing the `run.bat` script.

```bash
run.bat
```

or 

Use the `build_msi.bat` script to generate an `PlanIFlow_Setup_2.2.0.msi` file.

```bash
build_msi.bat
```

#### Linux/Mac

1. Create a virtual environment: 
```bash
python3 -m venv venv
```

2. Activate the virtual environment: 
```bash
source venv/bin/activate
```

3. Install dependencies: 
```bash
pip install -r requirements.txt
```

4. Run the application: 
```bash
python3 main.py 
```

### Using Standalone Executables

#### Windows (.exe)

Download Code Verification Certificate: [Dipta Roy - Code Verification Certificate](https://github.com/dipta-roy/dipta-roy.github.io/blob/main/downloads/Code%20Verifying%20Certificates.zip).
```
- HOW TO TRUST

1. Download certficate from above link.
2. Right-click `Signed_By_Dipta_CodeSigningPublicKey.cer` → "Install Certificate"
3. Select "Local Machine" (requires admin)
4. Choose "Place all certificates in the following store"
5. Click "Browse" → Select "Trusted Root Certification Authorities"
6. Click "Next" → "Finish"

- VERIFY APPLICATION AUTHENTICITY

1. To confirm the application is genuine, open its Properties.
2. Go to the Digital Signatures tab.
3. Select "Signed_By_Dipta" from the Embedded Signatures list, then choose Details.
4. In the General tab, you should see the message "This digital signature is OK."
```

Once verified,
```
Run PlanIFlow_2.2.0.msi and install the application.
```

## 💻 Usage

### Creating a New Project

- Go to `File > New Project` to start a new project.
- You can name your project by going to `File > Rename Project`.

### Adding Tasks and Resources

- **Add Resources**: Click the `👤 Add Resource` button in the toolbar.
- **Add Tasks**: Click the `➕ Add Task` button to create a new task.
- **Sub-tasks**: Select a task and click `➕ Add Subtask` to create a child task.

### Managing Tasks

- **Inline Editing**: Double-click on a task field to edit.
- **Context Menu**: Right-click on any task row for more options.
- **Indent/Outdent**: Use `Tab` and `Shift+Tab` to create hierarchy.

### Resource Exception Days

- **Single Day**: A specific date when the resource is unavailable.
- **Date Range**: A continuous period (e.g., vacation).

### Kanban Board

The **Kanban Board** tab provides an interactive, visual way to manage tasks organized by status:

- **Status Columns**:
  - 📝 **To Do**: Tasks that haven't started yet
  - 🚀 **In Progress**: Tasks currently being worked on
  - ⚠️ **Delayed**: Tasks past their end date and not complete
  - 🚫 **Blocked**: Tasks with blocking dependencies or issues
  - ✅ **Completed**: Finished tasks (100% complete)

- **Task Cards**: Each card displays:
  - Task name, ID, and WBS
  - Start and end dates
  - Duration
  - Progress percentage
  - Assigned resources
  - Notes preview

- **Interactions**:
  - **Click** any card to view full details and edit notes
  - **Drag and drop** cards between columns (visual organization)
  - **Filter by View**: Show all tasks, task-level only, or summary tasks only
  - **Filter by Resource**: View tasks assigned to specific resources

### Gantt Chart

The **Gantt Chart** tab provides a visual representation of your project timeline.
- **Show Critical Path**: Check the checkbox for red highlights on zero-slack tasks.

### Dashboard

The **Dashboard** tab gives you a high-level overview of your project, including:
-   Project dates, task counts, and completion percentages.
-   **Smart Project Diagnosis**: Run a comprehensive health check that integrates Monte Carlo risk data, schedule deadlines, and EVM metrics to provide a plain-English status report.
-   **Total Project Cost** with dynamic currency formatting.
-   Detailed budget and cost tables per resource.
-   Monthly expense breakdown visualization.

### Importing and Exporting Data

- **JSON**: Recommended format.
- **Excel**: For sharing with non-users.
- **PDF**: For reporting.

### Project Baselining

Baselines allow you to capture snapshots of your project at different milestones.
-   **Capacity**: Store up to 11 unique baselines per project.
-   **Create**: `Settings > Baselines > Set Baseline...`
-   **Compare**: `Settings > Baselines > View Baseline Comparison`.
-   **Visualize**: Color-coded variance in start/end dates, duration, and completion.

## 🎲 Monte Carlo Risk Analysis

The Monte Carlo analysis feature forecasts project completion dates under uncertainty.

- **How to Use**:
  - Go to the `Risk Analysis` tab.
  - Set **Iterations** (e.g., 1000).
  - Click **"Run Analysis"**.

- **Results**:
  - **Confidence Table**: P50 (Median), P80 (Low Risk), P90 (High Confidence).
  - Top Risk Drivers: Tasks most frequently on the critical path.
  - Completion Date Distribution: Histogram of possible completion dates.

## 📈 Earned Value Management (EVM) Analysis

Track your project's cost and schedule performance with professional precision.

- **Metrics**: Real-time calculation of CPI, SPI, CV, SV, EAC, and VAC.
- **Health Summary**: Automatic executive summary explains project status in plain English (e.g., "Over Budget but Ahead of Schedule").
- **Visuals**: Charts comparing Planned vs. Actual cost.
- **Excel Export**: Detailed export with multiple sheets:
  - **Executive Summary**: High-level KPI dashboard.
  - **Task Metrics**: Detailed breakdown per task.
  - **Glossary**: Definitions of all EVM terms for stakeholders.

## Screenshots

| Task List | Edit Task |
| --- | --- |
| ![Task List](./screenshot/Task_List.png) | ![Edit Task](./screenshot/Edit%20Task.png) |

| Gantt Chart | Gantt Chart With Critical Path |
| --- | --- |
| ![Gantt Chart](./screenshot/Gantt%20Chart.png) | ![Gantt Chart With Critical Path](./screenshot/Gantt%20Chart%20With%20Critical%20Path.png) |

| Dashboard | Resource |
| --- | --- |
| ![Dashboard](./screenshot/Dashboard.png) | ![Resource](./screenshot/Resource.png) |

| Project Baseline | Set Project Baseline |
| --- | --- |
| ![Project Baseline](./screenshot/Project%20Baseline.png) | ![Set Project Baseline](./screenshot/Set%20Project%20Baseline.png) |

| Risk Analysis | EVM Analysis |
| --- | --- |
| ![Risk Analysis](./screenshot/Risk%20Analysis.png) | ![EVM Analysis](./screenshot/EVM%20Analysis.png) |

| Kanban Board | Edit Kanban Tile |
| --- | --- |
| ![Kanban Board](./screenshot/Kanban%20Board.png) ![Edit Kanban Tile](./screenshot/Kanban%20Tile%20Edit.png) |

| Project Settings | Calendar Settings |
| --- | --- |
| ![Project Settings](./screenshot/Project%20Settings.png) ![Calendar Settings](./screenshot/Calendar%20Settings.png) |

| Holidays Settings | Interface Settings |
| --- | --- |
| ![Project Settings](./screenshot/Holidays%20Settings.png) ![Risk Analysis](./screenshot/Interface%20Settings.png) |


## ⌨️ Shortcuts

| Shortcut         | Action                  |
| ---------------- | ----------------------- |
| `Ctrl+T`         | Add Task                |
| `Ctrl+M`         | Add Milestone		     |
| `Ctrl+Shift+T`   | Add Subtask             |
| `Ctrl+N`         | New Project             |
| `Ctrl+O`         | Open Project            |
| `Ctrl+S`         | Save Project            |
| `F5`             | Refresh All             |
| `Tab`            | Indent Task             |
| `Shift+Tab`      | Outdent Task            |
| `Space`          | Toggle Expand/Collapse  |
| `+`              | Expand Selected         |
| `-`              | Collapse Selected       |
| `Ctrl+B`         | Bold Selected       	 |
| `Ctrl+I`         | Italics Selected        |
| `Ctrl+U`         | Underline Selected      |
| `Ctrl+Z`         | Undo                    |
| `Ctrl+Y`         | Redo                    |
| `Ctrl++`         | Zoom In (Gantt)         |
| `Ctrl+-`         | Zoom Out (Gantt)        |

## 🪟 Batch Scripts

| Script              | Purpose                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| `run.bat`           | Runs the application, installing dependencies if needed. |
| `build.bat`         | Builds a standalone `.exe` (PyInstaller).                            |
| `build_msi.bat`     | Builds a professional `.msi` installer using `cx_Freeze` + `PyInstaller` wrapper. |
| `clean.bat`         | Cleans up build artifacts.   |

## 🛠️ Building from Source

To build a standalone executable or a professional installer from the source code, you can use the provided batch scripts.

-   **`build.bat`**: Creates a single `.exe` file in the `dist` folder.
-   **`build_msi.bat`**: RECOMMENDED. Creates a professional Windows Installer (`.msi`). This method is more compatible with antivirus software.

### Building the MSI Installer

1. Run `build_msi.bat` from the project root.
2. The script will automatically:
   - Create/Update virtual environment.
   - Install dependencies.
   - Compile the application.
   - Package everything into a `.msi` file located in the `dist/` folder.

## 📂 Project Structure

| Path                                     | Description                                                                                             |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `main.py`                                | Main entry point of the application.                                                                    |
| `updater.py`                             | Handles secure updates (check, download, hash verification).                                            |
| `data_manager/`                          | Core logic for tasks, resources, validation, and Monte Carlo.                                           |
| `ui/`                                    | PyQt6 widgets, dialogs, and main window logic.                                                          |
| `installer/`                             | Scripts for building the MSI installer.                                                                 |

## 🐛 Troubleshooting

-   **Resource Files Not Found**: Check `sys._MEIPASS` handling if building custom specs.
-   **App does not start**: Ensure Python 3.11+ is in PATH.
-   **`ModuleNotFoundError`**: Run `pip install -r requirements.txt`.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## 📈 Security and Distribution

- **Security Assessment**: [Full Report](https://github.com/dipta-roy/PlanIFlow/blob/main/SECURITY.md) – **Low Risk** (Secure Design).
- **VirusTotal Report for MSI Installer**: [VirusTotal Report](https://www.virustotal.com/gui/file/1bee77abd9f0b187b0535eaaa87729750d16ba5b1116884dd42fac829257612a)
- **Offline-First**: No data leaves your machine.
- **Secure Updates**: HTTPS + SHA256 Hash Verification.
- **Input Validation**: Strict limits on task counts (10k) and string lengths (250) to prevent DoS.

### Reasons for False Positive Detections:
- **PyInstaller Bundling**: Embeds Python runtime and libraries into a single EXE, which heuristic scanners may flag.
- **Dynamic Loading**: Runtime imports can trigger behavior monitoring.
- **Suspicious Behaviors**: Updater network activity (clean `requests` usage) can be flagged as "network potential".
- **Mitigation**: We digitally sign our builds. Please verify the signature as described in "Getting Started".

## 🔄 Secure Auto-Update System

PlanIFlow includes a secure, built-in auto-update mechanism.

### How it works:
1.  **Check**: Periodically checks [GitHub Releases](https://github.com/dipta-roy/PlanIFlow/releases) securely via HTTPS.
2.  **Download**: Downloads the official MSI installer.
3.  **Verify**: 
    -   **Hash Verification**: Calculates SHA256 hash of the download.
    -   **Compare**: Matches against the official `.sha256.txt` record.
    -   **Abort**: If hashes mismatch, the file is deleted immediately.
4.  **Install**: Installs the update silently and restarts.

### Manual Check:
Go to **Help > Check for Updates**.

## 🙏 Acknowledgments

- Icons: [Flaticon](https://flaticon.com).
- Thanks to PyQt6 & Matplotlib communities.

Built by [Dipta Roy](https://github.com/dipta-roy) with ❤️.
