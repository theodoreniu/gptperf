
from config import aoai, ds, ds_foundry, ds_models, aoai_models, model_types
import streamlit as st
from dotenv import load_dotenv
from tables import Tasks
from task_loads import add_task, delete_task, delete_task_data, queue_task, stop_task, update_task

load_dotenv()


def task_form(task: Tasks, edit: bool = False):

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task.name = st.text_input(
            label="Name",
            value=task.name
        )
    with col2:
        task.desc = st.text_input(
            label="Description",
            value=task.desc
        )
    with col3:
        task.api_key = st.text_input(
            label="api_key",
            value=task.api_key,
            type="password"
        )
    with col4:
        task.feishu_token = st.text_input(
            label="feishu_token",
            value=task.feishu_token,
            help="Will send message to feishu if set when task status changed"
        )

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        task.threads = st.number_input(
            label="threads",
            value=task.threads,
            step=1,
            min_value=1,
            max_value=20,
            help="!!"
        )
    with col2:
        task.request_per_thread = st.number_input(
            label="request_per_thread",
            value=task.request_per_thread,
            step=1,
            min_value=1,
            max_value=1000,
            help="!!"
        )
    with col3:
        st.number_input(
            label="request_total",
            disabled=True,
            value=task.threads * task.request_per_thread
        )
    with col4:
        task.content_length = st.number_input(
            label="Content Length",
            value=task.content_length,
            step=1,
            min_value=1,
            max_value=204800
        )
    with col5:
        task.temperature = st.text_input(
            label="Temperature",
            value=task.temperature
        )
    with col6:
        task.timeout = st.number_input(
            label="timeout (ms)",
            value=task.timeout,
            step=1,
            min_value=1000,
            max_value=100000,
            help="!!"
        )
    col1, col2 = st.columns(2)
    with col1:
        task.system_prompt = st.text_area(
            label="system_prompt",
            value=task.system_prompt,
            help="!!",
            height=200
        )
    with col2:
        task.user_prompt = st.text_area(
            label="user_prompt",
            value=task.user_prompt,
            help="!!",
            height=200
        )

    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
    with col1:
        task.model_type = st.selectbox(
            label='💡 model_type',
            options=model_types,
            index=model_types.index(task.model_type) if task.model_type else 0
        )
    with col2:
        if task.model_type == aoai:
            task.azure_endpoint = st.text_input(
                label="azure_endpoint",
                value=task.azure_endpoint,
                placeholder="https://xxx.openai.azure.com"
            )
        if task.model_type == ds:
            task.azure_endpoint = st.text_input(
                label="endpoint",
                value=task.azure_endpoint,
            )
        if task.model_type == ds_foundry:
            task.azure_endpoint = st.text_input(
                label="endpoint",
                value=task.azure_endpoint,
                placeholder="https://xxxxx.services.ai.azure.com/models"
            )
    with col3:
        if task.model_type == aoai:
            task.model_id = st.selectbox(
                label='model_id',
                options=aoai_models,
                index=aoai_models.index(
                    task.model_id) if task.model_id and task.model_id in aoai_models else 0
            )
        if task.model_type == ds:
            task.model_id = st.selectbox(
                label='model_id',
                options=ds_models,
                index=ds_models.index(
                    task.model_id) if task.model_id and task.model_id in ds_models else 0
            )
        if task.model_type == ds_foundry:
            task.model_id = st.text_input(
                label="model_id",
                value=task.model_id,
            )
    with col4:
        if task.model_type == aoai:
            task.deployment_name = st.text_input(
                label="deployment_name",
                value=task.deployment_name,
                help="!!"
            )
        if task.model_type == ds:
            task.enable_think = st.selectbox(
                label="enable_think",
                options=[True, False],
                index=[True, False].index(
                    task.enable_think) if task.enable_think else 1
            )
    with col5:
        if task.model_type == aoai:
            task.api_version = st.text_input(
                label="api_version",
                value=task.api_version,
                placeholder="2024-08-01-preview"
            )

    def create_update(task: Tasks, edit: bool):
        with st.spinner():
            if not task.name:
                st.error("Name is required.")
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
            if task.model_type == aoai or task.model_type == ds_foundry:
                if not task.api_key:
                    st.error("api_key is required.")
                    return
            if edit:
                update_task(task)
                st.success("Updated Succeed")
            else:
                add_task(task)
                st.success("Created Succeed")
    if not edit:
        create_update_btn = st.button(
            label="➕ Create",
            use_container_width=True,
        )
        if create_update_btn:
            return create_update(task, edit)

    if edit:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_update_btn = st.button(
                label="🔄 Update",
                disabled=task.status == 2,
                use_container_width=True,
            )
        if create_update_btn:
            create_update(task, edit)

        with col2:
            run_btn = st.button(
                label="🚀 Rerun" if task.status == 2 else "🚀 Run",
                key=f"run_task_{task.id}",
                disabled=task.status == 1,
                use_container_width=True
            )
        if run_btn:
            queue_task(task)
            st.success("Pendding")

        with col3:
            stop_btn = st.button(
                label="⛔ Stop",
                key=f"stop_task_{task.id}",
                disabled=task.status != 2,
                use_container_width=True
            )
        if stop_btn:
            stop_task(task)
            st.success("Stoped")

        with col4:
            delete_btn = st.button(
                label="🗑️ Delete",
                key=f"delete_task_{task.id}",
                disabled=task.status == 1 or task.status == 2,
                use_container_width=True
            )
        if delete_btn:
            delete_task_data(task)
            delete_task(task)
            st.success("Deleted")
