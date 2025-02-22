from time import sleep
from tables import TaskRequestChunkTable, TaskRequestTable
from task_executor import task_executor
from task_loads import TaskTable, error_task, load_queue_tasks, run_task, sql_commit
from typing import List
import traceback

if __name__ == "__main__":

    while (True):

        tasks: List[TaskTable] = load_queue_tasks()
        for task in tasks:
            try:
                run_task(task)
                sql_commit(
                    f'delete from {TaskRequestTable.__tablename__} where task_id = {task.id}')
                sql_commit(
                    f'delete from {TaskRequestChunkTable.__tablename__} where task_id = {task.id}')
                task_executor(task)
            except Exception as e:
                error_task(task, {e})
                print(e)
                traceback.print_exc()

        print("sleep 5 seconds...")
        sleep(5)
