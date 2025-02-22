from time import sleep
from task_executor import task_executor
from task_loads import TaskTable, delete_task_data, error_task, load_queue_tasks, run_task
from typing import List
import traceback

if __name__ == "__main__":

    while (True):

        tasks: List[TaskTable] = load_queue_tasks()
        for task in tasks:
            try:
                run_task(task)
                delete_task_data(task)
                task_executor(task)
            except Exception as e:
                error_task(task, {e})
                print(e)
                traceback.print_exc()

        print("sleep 5 seconds...")
        sleep(5)
