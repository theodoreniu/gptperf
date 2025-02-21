from time import sleep
from task_executor import task_executor
from task_loads import TaskTable, error_task, load_queue_tasks
from typing import List


if __name__ == "__main__":

    while (True):

        tasks: List[TaskTable] = load_queue_tasks()
        for task in tasks:
            try:
                task_executor(task)
            except Exception as e:
                error_task(task, 'e.message')
                print(f"task {task.id} error")

        print("sleep 5 seconds...")
        sleep(5)
