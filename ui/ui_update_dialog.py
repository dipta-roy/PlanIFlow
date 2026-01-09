from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QProgressBar, QMessageBox, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSlot, QMetaObject, Q_ARG
from constants.constants import APP_NAME, VERSION, REPO_OWNER, REPO_NAME
from updater import Updater
import sys

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check for Updates")
        self.setFixedSize(400, 250)
        self.updater = Updater(callback=self.on_updater_callback)
        self._init_ui()
        
        # Auto-check on open
        self.check_for_updates()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Do you have the latest {APP_NAME} update?")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1976D2;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current Version
        version = QLabel(f"Current Version: {VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        # Status Label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.action_btn = QPushButton("Check Again")
        self.action_btn.clicked.connect(self.check_for_updates)
        self.action_btn.setVisible(False)
        btn_layout.addWidget(self.action_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

    def check_for_updates(self):
        self.status_label.setText("Checking for updates...")
        self.status_label.setStyleSheet("color: black;")
        self.action_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.updater.check_for_updates()

    def on_updater_callback(self, status, data):
        # Thread-safe UI update
        QMetaObject.invokeMethod(self, "handle_update_status", Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, status), Q_ARG(object, data))

    @pyqtSlot(str, object)
    def handle_update_status(self, status, data):
        if status == "UPDATE_AVAILABLE":
            self.status_label.setText(f"Update Available: {data['version']}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            self.action_btn.setText("Update Now")
            # Safe disconnect
            try: self.action_btn.clicked.disconnect()
            except TypeError: pass 
            self.action_btn.clicked.connect(lambda: self.start_update(data['url'], data.get('hash_url')))
            self.action_btn.setVisible(True)
            self.action_btn.setEnabled(True)
            
        elif status == "NO_UPDATE":
            self.status_label.setText("You are using the latest version.")
            self.status_label.setStyleSheet("color: green;")
            self.action_btn.setText("Check Again")
            try: self.action_btn.clicked.disconnect()
            except TypeError: pass
            self.action_btn.clicked.connect(self.check_for_updates)
            self.action_btn.setVisible(True)
            self.action_btn.setEnabled(True)

        elif status == "NO_MSI_FOUND":
             self.status_label.setText("New version found, but no installer available.")
             self.status_label.setStyleSheet("color: orange;")
             self.action_btn.setVisible(False)

        elif status == "ERROR":
            self.status_label.setText(f"Error: {data}")
            self.status_label.setStyleSheet("color: red;")
            self.action_btn.setText("Retry")
            try: self.action_btn.clicked.disconnect()
            except TypeError: pass
            self.action_btn.clicked.connect(self.check_for_updates)
            self.action_btn.setVisible(True)
            self.action_btn.setEnabled(True)

        elif status == "DOWNLOADING":
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(data)
            self.action_btn.setEnabled(False)
            self.status_label.setText("Downloading update...")
        
        elif status == "VERIFYING_HASH":
            self.status_label.setText("Verifying download integrity...")
            self.progress_bar.setVisible(True) # Keep showing progress bar (full)
            
        elif status == "DOWNLOAD_COMPLETE":
             self.status_label.setText("Download complete. Ready to install.")
             self.progress_bar.setVisible(False)
             
             reply = QMessageBox.question(self, "Update Ready", 
                                          "The update is fully downloaded. \n\nThe application will silently save your project and then close to install the update.\n\nProceed?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                         
             if reply == QMessageBox.StandardButton.Yes:
                 # Auto-save project if possible
                 try:
                     parent = self.parent()
                     if parent and hasattr(parent, '_save_project'):
                         # Check if the project is new (untitled) or existing
                         # If it's untitled, _save_project might open a dialog which could be confusing if canceled.
                         # Instead, we just trigger the standard save.
                         parent._save_project()
                         
                 except Exception as e:
                     print(f"Update Auto-Save Warning: {e}")
                 
                 # Now install
                 self.updater.install_update(data) # 'data' is msi_path here
             else:
                 self.status_label.setText("Update download kept. Restart app or click 'Check Again'.")
                 self.action_btn.setEnabled(True)

        elif status == "INSTALL_STARTED":
             # This means subprocess.Popen was called.
             # We should close the app now.
             sys.exit(0)

    def start_update(self, url, hash_url=None):
        self.updater.download_update(url, hash_url)
