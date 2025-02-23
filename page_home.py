
import streamlit as st
from dotenv import load_dotenv
from typing import List
from helper import time_now
from page_task_edit import task_form
from tables import Tasks
from page_request import request_page
from page_task import task_page
from task_loads import current_user, load_all_tasks


load_dotenv()


def home_page():

    task_id = st.query_params.get("task_id", None)
    if task_id:
        return task_page(task_id)

    request_id = st.query_params.get("request_id", None)
    if request_id:
        return request_page(request_id)

    st.markdown("-----------")

    create_task()

    render_list()


def create_task():
    st.markdown("### Create Task")

    task = Tasks(
        status=0,
        desc="",
        enable_think=True,
        created_at=time_now(),
        content_length=2048,
        temperature=0.8,
        timeout=100000,
        threads=1,
        request_per_thread=1,
        user_id=current_user().id,
        deployment_type="",
    )

    task_form(task, False)


def render_list():

    tasks: List[Tasks] = load_all_tasks()
    st.session_state.tasks = tasks

    st.markdown(f"### Tasks ({len(st.session_state.tasks)})")

    if st.button(f"Refresh", key="refresh", icon="🔄"):
        st.session_state.tasks = load_all_tasks()

    for task in st.session_state.tasks:

        st.markdown(
            f'{task.status_icon} {task.name} `{task.model_id}` <a href="/?task_id={task.id}" target="_blank">⚙️ Manage</a>',
            unsafe_allow_html=True
        )
