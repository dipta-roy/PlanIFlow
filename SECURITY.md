# **PlanIFlow - Formal Security Assessment Report**  
## **PlanIFlow v2.4.0 – Offline-First Desktop Project Management Application**  
**Assessment Conducted:** January 15, 2026  
**Scope:** All Python source files (`*.py`) including `main.py`, `ui/`, `data_manager/`, `updater.py`, and build scripts.  
**Methodology:** Static code analysis (SAST), manual code review, data flow tracing, STRIDE threat modeling, CVSS v3.1 scoring.  
**Classification:** **LOW RISK – SECURE FOR INTENDED USE**

## **1. Executive Summary**

**PlanIFlow** is a **standalone desktop application** built with **Python 3.10+ and PyQt6**, designed for **project planning and management**. It operates primarily **offline**, with **optional network connectivity** solely for checking and downloading application updates from GitHub.

After a **comprehensive security audit** of all source code, **no critical or high-severity vulnerabilities** were identified. The application's design minimizes attack surface by avoiding persistent network listeners, user authentication, or external cloud storage.

> **Final Risk Rating: LOW** (Base CVSS: 3.9/10)  
> **Recommended Posture: SAFE FOR DEPLOYMENT**

The application is **secure by design** for its intended use case: **single-user, local project planning on Windows**.

## **2. Scope & Methodology**

| Item 						| Details 													|
|---------------------------|-----------------------------------------------------------|
| **Files Analyzed** 		| ~55 `.py` files (e.g., `main.py`, `updater.py`, `data_manager/validator.py`, `installer/package_installer.py`) |
| **Analysis Type** 		| White-box static analysis (SAST) and manual code review. 	|
| **Tools Used** 			| Manual code review, dependency check, CVSS v3.1 scoring. |
| **Threat Model** 			| STRIDE Analysis (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege). |
| **Standards Referenced** 	| OWASP Top 10 (Python), CWE. 			|

## **3. System Architecture Overview**

```
[User Input via Qt Widgets] → [PyQt6 UI Layer] → [DataManager Models] → [Local I/O: JSON/Excel/PDF]
                                           ↑
                                    [Visualization: Matplotlib Gantt/Dashboard]
                                           ↓
[Update Manager] ← (HTTPS/TLS) → [GitHub Releases API]
```

- **Minimal Network Stack**: `requests` is used only in `updater.py` for version checks and downloads. No server listeners or telemetry.
- **No Database Server**: Data is managed in-memory with `pandas` and persisted via local JSON/Excel files. SQLite is present (`sqlite3.dll`) but used only as a library dependency (e.g. by pandas internally), not for central app storage.
- **No Privilege Escalation**: Runs in user-context. Installer creation uses `PyInstaller`; main app uses `cx_Freeze`.
- **All file I/O is user-initiated** via `QFileDialog` or standard temporary file mechanisms.

## **4. Security Findings**

### **4.1 Remote Attack Surface**

The application has a **minimal** remote attack surface, limited strictly to the update mechanism.

| Feature | Protocol | Risk | Mitigation |
|:---|:---|:---|:---|
| **Auto-Update Check** | HTTPS (Outbound) | Low | Uses `requests` with strict TLS verification to fetch data from `api.github.com`. |
| **Update Download** | HTTPS (Outbound) | Low | Downloads `.msi` files from GitHub Releases. |
| **Hash Verification** | SHA256 | Low | `updater.py` verifies the SHA256 hash of downloaded MSI files against a trusted hash file from the release before execution. |

### **4.2 File Input Validation & Sanitization**

File parsing is handled by standard, well-vetted libraries with robust application-level validation.

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
- **No `pickle`, `yaml.load`, or custom decoders are used for user data.**
- **JSON and Excel parsing are handled securely**, preventing remote code execution from malicious files.

### **4.5 Privilege & Command Execution**

- **Runtime `subprocess`**: **Restricted**. 
    - `updater.py`: Executes `msiexec /i ...` to run the downloaded installer. This is standard practice for updates.
    - `installer/package_installer.py`: Uses `subprocess.check_call` to invoke `pyinstaller` during the *build* process.
