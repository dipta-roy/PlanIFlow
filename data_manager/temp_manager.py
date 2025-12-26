import os
import tempfile
import logging
import atexit
from typing import List, Optional

class TempFileManager:
    """
    Unified manager for temporary files created during application runtime.
    Ensures unique filenames and reliable cleanup.
    """
    
    _checked_files: List[str] = []
    _temp_dir: Optional[str] = None

    @classmethod
    def get_temp_dir(cls) -> str:
        """Get or create a dedicated temp directory for the app session"""
        if cls._temp_dir is None:
            cls._temp_dir = tempfile.mkdtemp(prefix="planiflow_")
            logging.info(f"Created session temp directory: {cls._temp_dir}")
        return cls._temp_dir

    @classmethod
    def get_temp_path(cls, suffix: str = ".tmp", prefix: str = "temp_") -> str:
        """Generate a unique temporary file path and register it for cleanup"""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=cls.get_temp_dir())
        os.close(fd) # Close file descriptor immediately, we just want the path
        cls._checked_files.append(path)
        return path

    @classmethod
    def register_file(cls, path: str):
        """Register an existing file for automated cleanup"""
        if path and path not in cls._checked_files:
            cls._checked_files.append(path)

    @classmethod
    def cleanup(cls):
        """Clean up all registered temporary files and directories"""
        for path in cls._checked_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    # logging.debug(f"Cleaned up temp file: {path}")
            except Exception as e:
                logging.warning(f"Failed to cleanup temp file {path}: {e}")
        
        # Clear the list
        cls._checked_files = []
        
        # Remove the session temp directory if it exists
        if cls._temp_dir and os.path.exists(cls._temp_dir):
            try:
                import shutil
                shutil.rmtree(cls._temp_dir)
                # logging.debug(f"Removed session temp directory: {cls._temp_dir}")
            except Exception as e:
                logging.warning(f"Failed to remove temp directory {cls._temp_dir}: {e}")
            cls._temp_dir = None

    @classmethod
    def cleanup_old_sessions(cls):
        """Scan system temp directory and remove leftover session directories from previous runs"""
        try:
            temp_root = tempfile.gettempdir()
            for item in os.listdir(temp_root):
                item_path = os.path.join(temp_root, item)
                if os.path.isdir(item_path) and item.startswith("planiflow_"):
                    # Basic check: if it's older than 24 hours, it's likely a leftover from a crash
                    import time
                    if (time.time() - os.path.getmtime(item_path)) > 86400: # 24 hours
                        try:
                            import shutil
                            shutil.rmtree(item_path)
                            logging.info(f"Cleaned up stale temp session: {item}")
                        except:
                            pass
        except Exception as e:
            logging.debug(f"Error scanning for old sessions: {e}")

# Register cleanup to run on normal program exit
atexit.register(TempFileManager.cleanup)
# Cleanup old sessions once on module load
TempFileManager.cleanup_old_sessions()
