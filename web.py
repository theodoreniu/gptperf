
from config import aoai, ds
import logging
import sys
from time import sleep
import streamlit as st
import os
from dotenv import load_dotenv
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from typing import List
from helper import is_admin, time_now
from tables import TaskTable
from task_loads import add_task, delete_task, find_task, load_all_tasks, queue_task
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()

notebook_dir = os.path.abspath("")
parent_dir = os.path.dirname(notebook_dir)
grandparent_dir = os.path.dirname(parent_dir)

sys.path.append(grandparent_dir)


def create_task():
    st.markdown("### Create Task")

    task = TaskTable(
        status=1,
        enable_think=True,
        created_at=time_now(),
    )

    col1, col2 = st.columns(2)
    with col1:
        task.name = st.text_input(label="Name", help="!!")
    with col2:
        task.desc = st.text_input(label="Description", help="!!")

    col1, col2, col3 = st.columns(3)
    with col1:
        task.threads = st.number_input(
            label="threads", step=1, min_value=1, max_value=20, help="!!"
        )
        task.feishu_token = st.text_input(label="feishu_token", help="!!")
        task.model_type = st.selectbox(
            label='💡 model_type', options=[aoai, ds])
    with col2:
        task.request_per_thread = st.number_input(
            label="request_per_thread", step=1,
            min_value=1, max_value=1000, help="!!"
        )
        task.api_key = st.text_input(label="api_key", help="!!")
    with col3:
        st.number_input(
            label="request_total", disabled=True,
            value=task.threads * task.request_per_thread
        )
        task.model_id = st.text_input(label="model_id", help="!!")

    if task.model_type == aoai:
        col1, col2 = st.columns(2)
        with col1:
            task.azure_endpoint = st.text_input(
                label="azure_endpoint", help="!!")
            task.deployment_name = st.text_input(
                label="deployment_name", help="!!")
        with col2:
            task.api_version = st.text_input(label="api_version", help="!!")
            task.deployment_type = st.selectbox(label='deployment_type', options=[
                'global standed', 'ds'])

    if task.model_type == ds:
        col1, col2 = st.columns(2)
        with col1:
            task.azure_endpoint = st.text_input(label="endpoint", help="!!")
        with col2:
            enable_think = st.selectbox(label="enable_think", options=[
                'Yes', 'No'])
            if enable_think == 'No':
                task.enable_think = False

    col1, col2 = st.columns(2)
    with col1:
        task.system_prompt = st.text_area(
            label="system_prompt", help="!!", height=200)
    with col2:
        task.user_prompt = st.text_area(
            label="user_prompt", help="!!", height=200)

    if st.button(label="➕ Create"):
        with st.spinner():

            if not task.name:
                st.error("Name is required.")
                return
            if not task.desc:
                st.error("Description is required.")
                return
            if not task.name:
                st.error("Name is required.")
                return
            if not task.model_id:
                st.error("Model ID is required.")
                return
            if not task.azure_endpoint:
                st.error("endpoint is required.")
                return

            if task.model_type == aoai:
                if not task.api_version:
                    st.error("api_version is required.")
                    return
                if not task.deployment_name:
                    st.error("deployment_name is required.")
                    return

            add_task(task)

            st.success("Created Succeed")


def render_list():
    tasks: List[TaskTable] = load_all_tasks()
    st.session_state.tasks = tasks

    if st.button(f"Refresh Tasks ({len(st.session_state.tasks)})", key="refresh", icon="🔄"):
        st.session_state.tasks = load_all_tasks()

    for task in st.session_state.tasks:

        st.markdown(
            f'{task.status_icon} {task.name} <a href="/?task_id={task.id}" target="_blank">⚙️ Manage</a>',
            unsafe_allow_html=True
        )


def home_page():
    st.markdown("--------------")
    task_id = st.query_params.get("task_id", None)
    if task_id:
        return task_page(task_id)
    with st.expander(label=f"➕ Create Task"):
        create_task()

    render_list()


def render_task(task_id: int):

    st.session_state.task = find_task(task_id)

    task = st.session_state.task

    if not task:
        st.error("task not found")
        return

    col1, col2 = st.columns([1, 12])
    with col1:
        if task.status != 1 and task.status != 2 and is_admin():
            delete_btn = st.button(
                label="🗑️ Delete", key=f"delete_task_{task.id}")
            if delete_btn:
                delete_task(task)
                st.success("Deleted")
                st.session_state.tasks = load_all_tasks()
    with col2:
        if task.status != 1 and task.status != 2:
            run_btn = st.button(
                label="✅ Run", key=f"run_task_{task.id}")
            if run_btn:
                queue_task(task)
                st.success("Pendding")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"name: `{task.name}`")
    with col2:
        st.write(f"desc: `{task.desc}`")
    with col3:
        st.write(f"created_at: `{task.created_at}`")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"status: {task.status_icon} `{task.status_text}`")
    with col2:
        st.write(f"progress_percentage: `{task.progress_percentage}%`")
    with col3:
        st.write(f"model_id: `{task.model_id}`")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"model_type: `{task.model_type}`")
    with col2:
        st.write(f"endpoint: `{task.azure_endpoint}`")
    with col3:
        st.write(f"api_key: `******************`")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"threads: `{task.threads}`")
    with col2:
        st.write(f"request_per_thread: `{task.request_per_thread}`")
    with col3:
        st.write(f"request_total: `{task.request_per_thread * task.threads}`")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"request_succeed: `{task.request_succeed}`")
    with col2:
        st.write(f"request_failed: `{task.request_failed}`")

    st.write(f"system_prompt: `{task.system_prompt}`")
    st.write(f"user_prompt: `{task.user_prompt}`")

    if task.error_message:
        st.error(task.error_message)


def task_page(task_id: int):
    render_task(task_id)


if __name__ == "__main__":

    page_title = "LLM 压测服务"
    st.set_page_config(
        page_title=page_title,
        page_icon="avatars/favicon.ico",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.image("avatars/logo.svg", width=100)
    st.title(page_title)

    if not os.path.exists("./config.yaml"):
        home_page()
    else:
        with open("./config.yaml") as file:
            yaml_config = yaml.load(file, Loader=SafeLoader)
            authenticator = stauth.Authenticate(
                yaml_config["credentials"],
                yaml_config["cookie"]["name"],
                yaml_config["cookie"]["key"],
                yaml_config["cookie"]["expiry_days"],
            )

            authenticator.login()

            if st.session_state["authentication_status"]:
                st.write(
                    f'Welcome `{st.session_state["name"]}`')

                col1, col2 = st.columns([1, 16])
                with col1:
                    authenticator.logout()

                home_page()
            elif st.session_state["authentication_status"] is False:
                st.error("Username/password is incorrect")
            elif st.session_state["authentication_status"] is None:
                st.warning("Please enter your username and password")
