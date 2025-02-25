
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
    request_id = st.query_params.get("request_id", None)

    if task_id and request_id:
        return request_page(task_id, request_id)

    if task_id:
        return task_page(task_id)

    create_task()

    render_list()


def create_task():
    st.markdown("## 📗 Create Task")

    task = Tasks(
        status=0,
        desc="",
        enable_think=True,
        created_at=time_now(),
        content_length=2048,
        temperature=0.8,
        timeout=30000,
        threads=1,
        request_per_thread=1,
        user_id=current_user().id,
        deployment_type="",
    )

    with st.container(
        border=True
    ):
        task_form(task, False)


def render_list():
    tasks: List[Tasks] = load_all_tasks()
    st.session_state.tasks = tasks

    st.markdown(f"## 📁 Tasks ({len(st.session_state.tasks)})")

    if st.button(f"Refresh", key="refresh", icon="🔄"):
        st.session_state.tasks = load_all_tasks()

    with st.container(
        border=True
    ):

        for task in st.session_state.tasks:
            desc = ""
            if task.desc:
                desc = f"| `{task.desc}`"

            st.markdown(
                f'{task.status_icon} {task.name} `{task.model_id}` {desc} <a href="/?task_id={task.id}" target="_blank">⚙️ Manage</a>',
                unsafe_allow_html=True
            )
