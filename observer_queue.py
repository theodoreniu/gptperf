import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logger import logger

TARGET_SCRIPT = 'worker_queue.py'

process = None


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global process

        if event.src_path.endswith('.py'):
            logger.info(f"{TARGET_SCRIPT} updated, restarting...")

            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            process = subprocess.Popen(['python', TARGET_SCRIPT])


if __name__ == "__main__":

    process = subprocess.Popen(['python', TARGET_SCRIPT])

    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
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