- **Build System**: The main application is frozen using `cx_Freeze`. The final installer is wrapped using `PyInstaller`.
- **Registry/Privileges**: The application runs entirely in user-context. The installer may request elevation (UAC) if installing to system directories.

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
| requests      | `2.32.5`          | None. | Low   |
| cx_Freeze     | `8.5.3`           | None. | Low   |

## **5. STRIDE Threat Modeling**

A STRIDE analysis was performed to identify and mitigate potential threats in the application lifecycle.

| Threat Category | Potential Scenario | Mitigation Strategy | Status |
|:---|:---|:---|:---|
| **S**poofing | Attacker impersonates the GitHub update server to serve malicious payloads. | **TLS/HTTPS Verification**: The `updater.py` uses `requests` which enforces strict SSL/TLS certificate validation. | ✅ Mitigated |
| **T**ampering | Attacker modifies local JSON/Excel project files to inject malicious code or crash the app. | **Input Validation**: `ProjectValidator` enforces schema compliance, data type checks, and string sanitization. No `eval()` or macro execution is permitted. | ✅ Mitigated |
| **T**ampering | Attacker modifies the downloaded installer binary during transit. | **Hash Verification**: The application calculates the SHA256 hash of the downloaded MSI and compares it against a signed/trusted hash file before execution. | ✅ Mitigated |
| **R**epudiation | User denies actions taken within the application (e.g., deleting a critical task). | **Scope Note**: As a single-user offline desktop app, non-repudiation is not a primary security requirement. Local file system logs provide basic traceability. | ⚪ Accepted |
| **I**nformation Disclosure | Application leaks sensitive project data via error logs or crash reports. | **Error Handling**: Global exception handlers sanitize error messages presented to the user. No automatic crash reporting or telemetry is sent to external servers. | ✅ Mitigated |
| **D**enial of Service | User imports a "Zip Bomb" style file (e.g., 1 million tasks) to crash the application. | **Resource Limits**: `ProjectValidator.MAX_TASKS` (10,000) and `MAX_STR_LEN` (250) constants hard-limit the data processing to prevent memory exhaustion. | ✅ Mitigated |
| **E**levation of Privilege | Application exploits OS vulnerabilities to gain Admin rights. | **Least Privilege**: The application runs strictly in the user's context. `msiexec` is invoked for updates but relies on standard Windows UAC if admin rights are needed for installation. | ✅ Mitigated |

## **6. Risk Assessment Matrix**

| Threat 					| Likelihood 	| Impact 	| Risk Level 	| CVSS v3.1 Score & Vector |
|---------------------------|---------------|-----------|---------------|--------------------------|
| **Malicious JSON/Excel RCE** 	| Improbable 	| High 		| **LOW** 		| **0.0** (None)<br>`CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:N/I:N/A:N` |
| **Input-Induced DoS** 		| Unlikely 		| Low 		| **LOW** 		| **3.3** (Low)<br>`CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:N/I:N/A:L` |
| **Update Man-in-the-Middle**  | Very Low      | High      | **LOW**       | **3.1** (Low)<br>`CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:L/A:N` |
| **Supply-Chain** (pinned deps)| Improbable | Low | **LOW** | **0.0** (None)<br>`CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N` |

*Note: Path Traversal, Privilege Escalation, and Network-based attacks (listening services) were evaluated and deemed not applicable.*

## **7. Security Strengths**

| Strength 						| Benefit 					|
|-------------------------------|---------------------------|
| **Offline-First Design** 	    | Network usage is strictly optional and user-initiated (updates). |
| **Strict Input Validation**   | `ProjectValidator` enforces strict limits on task counts and string lengths, mitigating DoS and memory exhaustion. |
| **Secure Update Mechanism**   | Enforces SHA256 hash verification on downloaded updates. |
| **User-controlled file I/O** 	| `QFileDialog` prevents unauthorized file access. |
| **Safe deserialization** 		| `json` and `openpyxl` used safely; no `pickle` or `eval`. |
| **Local-only data** 			| No privacy risk from data exfiltration. |

## **8. Conclusion**

> **PlanIFlow v2.4.0 is secure, robust, and suitable for deployment.**

It adheres to **defense-in-depth principles**, balancing user convenience (auto-updates) with strong security controls (input validation, hash verification).

**End of Report**