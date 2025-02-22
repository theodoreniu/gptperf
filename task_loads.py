

from typing import List


from sqlalchemy import text, update

from tables import TaskRequestChunkTable, TaskRequestTable, TaskTable
from dotenv import load_dotenv


import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

load_dotenv()


def sql_query(session, sql: str):
    session.execute(text(sql))

    return session.execute(text(sql))


def sql_commit(session, sql: str):
    session.execute(text(sql))
    session.commit()


def queue_task(session, task: TaskTable):
    task.status = 1
    session.commit()


def run_task(session, task: TaskTable):
    task.status = 2
    task.error_message = ""
    task.request_failed = 0
    task.request_succeed = 0
    session.commit()


def error_task(session, task: TaskTable, message: str):
    task.status = 3
    task.error_message = message
    session.commit()


def succeed_task(session, task: TaskTable):
    task.status = 4
    task.error_message = ""
    session.commit()


def delete_task_data(session, task: TaskTable):
    sql_commit(
        session, f'delete from {TaskRequestTable.__tablename__} where task_id = {task.id}')
    sql_commit(
        session, f'delete from {TaskRequestChunkTable.__tablename__} where task_id = {task.id}')


def load_all_tasks(session) -> List[TaskTable]:
    results = session.query(
        TaskTable
    ).order_by(
        TaskTable.created_at.desc()
    ).all()

    return results


def load_all_requests(session, task: TaskTable, success: int) -> List[TaskRequestTable]:
    results = session.query(
        TaskRequestTable
    ).filter(
        TaskRequestTable.task_id == task.id,
        TaskRequestTable.success == success
    ).order_by(
        TaskRequestTable.request_index.desc()
    ).limit(
        10000
    ).all()

    return results


def load_all_chunks(session, request: TaskRequestChunkTable) -> List[TaskRequestChunkTable]:
    results = session.query(
        TaskRequestChunkTable
    ).filter(
        TaskRequestChunkTable.request_id == request.id,
    ).order_by(
        TaskRequestChunkTable.created_at.asc()
    ).limit(
        10000
    ).all()

    return results


def load_queue_tasks(session) -> List[TaskTable]:
    results = session.query(
        TaskTable
    ).filter(
        TaskTable.status == 1
    ).order_by(
        TaskTable.created_at.asc()
    ).limit(
        1
    ).all()

    return results


def find_request(session, request_id: int) -> TaskRequestTable | None:
    request = session.query(
        TaskRequestTable
    ).filter(
        TaskRequestTable.id == request_id
    ).first()

    return request
