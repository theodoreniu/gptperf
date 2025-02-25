from time import sleep
import traceback
from task_executor import task_executor
from task_loads import error_task,  run_task, task_dequeue
from logger import logger

if __name__ == "__main__":

    while (True):

        try:
            task = task_dequeue()
            if task:
                try:
                    logger.info(f"task {task.id} start...")
                    run_task(task.id)

                    logger.info(f"start request ...")
                    task_executor(task)
                except Exception as e:
                    error_task(task, f"{traceback.format_exc()}")
                    logger.error(f'Error: {e}', exc_info=True)
            else:
                sleep(1)

        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
