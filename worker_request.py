from time import sleep
from helper import get_mysql_session
from tables.tasks import Tasks
from task_executor import task_executor
from task_loads import delete_task_data, error_task, load_queue_tasks, run_task
from typing import List


import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    while (True):
        session = get_mysql_session()
        tasks: List[Tasks] = load_queue_tasks(session)
        for task in tasks:
            try:
                logger.info(f"task {task.id} start...")
                run_task(session, task)
                delete_task_data(session, task)
                task_executor(session, task)
            except Exception as e:
                error_task(session, task, {e})
                logger.error(f'Error: {e}', exc_info=True)

        if len(tasks) == 0:
            logger.info("sleep 1 seconds for request...")
            sleep(1)
