
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
from report import task_report
from tables import TaskTable
from task_loads import add_task, delete_task, find_task, load_all_requests, load_all_tasks, queue_task
import pandas as pd

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
        task.timeout = st.number_input(
            label="timeout", step=1,
            min_value=10000, max_value=100000, help="!!"
        )
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

    col1, col2 = st.columns(2)
    with col1:
        task.system_prompt = st.text_area(
            label="system_prompt", help="!!", height=200)
    with col2:
        task.user_prompt = st.text_area(
            label="user_prompt", help="!!", height=200)

    col1, col2, col3 = st.columns(3)
    with col1:
        task.model_type = st.selectbox(
            label='💡 model_type', options=[aoai, ds])

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
    task_id = st.query_params.get("task_id", None)
    if task_id:
        return task_page(task_id)
    with st.expander(label=f"➕ Create Task"):
        create_task()

    render_list()


def task_page(task_id: int):

    st.session_state.task = find_task(task_id)

    task = st.session_state.task

    st.markdown(
        f"## {task.status_icon} {task.name} `{task.status_text}` `{task.progress_percentage}%`")

    if task.status > 1 and task.progress_percentage > 0:
        st.progress(task.progress_percentage)

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
        st.write(f"desc: `{task.desc}`")
        st.write(f"progress_percentage: `{task.progress_percentage}%`")
        st.write(f"model_type: `{task.model_type}`")
        st.write(f"request_succeed: `{task.request_succeed}`")
    with col2:
        st.write(f"created_at: `{task.created_at}`")
        st.write(f"model_id: `{task.model_id}`")
        st.write(f"endpoint: `{task.azure_endpoint}`")
        st.write(f"request_failed: `{task.request_failed}`")
    with col3:
        st.write(f"api_key: `******************`")
        st.write(f"threads: `{task.threads}`")
        st.write(f"request_per_thread: `{task.request_per_thread}`")
        st.write(f"request_total: `{task.request_per_thread * task.threads}`")

    st.write(f"system_prompt: `{task.system_prompt}`")
    st.write(f"user_prompt: `{task.user_prompt}`")

    if task.error_message:
        st.error(task.error_message)

    if task.status > 1 and task.progress_percentage > 0:

        with st.spinner(text="Loading Report..."):
            try:
                data = task_report(task)
                df = pd.DataFrame.from_dict(data, orient='index')
                st.markdown("## Report")
                st.table(df)
            except Exception as e:
                print(e)

        with st.spinner(text="Loading Requests..."):
            try:
                requests = load_all_requests(task)
                list = []
                for request in requests:
                    list.append({
                        "request_id": request.id,
                        "thread_num": request.thread_num,
                        "created_at": request.created_at,
                        "response": request.response,
                        "success": request.success,
                        "chunks_count": request.chunks_count,
                        "completed_at": request.completed_at,
                        "cost_req_time_ms": request.cost_req_time_ms,
                        "first_token_latency_ms": request.first_token_latency_ms,
                        "output_token_count": request.output_token_count,
                        "response_latency_ms": request.response_latency_ms,
                    })

                if len(requests) > 0:
                    st.markdown("## Requests")
                    st.dataframe(list)
            except Exception as e:
                print(e)


if __name__ == "__main__":

    page_title = "LLM Testing Platform"
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

                col1, col2 = st.columns([10, 2])
                with col1:
                    authenticator.logout()

                home_page()
            elif st.session_state["authentication_status"] is False:
                st.error("Username/password is incorrect")
            elif st.session_state["authentication_status"] is None:
                st.warning("Please enter your username and password")
