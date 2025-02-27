"""File system watcher that automatically restarts worker queue on code changes."""

import time
import subprocess
from watchdog.observers import Observer
from observer_handler import MyHandler

TARGET_SCRIPT = "worker_queue.py"


if __name__ == "__main__":
    handler = MyHandler()
    handler.process = subprocess.Popen(["python", TARGET_SCRIPT])

    observer = Observer()
    observer.schedule(handler, path=".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

        if handler.process and handler.process.poll() is None:
            handler.process.terminate()
            try:
                handler.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                handler.process.kill()
    observer.join()
