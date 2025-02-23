from time import sleep
from tables import Tasks
from task_executor import task_executor
from task_loads import delete_task_data, error_task, load_queue_tasks, run_task
from typing import List
from logger import logger

if __name__ == "__main__":

    while (True):

        try:
            tasks: List[Tasks] = load_queue_tasks()
            for task in tasks:
                try:
                    logger.info(f"task {task.id} start...")
                    run_task(task)

                    logger.info(f"delete old data ...")
                    delete_task_data(task)

                    logger.info(f"start request ...")
                    task_executor(task)
                except Exception as e:
                    error_task(task, {e})
                    logger.error(f'Error: {e}', exc_info=True)

            if len(tasks) == 0:
                logger.info("waitting for request ...")
                sleep(3)

        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            sleep(3)
