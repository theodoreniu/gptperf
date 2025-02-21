from time import sleep
from task_executor import task_executor
from task_loads import TaskTable, error_task, load_queue_tasks, truncate_table
from typing import List


if __name__ == "__main__":

    while (True):

        tasks: List[TaskTable] = load_queue_tasks()
        for task in tasks:
            try:
                truncate_table('tasks_requests')
                truncate_table('tasks_requests_chunks')
                task_executor(task)
            except Exception as e:
                error_task(task, {e})
                print(e)

        print("sleep 5 seconds...")
        sleep(5)
