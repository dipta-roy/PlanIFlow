# 📊 PlanIFlow - Project Planner

![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Framework](https://img.shields.io/badge/Framework-PyQt6-blue.svg)

PlanIFlow is a fully offline, standalone desktop application for project planning and management, offering features similar to Microsoft Project.

## 📝 Table of Contents

- [Features](#-features)
- [Technologies Used](#️-technologies-used)
- [Architecture Overview](#-architecture-overview)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Usage](#-usage)
  - [Creating a New Project](#creating-a-new-project)
  - [Adding Tasks and Resources](#adding-tasks-and-resources)
  - [Managing Tasks](#managing-tasks)
  - [Gantt Chart](#gantt-chart)
  - [Dashboard](#dashboard)
  - [Importing and Exporting Data](#importing-and-exporting-data)
- [Shortcuts](#️-shortcuts)
- [Batch Scripts](#-batch-scripts)
- [Building from Source](#️-building-from-source)
- [License](#-license)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Security and Distribution](#-security-and-distribution)
- [Acknowledgments](#-acknowledgments)

## ✨ Features

- **Modular UI Architecture**: A well-organized and extensible user interface, making it easier to navigate and manage project elements.
- **Project Settings Management**: Dedicated interface for configuring project-specific settings and preferences.
- **Task Management**: Create, edit, delete tasks with dependencies
- **Hierarchical Tasks**: Create summary tasks and sub-tasks.
- **Inline Editing**: Directly edit task properties within the table for quick modifications.
- **Context Menus**: Right-click on tasks for quick access to actions like edit, delete, indent, and outdent.
- **Task Filtering**: Search and filter by resource, status, or name
- **Calendar Management**: Custom work hours
- **Resource Management**: Allocate resources, track utilization, and manage billing rates.
- **Resource Allocation Tracking**: Detect over-allocation
- **Resource Exception**: Resources can now have exception days (holidays/leaves) that exclude them from work on specific dates. This affects their billing and effort calculations.
- **Total Project Cost in Dashboard**: The dashboard now displays the total estimated cost of the project, calculated from all assigned resources and their billing rates.
- **Dynamic Gantt Charts**: Real-time visualization with dependencies
- **Project Dashboard**: Overview of project metrics, including total project cost.
- **Excel Import/Export**: Share plans via Excel files
- **JSON Import/Export**: Save and load projects in JSON format.
- **PDF Import/Export**: Save and load projects in PDF format.
- **Dark Mode**: Toggle between light and dark themes

## 🛠️ Technologies Used

- Python
- PyQt6
- Pandas
- Matplotlib
- Openpyxl
- Reportlab
- Numpy

## Architecture Overview

```
PlanIFlow 1.7.0/
├───__init__.py                # Marks the directory as a Python package.
├───main.py                    # The main entry point of the application, responsible for initializing the GUI and loading initial data.
├───prepare_spec.py            # Script used for preparing the PyInstaller spec file, possibly for custom build configurations.
├───calendar_manager/          # Manages project calendars, including working days, holidays, and custom work schedules.
│   ├───__init__.py            # Marks the calendar_manager directory as a Python package.
│   └───calendar_manager.py    # Core logic for managing holidays, working days, and work schedules.
├───constants/                 # Defines global constants and application-wide configurations.
│   ├───__init__.py            # Marks the constants directory as a Python package.
│   ├───app_images.py          # Contains Base64 encoded application images and icons used throughout the UI.
│   └───constants.py           # Defines global constants and configuration values for the application.
├───data_manager/              # Handles all data management operations, including tasks, resources, and critical path calculations.
│   ├───__init__.py            # Marks the data_manager directory as a Python package.
│   ├───manager.py             # The core data manager, handling tasks, resources, critical path method (CPM) calculations, and cost management.
│   └───models.py              # Defines data models for tasks, resources, and other project entities.
├───exporter/                  # Manages the import and export of project data to various formats.
│   ├───__init__.py            # Marks the exporter directory as a Python package.
│   ├───exporter.py            # Handles the import and export of project data in formats like JSON and Excel.
│   └───pdf_exporter.py        # Responsible for exporting project reports and Gantt charts to PDF format.
├───settings_manager/          # Manages application settings and user preferences.
│   ├───__init__.py            # Marks the settings_manager directory as a Python package.
│   └───settings_manager.py    # Manages application settings, such as duration units and theme preferences.
└───ui/                        # Contains all user interface components and related logic.
    ├───__init__.py            # Marks the ui directory as a Python package.
    ├───gantt_chart.py         # Implements the dynamic Gantt chart visualization, including task dependencies and critical path highlighting.
    ├───themes.py              # Manages the application's visual themes (e.g., light and dark mode).
    ├───ui_calendar_settings_dialog.py # Defines the dialog for configuring project calendar settings.
    ├───ui_dashboard.py        # Creates the project dashboard interface, displaying key metrics, charts, and status cards.
    ├───ui_delegates.py        # Contains custom delegates for various UI editors, such as date pickers and resource selectors.
    ├───ui_duration_unit_dialog.py # Defines the dialog for setting duration units (e.g., days, hours).
    ├───ui_file_manager.py     # Manages file-related operations within the UI, such as opening and saving project files.
    ├───ui_helpers.py          # Provides utility functions and helper methods for UI-related tasks, suchs as icon loading and path management.
    ├───ui_main.py             # The main window of the user interface, containing tabs, menus, and the primary tree view.
    ├───ui_menu_toolbar.py     # Handles actions and shortcuts for the application's menu and toolbar.
    ├───ui_project_settings.py # Defines the dialog for configuring general project settings.
    ├───ui_resource_dialog.py  # Defines the dialog for managing and editing resources.
	├── ui_resource_exceptions_widget.py  # Exception management widget
    ├───ui_resources.py        # Implements the resource table, displaying resource allocation and warnings.
    ├───ui_task_dialog.py      # Defines the dialog for managing and editing individual tasks.
    ├───ui_task_manager.py     # Manages task-related operations and interactions within the UI.
    ├───ui_tasks.py            # Implements the task tree view, handling task hierarchy and dependencies.
    ├───ui_tree_view_manager.py # Manages the overall behavior and interactions of the tree view widgets.
    └───ui_view_manager.py     # Manages the different views and their transitions within the application.
```

## 🚀 Getting Started

### Prerequisites

- Windows Operating System
- Python 3.10 or higher

### Running the Application

#### Windows:

Once the installation is complete, you can run the application by executing the `run.bat` script. This script will activate the virtual environment and start the application.

```bash
run.bat
```

or 

Use the `build.bat` script to generate an `PlayIFlow 1.7.0.exe` file which will be saved at `dist/` folder.

```bash
build.bat
```

#### Linux/Mac

To run this application on Linux or macOS, follow these steps:
1. Open your terminal.

2. Create a virtual environment: 
```bash
python3 -m venv venv
```

3. Activate the virtual environment: 
```bash
source venv/bin/activate
```

4. Install dependencies: 
```bash
pip install -r requirements.txt
```

5. Run the application: 
```bash
python3 main.py 
```

### Using Standalone Executables

#### Windows (.exe)
Download PlanIFlow `PlanIFlow_1.7.0.zip`:
Download Code Verification Certificate: [Dipta Roy](https://github.com/dipta-roy/dipta-roy.github.io/blob/main/downloads/Code%20Verifying%20Certificates.zip).
```
- HOW TO TRUST

1. Unzip the distribution package.
2. Double-click: Signed_By_Dipta_CodeSigningPublicKey.cer
3. Click: "Open" -> "Install Certificate..."
4. Select: "Current User"
5. Choose: "Place all certificates in the following store"
6. Browse -> "Trusted People" -> OK -> Next -> Finish

- VERIFY APPLICATION AUTHENTICITY

1. To confirm the application is genuine, open its Properties.
2. Go to the Digital Signatures tab.
3. Select "Signed_By_Dipta" from the Embedded Signatures list, then choose Details.
4. In the General tab, you should see the message "This digital signature is OK." which confirms the app was signed by Dipta using the listed certificates.
```

Once verified,
```
Run: PlanIFlow_1.7.0.exe
```

## 💻 Usage

### Creating a New Project

- Go to `File > New Project` to start a new project.
- You can name your project by going to `File > Rename Project`.

### Adding Tasks and Resources

- **Add Resources**: Click the `👤 Add Resource` button in the toolbar to add resources like team members or equipment. You can now also specify a billing rate for each resource.
- **Add Tasks**: Click the `➕ Add Task` button to create a new task. You can set the start and end dates, assign resources, and add notes.
- **Sub-tasks**: Select a task and click `➕ Add Subtask` to create a child task.

### Managing Tasks

- **Inline Editing**: Double-click on a task field (e.g., Task Name, Start Date, End Date, Duration, % Complete, Dependencies, Resources, Notes) to directly edit its value. Press `Enter` to save changes or `Esc` to cancel.
  - **Date Fields**: Use the calendar dropdown for Start Date and End Date.
  - **Resources Field**: Select from a dropdown of existing resources or type new ones.
  - **Status and ID**: These fields are automatically populated and cannot be edited directly.
- **Context Menu**: Right-click on any task row to bring up a context menu with options such as editing the task, deleting it, indenting, or outdenting.
- **Indent/Outdent**: Use the `Tab` and `Shift+Tab` keys to indent and outdent tasks, creating a task hierarchy.

### Resource Exception Days

- **Single Day**: A specific date when the resource is unavailable
- **Date Range**: A continuous period when the resource is unavailable (e.g., vacation)

### Gantt Chart

The **Gantt Chart** tab provides a visual representation of your project timeline. Dependency lines are drawn between tasks, and the chart is updated in real-time.
- **Show Critical Path**: Check the checkbox → red highlights for zero-slack tasks.

### Dashboard

The **Dashboard** tab gives you a high-level overview of your project, including:

-   Project start and end dates
-   Total number of tasks
-   Overall project completion percentage
-   Task status breakdown
-   **Total Project Cost**: A summary of the estimated cost across all resources.
- 	Scroll for Budget and cost tables.

### Importing and Exporting Data

- **JSON**: Save and load your projects using the `.json` format. This is the recommended format for saving your work.
- **Excel**: Import and export your projects to and from Excel files. This is useful for sharing your project with others who may not have the application.
- **PDF**: Export your projects to and from PDF report.

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

## 🪟 Batch Scripts

This project includes a set of batch scripts to automate common tasks on Windows:

| Script              | Purpose                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| `run.bat`           | Runs the application, creating a virtual environment and installing dependencies if needed. |
| `build.bat`         | Builds a standalone `.exe` file of the application.                            |
| `clean.bat`         | Cleans up the project directory by removing build artifacts and cache files.   |

## 🛠️ Building from Source

To build a standalone executable from the source code, you can use the `build.bat` scripts.

-   **`build.bat`**: Creates a single `.exe` file in the `dist` folder. This is the easiest way to create a distributable version of the application.

## 📂 Project Structure

```
PlanIFlow 1.7.0/
├───__init__.py
├───build.bat
├───clean.bat
├───main.py
├───prepare_spec.py
├───README.md
├───requirements.txt
├───run.bat
├───SECURITY.md
├───version_info.txt
├───calendar_manager/
│   ├───__init__.py
│   └───calendar_manager.py
├───constants/
│   ├───__init__.py
│   ├───app_images.py
│   └───constants.py
├───data_manager/
│   ├───__init__.py
│   ├───manager.py
│   └───models.py
├───exporter/
│   ├───__init__.py
│   ├───exporter.py
│   └───pdf_exporter.py
├───images/
│   ├───logo_lg.ico
│   ├───logo.ico
│   └───Logo.png
├───sample/
│   └───Project_Replica.json
├───settings_manager/
│   ├───__init__.py
│   └───settings_manager.py
└───ui/
    ├───__init__.py
    ├───gantt_chart.py
    ├───themes.py
    ├───ui_calendar_settings_dialog.py
    ├───ui_dashboard.py
    ├───ui_delegates.py
    ├───ui_duration_unit_dialog.py
    ├───ui_file_manager.py
    ├───ui_helpers.py
    ├───ui_main.py
    ├───ui_menu_toolbar.py
    ├───ui_project_settings.py
    ├───ui_resource_dialog.py
    ├───ui_resource_exceptions_widget.py
    ├───ui_resources.py
    ├───ui_task_dialog.py
    ├───ui_task_manager.py
    ├───ui_tasks.py
    ├───ui_tree_view_manager.py
    └───ui_view_manager.py
```

**Note:** The `build` and `dist` directories are generated during the build process and contain the compiled application and its dependencies. 

## 🐛 Troubleshooting

-   **Resource Files Not Found (PyInstaller builds)**: If you encounter issues with the application not finding images or other data files when running a built executable, it might be related to how PyInstaller bundles resources. The application uses `sys._MEIPASS` to locate files in standalone executables. Ensure all necessary data directories (e.g., `images`, `constants`) are correctly included in the PyInstaller build process via `--add-data` flags in `build.bat`.
-   **Application does not start**: Ensure you have Python 3.10 or higher installed and that it is in your system's PATH.
-   **`ModuleNotFoundError`**: If you get an error about a missing module, run `pip install -r requirements.txt` in the activated virtual environment.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## 📈 Security and Distribution

- **Security Assessment**: [Full Report](https://github.com/dipta-roy/PlanIFlow/blob/main/SECURITY.md) – **Low Risk** (offline, safe I/O).
- **Distribution**: Use signed builds; include .cer for trust.
- **VirusTotal Report**: [VirusTotal Report](https://www.virustotal.com/gui/file/87dbdb9200511849ab607a0bca3986d91fb488c700d9d79611e94a8628a0018d) - May detect as **false positive**, add to Exclusion if necessary.

## 🙏 Acknowledgments

- Built by [Dipta Roy](https://github.com/dipta-roy).
- Icons: [Flaticon](https://flaticon.com).
- Thanks to PyQt6 & Matplotlib communities.