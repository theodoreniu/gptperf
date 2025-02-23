
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy.orm.session import Session
from typing import List
from helper import time_now
from page_task_edit import task_form
from tables import Tasks
from page_request import request_page
from page_task import task_page
from task_loads import load_all_tasks
from users import current_user


load_dotenv()


def home_page(session: Session):

    task_id = st.query_params.get("task_id", None)
    if task_id:
        return task_page(session, task_id)

    request_id = st.query_params.get("request_id", None)
    if request_id:
        return request_page(session, request_id)

    st.markdown("-----------")

    create_task(session)

    render_list(session)


def create_task(session: Session):
    st.markdown("### Create Task")

    task = Tasks(
        status=1,
        enable_think=True,
        created_at=time_now(),
        content_length=2048,
        temperature=0.8,
        timeout=100000,
        threads=1,
        request_per_thread=1,
        user_id=current_user(session).id
    )

    task_form(task, session, False)


def render_list(session: Session):

    tasks: List[Tasks] = load_all_tasks(session)
    st.session_state.tasks = tasks

    st.markdown(f"### Tasks ({len(st.session_state.tasks)})")

    if st.button(f"Refresh", key="refresh", icon="🔄"):
        st.session_state.tasks = load_all_tasks(session)

    for task in st.session_state.tasks:

        st.markdown(
            f'{task.status_icon} {task.name} `{task.model_id}` <a href="/?task_id={task.id}" target="_blank">⚙️ Manage</a>',
            unsafe_allow_html=True
        )
