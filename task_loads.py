from typing import List
from sqlalchemy import text
from dotenv import load_dotenv
import streamlit_authenticator as stauth
from helper import get_mysql_session
from tables import (
    Users,
    create_chunk_table_class,
    create_request_table_class,
    create_log_table_class,
)
from tables import Tasks
import streamlit as st
from logger import logger
import copy

from task_cache import TaskCache

load_dotenv()


def get_authenticator():

    users = load_all_users()

    credentials = {"usernames": {}}

    if len(users) == 0:
        st.error("No user found")
        return None

    for user in users:
        credentials["usernames"][user.username] = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "password": user.password,
            "roles": [user.role],
        }

    return stauth.Authenticate(
        credentials=credentials,
        cookie_name="random_cookie_name_perf2",
        cookie_key="random_signature_key_llm_perf2",
        cookie_expiry_days=30,
    )


def is_admin() -> bool:
    return current_user().role == "admin" if current_user() else False


def current_user() -> Users | None:

    if "user" in st.session_state:
        return st.session_state["user"]

    st.session_state["user"] = find_user_by_username(st.session_state["username"])

    return st.session_state["user"]


def load_all_users() -> List[Users]:
    session = get_mysql_session()

    results = session.query(Users).order_by(Users.created_at.desc()).all()

    session.close()

    return results


def sql_query(sql: str):
    session = get_mysql_session()
    result = session.execute(text(sql))
    session.close()

    return result


def sql_commit(sql: str):
    session = get_mysql_session()
    session.execute(text(sql))
    session.commit()
    session.close()


def rebuild_task(task_id: int):
    session = get_mysql_session()
    try:
        task = session.query(Tasks).filter(Tasks.id == task_id).first()
        task.status = 0
        task.error_message = ""
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def queue_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(Tasks).filter(Tasks.id == task.id).first()
        task.status = 1
        task.error_message = ""
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def delete_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(Tasks).filter(Tasks.id == task.id).first()
        session.delete(task)
        session.commit()
        cache = TaskCache()
        cache.delete_task(task.id)
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def update_task(task_update: Tasks, messages: list):
    session = get_mysql_session()
    try:

        task = session.query(Tasks).filter(Tasks.id == task_update.id).first()

        task.name = task_update.name
        task.desc = task_update.desc
        task.model_id = task_update.model_id
        task.azure_endpoint = task_update.azure_endpoint
        task.api_key = task_update.api_key
        task.timeout = task_update.timeout
        task.request_per_thread = task_update.request_per_thread
        task.threads = task_update.threads
        task.feishu_token = task_update.feishu_token
        task.enable_think = task_update.enable_think
        task.messages = messages
        task.message_type = task_update.message_type
        task.temperature = task_update.temperature
        task.max_tokens = task_update.max_tokens
        task.stream = task_update.stream

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
        st.error(f"Error: {e}")
    finally:
        session.close()


def add_user(user: Users):
    session = get_mysql_session()
    try:
        new_user = copy.deepcopy(user)
        session.add(new_user)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
        st.error(f"Error: {e}")
    finally:
        session.close()


def find_task(task_id: int):
    session = get_mysql_session()

    try:
        return session.query(Tasks).filter(Tasks.id == task_id).first()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
        st.error(f"Error: {e}")
        return None
    finally:
        session.close()


def find_user_by_username(username: str):
    session = get_mysql_session()

    try:
        return session.query(Users).filter(Users.username == username).first()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
        st.error(f"Error: {e}")
        return None
    finally:
        session.close()


def add_task(task: Tasks):
    session = get_mysql_session()
    try:
        new_task = copy.deepcopy(task)
        session.add(new_task)
        session.commit()
        task_id = new_task.id
        return task_id
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
        st.error(f"Error: {e}")
    finally:
        session.close()


def run_task(task_id: int):
    session = get_mysql_session()
    try:
        task = session.query(Tasks).filter(Tasks.id == task_id).first()
        task.status = 2
        task.error_message = ""
        task.request_failed = 0
        task.request_succeed = 0
        session.commit()
        cache = TaskCache()
        cache.update_task_status(task.id, 2)
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def error_task(task: Tasks, message: str):
    session = get_mysql_session()
    try:
        task = session.query(Tasks).filter(Tasks.id == task.id).first()
        task.status = 3
        task.error_message = message
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def stop_task(task: Tasks):
    session = get_mysql_session()
    try:
        task = session.query(Tasks).filter(Tasks.id == task.id).first()
        task.status = 5
        session.commit()
        cache = TaskCache()
        cache.update_task_status(task.id, 5)
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
    finally:
        session.close()


def load_all_tasks() -> List[Tasks]:
    session = get_mysql_session()

    tasks = None

    if is_admin():
        tasks = (
            session.query(Tasks)
            .with_entities(
                Tasks.id,
                Tasks.name,
                Tasks.model_id,
                Tasks.status,
                Tasks.created_at,
                Tasks.desc,
            )
            .order_by(Tasks.created_at.desc())
            .all()
        )
    else:
        tasks = (
            session.query(Tasks)
            .with_entities(
                Tasks.id,
                Tasks.name,
                Tasks.model_id,
                Tasks.status,
                Tasks.created_at,
                Tasks.desc,
            )
            .order_by(Tasks.created_at.desc())
            .filter(Tasks.user_id == current_user().id)
            .all()
        )

    session.close()

    return tasks


def load_all_requests(task_id: int):
    Requests = create_request_table_class(task_id)
    session = get_mysql_session()

    requests = (
        session.query(Requests)
        .with_entities(
            Requests.id,
            Requests.start_req_time,
            Requests.first_token_latency_ms,
            Requests.request_latency_ms,
            Requests.chunks_count,
            Requests.output_token_count,
            Requests.success,
            Requests.start_req_time,
        )
        .order_by(Requests.start_req_time.desc())
        .limit(10000)
        .all()
    )

    session.close()

    return requests


def load_all_chunks(task_id: int, request_id: str):
    session = get_mysql_session()
    Chunks = create_chunk_table_class(task_id)

    results = (
        session.query(Chunks)
        .filter(
            Chunks.request_id == request_id,
        )
        .order_by(Chunks.created_at.asc())
        .limit(10000)
        .all()
    )

    session.close()

    return results


def load_all_logs(task_id: int, request_id: str):
    session = get_mysql_session()
    Logs = create_log_table_class(task_id)

    results = (
        session.query(Logs)
        .filter(
            Logs.request_id == request_id,
        )
        .order_by(Logs.created_at.asc())
        .limit(10000)
        .all()
    )

    session.close()

    return results


def task_dequeue() -> Tasks | None:
    session = get_mysql_session()

    task = session.query(Tasks).filter(Tasks.status == 1).limit(1).first()

    session.close()

    return task


def find_request(task_id: int, request_id: str):
    Requests = create_request_table_class(task_id)
    session = get_mysql_session()

    request = session.query(Requests).filter(Requests.id == request_id).first()

    session.close()

    return request
