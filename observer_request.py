"""File system watcher that automatically restarts worker request on code changes."""

import time
import subprocess
from watchdog.observers import Observer
from observer_handler import MyHandler

TARGET_SCRIPT = "worker_request.py"


if __name__ == "__main__":

    process = subprocess.Popen(["python", TARGET_SCRIPT])

    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    observer.join()
