

from typing import List
from sqlalchemy import text
from dotenv import load_dotenv

from sqlalchemy.orm.session import Session
from helper import get_mysql_session
from tables import Chunks, Users
from tables import Requests
from tables import Tasks
from sqlalchemy import update

from logger import logger
from users import current_user, is_admin

load_dotenv()


def load_all_users() -> List[Users]:
    session = get_mysql_session()

    results = session.query(
        Users
    ).order_by(
        Users.created_at.desc()
    ).all()

    session.close()

    return results


def sql_query(session: Session, sql: str):
    session.execute(text(sql))

    return session.execute(text(sql))


def sql_commit(session: Session, sql: str):
    session = get_mysql_session()
    session.execute(text(sql))
    session.commit()
    session.close()


def queue_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task.id
        ).first()
        task.status = 1
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def delete_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task.id
        ).first()
        session.delete(task)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def update_task(task: Tasks):
    session = get_mysql_session()
    try:

        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task.id
        ).first()

        task.name = task.name
        task.model_type = task.model_type
        task.model_id = task.model_id
        task.azure_endpoint = task.azure_endpoint
        task.api_key = task.api_key
        task.api_version = task.api_version
        task.deployment_name = task.deployment_name
        task.timeout = task.timeout
        task.request_per_thread = task.request_per_thread
        task.threads = task.threads
        task.feishu_token = task.feishu_token
        task.enable_think = task.enable_think

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def add_request(request: Requests):
    session = get_mysql_session()
    try:
        session.add(request)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def add_chunk(chunk: Chunks):
    session = get_mysql_session()
    try:
        session.add(chunk)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def add_user(user: Users):
    session = get_mysql_session()
    try:
        session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def find_user_by_username(username: str):
    session = get_mysql_session()

    try:
        return session.query(
            Users
        ).filter(
            Users.username == username
        ).first()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()
        return None


def add_task(task: Tasks):
    session = get_mysql_session()
    try:
        session.add(task)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def run_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task.id
        ).first()
        task.status = 2
        task.error_message = ""
        task.request_failed = 0
        task.request_succeed = 0
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def error_task(task: Tasks, message: str):
    session = get_mysql_session()
    try:
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task.id
        ).first()
        task.status = 3
        task.error_message = message
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def task_request_succeed(request: Requests):
    session = get_mysql_session()
    try:
        session.execute(
            update(
                Tasks
            ).where(
                Tasks.id == request.task_id
            ).values(
                request_succeed=Tasks.request_succeed + 1
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def task_request_failed(request: Requests):
    session = get_mysql_session()
    try:
        session.execute(
            update(
                Tasks
            ).where(
                Tasks.id == request.task_id
            ).values(
                request_failed=Tasks.request_failed + 1
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def succeed_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task.id
        ).first()
        task.status = 4
        task.error_message = ""
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def delete_task_data(task: Tasks):
    sql_commit(
        f'delete from {Requests.__tablename__} where task_id = {task.id}')
    sql_commit(f'delete from {Chunks.__tablename__} where task_id = {task.id}')


def load_all_tasks() -> List[Tasks]:
    session = get_mysql_session()

    admin = is_admin()

    tasks = None
    if admin:
        tasks = session.query(
            Tasks
        ).order_by(
            Tasks.created_at.desc()
        ).all()

    tasks = session.query(
        Tasks
    ).order_by(
        Tasks.created_at.desc()
    ).filter(
        Tasks.user_id == current_user().id
    ).all()

    session.close()

    return tasks


def load_all_requests(task: Tasks, success: int) -> List[Requests]:
    session = get_mysql_session()

    requests = session.query(
        Requests
    ).filter(
        Requests.task_id == task.id,
        Requests.success == success
    ).order_by(
        Requests.request_index.desc()
    ).limit(
        10000
    ).all()

    session.close()

    return requests


def load_all_chunks(request: Chunks) -> List[Chunks]:
    session = get_mysql_session()

    results = session.query(
        Chunks
    ).filter(
        Chunks.request_id == request.id,
    ).order_by(
        Chunks.created_at.asc()
    ).limit(
        10000
    ).all()

    session.close()

    return results


def load_queue_tasks() -> List[Tasks]:
    session = get_mysql_session()

    results = session.query(
        Tasks
    ).filter(
        Tasks.status == 1
    ).order_by(
        Tasks.created_at.asc()
    ).limit(
        1
    ).all()

    session.close()

    return results


def find_request(request_id: int) -> Requests | None:
    session = get_mysql_session()

    request = session.query(
        Requests
    ).filter(
        Requests.id == request_id
    ).first()

    session.close()

    return request
