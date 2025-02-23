

from typing import List
from sqlalchemy import text
from dotenv import load_dotenv

from sqlalchemy.orm.session import Session
from tables import Chunks
from tables import Requests
from tables import Tasks


from logger import logger
from users import current_user, is_admin

load_dotenv()


def sql_query(session: Session, sql: str):
    session.execute(text(sql))

    return session.execute(text(sql))


def sql_commit(session: Session, sql: str):
    session.execute(text(sql))
    session.commit()


def queue_task(session: Session, task: Tasks):
    task.status = 1
    session.commit()


def run_task(session: Session, task: Tasks):
    task.status = 2
    task.error_message = ""
    task.request_failed = 0
    task.request_succeed = 0
    session.commit()


def error_task(session: Session, task: Tasks, message: str):
    task.status = 3
    task.error_message = message
    session.commit()


def succeed_task(session: Session, task: Tasks):
    task.status = 4
    task.error_message = ""
    session.commit()


def delete_task_data(session: Session, task: Tasks):
    sql_commit(
        session, f'delete from {Requests.__tablename__} where task_id = {task.id}')
    sql_commit(
        session, f'delete from {Chunks.__tablename__} where task_id = {task.id}')


def load_all_tasks(session: Session) -> List[Tasks]:
    admin = is_admin(session)

    if admin:
        return session.query(
            Tasks
        ).order_by(
            Tasks.created_at.desc()
        ).all()

    return session.query(
        Tasks
    ).order_by(
        Tasks.created_at.desc()
    ).filter(
        Tasks.user_id == current_user(session).id
    ).all()


def load_all_requests(session: Session, task: Tasks, success: int) -> List[Requests]:
    results = session.query(
        Requests
    ).filter(
        Requests.task_id == task.id,
        Requests.success == success
    ).order_by(
        Requests.request_index.desc()
    ).limit(
        10000
    ).all()

    return results


def load_all_chunks(session: Session, request: Chunks) -> List[Chunks]:
    results = session.query(
        Chunks
    ).filter(
        Chunks.request_id == request.id,
    ).order_by(
        Chunks.created_at.asc()
    ).limit(
        10000
    ).all()

    return results


def load_queue_tasks(session: Session) -> List[Tasks]:
    results = session.query(
        Tasks
    ).filter(
        Tasks.status == 1
    ).order_by(
        Tasks.created_at.asc()
    ).limit(
        1
    ).all()

    return results


def find_request(session: Session, request_id: int) -> Requests | None:
    request = session.query(
        Requests
    ).filter(
        Requests.id == request_id
    ).first()

    return request
