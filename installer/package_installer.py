import os
import shutil
import zipfile
import subprocess
import sys
import base64

# Add project root to path to allow imports from constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from constants.app_images import LOGO_ICO_BASE64
except ImportError:
    # Fallback if running from root without package structure or similar issues
    print("[WARN] Could not import LOGO_ICO_BASE64. Icon will not be set.")
    LOGO_ICO_BASE64 = None

def package_installer():
    base_dir = os.getcwd()
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")
    installer_dir = os.path.join(base_dir, "installer")
    
    # 1. Identify the Source Directory
    # We expect dist/PlanIFlow_2.2.0.exe (as a folder)
    source_dir_name = "PlanIFlow_2.2.0.exe"
    source_path = os.path.join(dist_dir, source_dir_name)
    
    if not os.path.exists(source_path):
        print(f"[ERROR] Source directory not found: {source_path}")
        print("Make sure you ran 'build.bat --onedir' first.")
        sys.exit(1)
        
    print(f"[INFO] Found source directory: {source_path}")

    # 1.5 Create Icon File
    icon_path = os.path.join(installer_dir, "setup_icon.ico")
    if LOGO_ICO_BASE64:
        try:
            with open(icon_path, "wb") as f:
                f.write(base64.b64decode(LOGO_ICO_BASE64))
            print(f"[INFO] Created temporary icon: {icon_path}")
        except Exception as e:
            print(f"[WARN] Failed to create icon file: {e}")
            icon_path = None
    else:
        icon_path = None
    
    # 2. Create Payload Zip
    payload_path = os.path.join(installer_dir, "payload.zip")
    print(f"[INFO] Creating payload: {payload_path}")
    
    with zipfile.ZipFile(payload_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk the directory and zip contents
        # We want the ZIP to contain the CONTENTS of source_path at root level
        for root, dirs, files in os.walk(source_path):
            for file in files:
                abs_path = os.path.join(root, file)
                # Calculate relative path from source_path
                rel_path = os.path.relpath(abs_path, source_path)
                zipf.write(abs_path, rel_path)
                
    print(f"[INFO] Payload created size: {os.path.getsize(payload_path) / (1024*1024):.2f} MB")
    
    # 3. Build the Installer Exe
    # Requires PyInstaller to be installed in current environment
    print("[INFO] Building Installer Executable...")
    
    installer_script = os.path.join(installer_dir, "installer_source.py")
    
    # PyInstaller arguments
    # --onefile: Single exe
    # --noconsole: GUI only
    # --add-data: Embed payload.zip
    # --name: Output name
    # --uac-admin: Request steps privileges (optional, maybe skip to avoid scary prompt if user installs to AppData?)
    # User requested: "Ask user about destination path".
    # Often installers need admin. But this is a simple self-extractor. I'll skip uac-admin to be friendly.
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--name", "PlanIFlow_Setup_2.2.0",
        *(["--icon", icon_path] if icon_path else []),
        "--add-data", f"{payload_path};.",
        *(["--add-data", f"{icon_path};."] if icon_path else []),
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--specpath", installer_dir,
        installer_script
    ]
    
    print(f"[EXEC] {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    # Cleanup payload
    if os.path.exists(payload_path):
        os.remove(payload_path)
    if icon_path and os.path.exists(icon_path):
        os.remove(icon_path)
        
    print(f"[SUCCESS] Installer created at: {os.path.join(dist_dir, 'PlanIFlow_Setup_2.2.0.exe')}")

if __name__ == "__main__":
    package_installer()
