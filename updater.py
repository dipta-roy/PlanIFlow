import os
import threading
import subprocess
import requests
import tempfile
import logging
import hashlib
from constants.constants import GITHUB_API_URL, VERSION

class Updater:
    def __init__(self, callback=None):
        self.callback = callback # Function to call with update status (status_code, data)
        # status_code: "UPDATE_AVAILABLE", "NO_UPDATE", "ERROR", "DOWNLOADING", "DOWNLOAD_COMPLETE", "INSTALL_STARTED", "NO_MSI_FOUND", "VERIFYING_HASH"

    def check_for_updates(self):
        """Checks for updates in a background thread."""
        thread = threading.Thread(target=self._check_update_worker)
        thread.daemon = True
        thread.start()

    def _check_update_worker(self):
        try:
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            
            latest_version = release_data.get("tag_name", "").strip("v")
            if self._is_newer(latest_version, VERSION):
                 # Find MSI asset and Hash asset
                assets = release_data.get("assets", [])
                msi_url = None
                hash_url = None
                
                for asset in assets:
                    name = asset["name"].lower()
                    if name.endswith(".msi"):
                        msi_url = asset["browser_download_url"]
                    elif name.endswith("sha256.txt"):
                        hash_url = asset["browser_download_url"]
                
                if msi_url:
                    if self.callback:
                        self.callback("UPDATE_AVAILABLE", {
                            "version": latest_version, 
                            "url": msi_url,
                            "hash_url": hash_url
                        })
                else:
                    if self.callback:
                        self.callback("NO_MSI_FOUND", None)
            else:
                 if self.callback:
                        self.callback("NO_UPDATE", None)
                        
        except Exception as e:
            logging.error(f"Update check failed: {e}")
            if self.callback:
                self.callback("ERROR", str(e))

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            # basic comparison
            return l_parts > c_parts
        except ValueError:
            # Fallback for simple string comparison or complex version strings
            return latest > current

    def download_update(self, url, hash_url=None):
        """Starts background download of the update."""
        thread = threading.Thread(target=self._download_worker, args=(url, hash_url))
        thread.daemon = True
        thread.start()

    def _download_worker(self, url, hash_url):
        try:
            if self.callback:
                self.callback("DOWNLOADING", 0)

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            temp_dir = tempfile.gettempdir()
            msi_path = os.path.join(temp_dir, "PlanIFlow_Update.msi")
            
            with open(msi_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            if self.callback:
                                self.callback("DOWNLOADING", progress)
            
            # Verify Hash if provided
            if hash_url:
                if self.callback:
                    self.callback("VERIFYING_HASH", None)
                
                hash_response = requests.get(hash_url, timeout=10)
                hash_response.raise_for_status()
                # Assuming the file contains just the hash or "hash filename"
                expected_hash = hash_response.text.split()[0].strip().lower() # First word is usually the hash
                
                local_hash = self._calculate_file_hash(msi_path)
                
                if local_hash != expected_hash:
                    os.remove(msi_path) # Delete invalid file
                    raise ValueError("Hash verification failed! File may be corrupted.")
            
            if self.callback:
                self.callback("DOWNLOAD_COMPLETE", msi_path)
                
        except Exception as e:
            logging.error(f"Download failed: {e}")
            if self.callback:
                self.callback("ERROR", str(e))

    def _calculate_file_hash(self, filepath):
        """Calculates SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest().lower()

    def install_update(self, msi_path):
        """Starts installation of the downloaded MSI."""
        thread = threading.Thread(target=self._install_worker, args=(msi_path,))
        thread.daemon = True
        thread.start()

    def _install_worker(self, msi_path):
        try:
            if self.callback:
                self.callback("INSTALL_STARTED", None)
            
            # /i install
            # /qn silent (no UI)
            
            # Construct command to run updated app after install
            import sys
            current_exe = sys.executable
            
            # Chain commands: Install -> Wait 5s -> Start App
            # We use 'start "" ' to ensure it detaches completely.
            # subprocess.Popen with shell=True handles the command execution via cmd.exe.
            # Double quotes around paths are sufficient. 
            # Added /norestart to msiexec to prevent unexpected reboots.
            
            cmd = f'msiexec /i "{msi_path}" /qn /norestart && timeout /t 5 && start "" "{current_exe}"'
            
            # Using Popen to detach.
            subprocess.Popen(cmd, shell=True)
            
        except Exception as e:
            logging.error(f"Install failed: {e}")
            if self.callback:
                self.callback("ERROR", str(e))
