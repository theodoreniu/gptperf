"""File system watcher that automatically restarts worker queue on code changes."""

import subprocess
from watchdog.events import FileSystemEventHandler
from logger import logger

TARGET_SCRIPT = "worker_queue.py"


class MyHandler(FileSystemEventHandler):
    """Handles file system events to restart the target script when modified."""
    def __init__(self):
        super().__init__()
        self.process = None

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            logger.info("%s updated, restarting...", TARGET_SCRIPT)

            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()

            self.process = subprocess.Popen(["python", TARGET_SCRIPT])
