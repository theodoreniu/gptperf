from time import sleep
from helper import get_mysql_session
from task_executor import task_executor
from task_loads import TaskTable, delete_task_data, error_task, load_queue_tasks
from typing import List
import traceback

if __name__ == "__main__":

    session = get_mysql_session()

    while (True):

        tasks: List[TaskTable] = load_queue_tasks(session)
        for task in tasks:
            try:
                task.status = 2
                session.commit()
                delete_task_data(session, task)
                task_executor(session, task)
            except Exception as e:
                error_task(session, task, {e})
                print(e)
                traceback.print_exc()

        print("sleep 5 seconds...")
        sleep(5)
