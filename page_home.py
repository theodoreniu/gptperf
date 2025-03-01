from typing import List
import streamlit as st
from dotenv import load_dotenv
from helper import time_now, task_status_icon
from page_task_edit import task_form
from tables import Tasks
from page_request import request_page
from page_task import task_page
from task_loads import current_user, load_all_tasks
from config import DEFAULT_MESSAGES_COMPLETE, MESSAGE_COMPLETE

load_dotenv()


def home_page():
    """Main page handler that routes to task or request pages based on URL parameters."""
    task_id = st.query_params.get("task_id", None)
    request_id = st.query_params.get("request_id", None)

    if task_id and request_id:
        return request_page(task_id, request_id)

    if task_id:
        return task_page(task_id)

    create_task()

    render_list()


def create_task():
    """Renders the task creation form with default values."""
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
        messages=DEFAULT_MESSAGES_COMPLETE,
        message_type=MESSAGE_COMPLETE,
    )

    with st.container(border=True):
        task_form(task, False)


def render_list():
    """Displays a list of all tasks with their status and management links."""
    tasks: List[Tasks] = load_all_tasks()
    st.session_state.tasks = tasks

    if st.button("Refresh", key="refresh", icon="🔄"):
        st.session_state.tasks = load_all_tasks()

    st.markdown(f"## 📁 Tasks ({len(st.session_state.tasks)})")

    for task in st.session_state.tasks:
        desc = f"| `{task.desc}`" if task.desc else ""
        with st.container(border=True):
            col1, col2 = st.columns([12, 2])
            with col1:
                st.markdown(
                    f"{task_status_icon(task.status)} {task.name} `{task.model_id}` {desc}"
                )
            with col2:
                st.link_button(
                    "⚙️ Manage", url=f"/?task_id={task.id}", use_container_width=True
                )
