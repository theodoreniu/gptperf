from time import sleep
from tables import create_task_tables, delete_table
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

                    logger.info(f"delete old data ...")
                    delete_table(task.id)
                    create_task_tables(task.id)

                    logger.info(f"start request ...")
                    task_executor(task)
                except Exception as e:
                    error_task(task, {e})
                    logger.error(f'Error: {e}', exc_info=True)
            else:
                # logger.info("waitting for request ...")
                sleep(1)

        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            sleep(1)
