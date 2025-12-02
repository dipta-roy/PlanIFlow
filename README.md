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
- **Inline Editing**: Directly edit task properties within the table for quick modifications.
- **Context Menus**: Right-click on tasks for quick access to actions like edit, delete, indent, and outdent.
- **Hierarchical Tasks**: Create summary tasks and sub-tasks.
- **Resource Management**: Allocate resources, track utilization, and manage billing rates.
- **Dynamic Gantt Charts**: Real-time visualization with dependencies
- **Excel Import/Export**: Share plans via Excel files
- **JSON Import/Export**: Save and load projects in JSON format.
- **PDF Import/Export**: Save and load projects in PDF format.
- **Calendar Management**: Custom work hours and holidays
- **Dark Mode**: Toggle between light and dark themes
- **Resource Allocation Tracking**: Detect over-allocation
- **Project Dashboard**: Overview of project metrics, including total project cost.
- **Task Filtering**: Search and filter by resource, status, or name
- **Resource Billing Rate Fix**: Corrected an issue where updating resource billing rates was not properly reflected in the resource table and total amount calculations.
- **Total Project Cost in Dashboard**: The dashboard now displays the total estimated cost of the project, calculated from all assigned resources and their billing rates.

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
main.py (Entry)
   ↓
ui_main.py (MainWindow: Tabs, Menus, TreeView)
   ├── ui_tasks.py (Task Tree: Hierarchy, Dependencies)
   ├── ui_task_dialog.py.py (Task Settings)
   ├── gantt_chart.py (Gantt: Arrows, Critical Toggle)
   ├── ui_resources.py (Resource Table: Allocation, Warnings)
   ├── ui_dashboard.py (Metrics: Charts, Status Cards)
   ├── ui_project_settings.py (Settings Dialog)
   ├── ui_calendar_settings_dialog.py (Calendar Settings Dialog)
   ├── ui_resource_dialog.py (Resource Dialog)
   └── ui_menu_toolbar.py (Actions, Shortcuts)
Data Layer:
   ├── data_manager.py (Tasks/Resources: CPM, Costs)
   ├── calendar_manager.py (Holidays, Working Days)
   ├── settings_manager_new_del.py (Settings: Duration, Themes)
   └── settings_manager.py (Deprecated: Old Settings)
I/O:
   ├── pdf_exporter.py (PDF report Export)
   └── exporter.py (JSON/Excel: Full State)
Utilities:
   ├── ui_helpers.py (Icons, Paths)
   ├── ui_delegates.py (Editors: Date, Resource)
   ├── themes.py (Light/Dark)
   ├── app_images.py (Base64 Images)
   └── __init__.py (Empty)
```

## 🚀 Getting Started

### Prerequisites

- Windows Operating System
- Python 3.10 or higher

### Installation

#### Windows (One-Click)
```bat
git clone https://github.com/dipta-roy/PlanIFlow.git
cd PlanIFlow
install.bat
run.bat
```

#### macOS/Linux (Terminal)
```bash
git clone https://github.com/dipta-roy/PlanIFlow.git
cd PlanIFlow
pip install -r requirements.txt
python main.py
```

### Running the Application

Once the installation is complete, you can run the application by executing the `run.bat` script:

```bash
run.bat
```

This script will activate the virtual environment and start the application.

### Using Standalone Executables

#### Windows (.exe)
Download PlanIFlow `PlanIFlow_1.6.1.zip`:
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
Run: PlanIFlow_1.6.1.exe
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
| `quick-start.bat`   | A menu-driven script to quickly run any of the other scripts.                  |
| `install.bat`       | One-click installer for first-time users.                                      |
| `run.bat`           | Runs the application, creating a virtual environment and installing dependencies if needed. |
| `build.bat`         | Builds a standalone `.exe` file of the application.                            |
| `setup.bat`         | Sets up the virtual environment and installs dependencies.                     |
| `clean.bat`         | Cleans up the project directory by removing build artifacts and cache files.   |

## 🛠️ Building from Source

To build a standalone executable from the source code, you can use the `build.bat` scripts.

-   **`build.bat`**: Creates a single `.exe` file in the `dist` folder. This is the easiest way to create a distributable version of the application.

## 📂 Project Structure

```
PlanIFlow_v1.6.1\
├───build.bat
├───clean.bat
├───install.bat 
├───quick-start.bat
├───run.bat
├───setup.bat 
├───README.md
├───requirements.txt
├───__init__.py
├───app_images.py
├───calendar_manager.py
├───data_manager.py
├───exporter.py
├───gantt_chart.py
├───main.py
├───settings_manager_new_del.py
├───settings_manager.py
├───themes.py
├───ui_dashboard.py
├───ui_delegates.py
├───ui_helpers.py
├───ui_main.py
├───ui_menu_toolbar.py
├───ui_project_settings.py
├───ui_resources.py
├───ui_tasks.py
├───pdf_exporter.py
├───version_info.txt
├───images\
│  └───logo.ico
└───sample\
   ├───Project_Replica_bkp.json
   └───Project_Replica.xlsx
```

**Note:** The `build` and `dist` directories are generated during the build process and contain the compiled application and its dependencies. 

## 🐛 Troubleshooting

-   **Application does not start**: Ensure you have Python 3.10 or higher installed and that it is in your system's PATH. Try running `install.bat` again.
-   **`ModuleNotFoundError`**: If you get an error about a missing module, run `pip install -r requirements.txt` in the activated virtual environment.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## 📈 Security and Distribution

- **Security Assessment**: [Full Report](https://github.com/dipta-roy/PlanIFlow/blob/main/SECURITY.md) – **Low Risk** (offline, safe I/O).
- **Distribution**: Use signed builds; include .cer for trust.
- **VirusTotal Report**: [VirusTotal Report](https://www.virustotal.com/gui/file/cc460de0c162b1aa43bc84440507c4ad7eced22fbf15edae915607a5417793c8) - May detect as **false positive**, add to Exclusion if necessary.

## 🙏 Acknowledgments

- Built by [Dipta Roy](https://github.com/dipta-roy).
- Icons: [Flaticon](https://flaticon.com).
- Thanks to PyQt6 & Matplotlib communities.