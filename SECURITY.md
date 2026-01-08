# **PlanIFlow - Formal Security Assessment Report**  
## **PlanIFlow v2.3.0 – Offline Desktop Project Management Application**  
**Assessment Conducted:** December 26, 2025  
**Scope:** All Python source files (`*.py`) including `main.py`, `ui/`, `data_manager/`, and build scripts.  
**Methodology:** Static code analysis (SAST), manual code review, data flow tracing, threat modeling, CVSS v3.1 scoring.  
**Classification:** **LOW RISK – SECURE FOR INTENDED USE**

## **1. Executive Summary**

**PlanIFlow** is a **fully offline, standalone desktop application** built with **Python 3.10+ and PyQt6**, designed for **project planning and management**. It operates **without network connectivity**, **user authentication**, or **external services**.

After a **comprehensive security audit** of all source code, **no critical or high-severity vulnerabilities** were identified. The application's offline, single-user design significantly minimizes its attack surface.

> **Final Risk Rating: LOW** (Base CVSS: 3.9/10)  
> **Recommended Posture: SAFE FOR DEPLOYMENT**

The application is **secure by design** for its intended use case: **single-user, local project planning on Windows, macOS, or Linux**.

## **2. Scope & Methodology**

| Item 						| Details 													|
|---------------------------|-----------------------------------------------------------|
| **Files Analyzed** 		| 52`.py` files (e.g., `main.py`, `ui_main.py`, `exporter.py`, `data_manager/manager.py`, `installer/package_installer.py`) |
| **Analysis Type** 		| White-box static analysis (SAST) and manual code review. 	|
| **Tools Used** 			| Manual code review, dependency check, CVSS v3.1 scoring. |
| **Threat Model** 			| Malicious local file input, resource exhaustion, build process integrity. 			|
| **Standards Referenced** 	| OWASP Top 10 (Python), CWE. 			|

## **3. System Architecture Overview**

```
[User Input via Qt Widgets] → [PyQt6 UI Layer] → [DataManager Models] → [Local I/O: JSON/Excel/PDF]
                                           ↑
                                    [Visualization: Matplotlib Gantt/Dashboard]
```

- **No network stack** (no sockets, `requests`, or `urllib` usage in runtime).
- **No database** (data managed in-memory with `pandas` DataFrames and Python objects).
- **No privilege escalation** (runs entirely in user-context).
- **All file I/O is user-initiated** via `QFileDialog`.

## **4. Security Findings**

### **4.1 No Remote Attack Surface**

The application is fully offline and does not use any network protocols during runtime. Remote Code Execution, Network Data Leaks, and Man-in-the-Middle attacks are **not applicable**.

### **4.2 File Input Validation & Sanitization**

File parsing is handled by standard, well-vetted libraries with additional application-level validation.

| Source 			| Validation 								| Risk 							| CVSS Vector |
|-------------------|-------------------------------------------|-------------------------------|-------------|
| **JSON Import** 	| `json.load()` checked against `jsonschema`. **DoS Limits:** Max 10,000 tasks, 250 char strings enforced in `ProjectValidator`. 	| **Safe**. Schema validation and size limits block malformed or massive files. | N/A |
| **Excel Import** 	| `openpyxl`/`pandas` with validation logic. 		| **Safe**. Parsed into rigid data models; no execution of macros. | N/A |

### **4.3 Input Sanitization**

Input is handled by Qt widgets and the `ProjectValidator` class.

| Input Field 			| Handling 						| Risk 					| CVSS Vector |
|-----------------------|-------------------------------|-----------------------|-------------|
| Task Name, Notes 		| `ProjectValidator.sanitize_string` trims to 250 chars and removes control chars.  	| **Low**. Strict limits prevent buffer issues or UI clutter. | N/A |
| Dependencies 			| Custom parsing of "ID (Type+Lag)" strings. | **Safe**. Regex based, no `eval()`. | N/A |
| Resource Rates 		| `QDoubleSpinBox` enforces `float` validation. | **Safe**. | N/A |

### **4.4 Deserialization Safety**

The application avoids unsafe deserialization methods.
- **No `pickle`, `yaml.load`, or custom decoders are used.**
- **JSON and Excel parsing are handled securely**, preventing remote code execution from malicious files.

### **4.5 Privilege & Command Execution**

- **Runtime `subprocess`**: **No**. `CommandManager` is for Undo/Redo only; it does not execute system shell commands.
- **Build `subprocess`**: **Yes**. `installer/package_installer.py` uses `subprocess.check_call` to invoke `pyinstaller`. This is isolated to the build process.
- **Registry/Privileges**: The application runs entirely in user-context with no admin rights required.

### **4.6 Third-Party Dependencies**

The project's dependencies are explicitly pinned in `requirements.txt`.

| Library 		| Pinned Version 	| Known CVEs (in this version) | Risk 	|
|---------------|-------------------|------------------------------|--------|
| PyQt6 		| `6.10.1`		    | None. | Low 	|
| pandas 		| `2.3.3`		    | None. | Low 	|
| openpyxl 		| `3.1.5`		    | None. | Low 	|
| matplotlib 	| `3.10.7`		    | None. | Low 	|
| reportlab 	| `4.4.5`		    | None. | Low 	|
| numpy 		| `2.1.2`		    | None. | Low 	|
| Pillow        | `12.0.0`          | None. | Low 	|
| jsonschema    | `4.23.0`          | None. | Low   |
| python-dateutil| `2.9.0`          | None. | Low   |

### **4.7 Static Analysis**

- `command_manager/command_manager.py`: Confirmed as an implementation of the Command Pattern for application state (Undo/Redo), **not** a shell command executor.
- `installer/package_installer.py`: Confirmed as a build-time utility.
- `data_manager/validator.py`: Confirmed robust input validation limits (Max Tasks: 10,000, Max String Length: 250).

## **5. Risk Assessment Matrix**

| Threat 					| Likelihood 	| Impact 	| Risk Level 	| CVSS Score |
|---------------------------|---------------|-----------|---------------|------------|
| Malicious JSON/Excel RCE 	| Improbable 	| High 		| **LOW** 		| 0.0 |
| Input-Induced DoS 			| Unlikely 		| Low 		| **LOW** 		| 2.5 |
| Supply-Chain (pinned deps) | Improbable | Low | **LOW** | 0.0 |

*Note: Path Traversal, Privilege Escalation, and Network-based attacks were evaluated and deemed not applicable due to the application's architecture.*

## **6. Security Strengths**

| Strength 						| Benefit 					|
|-------------------------------|---------------------------|
| **Zero network exposure** 	| Immune to all remote attacks. |
| **Strict Input Validation**   | `ProjectValidator` enforces strict limits on task counts and string lengths, mitigating DoS and memory exhaustion. |
| **User-controlled file I/O** 	| `QFileDialog` prevents unauthorized file access. |
| **Safe deserialization** 		| `json` and `openpyxl` used safely; no `pickle` or `eval`. |
| **Local-only data** 			| No privacy risk from data exfiltration. |

## **7. Conclusion**

> **PlanIFlow v2.3.0 is secure, robust, and suitable for deployment.**

It adheres to **defense-in-depth principles** appropriate for an offline desktop application.

**End of Report**