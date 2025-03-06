import streamlit as st
from dotenv import load_dotenv
from task_cache import TaskCache
from tables import Tasks, create_task_tables, delete_task_tables, truncate_table
from task_loads import (
    add_task,
    delete_task,
    queue_task,
    rebuild_task,
    stop_task,
    update_task,
)
from config import (
    DEFAULT_MESSAGES_COMPLETE,
    DEFAULT_MESSAGES_ASSISTANT,
    DEFAULT_MESSAGES_VISION,
    MESSAGE_ASSISTANT,
    MESSAGE_COMPLETE,
    MESSAGE_TYPES,
    MESSAGE_VISION,
    MODEL_TYPE_API,
    MODEL_TYPE_AOAI,
    MODEL_TYPE_DS_OLLAMA,
    MODEL_TYPE_DS_FOUNDRY,
    MODEL_TYPE_DS_MODELS,
    MODEL_TYPE_AOAI_MODELS,
    MODEL_TYPES,
)

from template_complete import template_complete
from template_vision import template_vision

load_dotenv()


def create_update(task: Tasks, edit: bool, messages: list):
    """Create or update a task after validating required fields.

    Args:
        task: Task object containing form data
        edit: Whether to update existing (True) or create new (False)
    """
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
        if task.model_type == MODEL_TYPE_AOAI:
            if not task.api_version:
                st.error("api_version is required.")
                return
            if not task.deployment_name:
                st.error("deployment_name is required.")
                return
        if (
            task.model_type in (MODEL_TYPE_AOAI, MODEL_TYPE_DS_FOUNDRY)
            and not task.api_key
        ):
            st.error("api_key is required.")
            return

        if not task.messages:
            st.error("Messages is required.")
            return

        if task.messages == []:
            st.error("Messages is required.")
            return

        if edit:
            update_task(task, messages)
            st.success("Updated Succeed")
        else:
            task_id = add_task(task)
            create_task_tables(task_id)
            st.success("Created Succeed")


def task_form(task: Tasks, edit: bool = False):
    """Render a form for creating or editing a task.

    Args:
        task: Task object to edit or use as template for creation
        edit: Whether this is an edit (True) or create (False) operation
    """
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task.name = st.text_input(label="Name", value=task.name)
    with col2:
        task.desc = st.text_input(
            label="Description / Size", value=task.desc, max_chars=200
        )
    with col3:
        task.api_key = st.text_input(
            label="API Key", value=task.api_key, type="password"
        )
    with col4:
        task.feishu_token = st.text_input(
            label="Feishu Token",
            value=task.feishu_token,
            help="Will send message to Feishu if set when task status changed",
        )

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        task.threads = st.number_input(
            label="Concurrency",
            value=task.threads,
            step=1,
            min_value=1,
            max_value=2000,
        )
    with col2:
        task.request_per_thread = st.number_input(
            label="Request Per Concurrency",
            value=task.request_per_thread,
            step=1,
            min_value=1,
            max_value=1000,
        )
    with col3:
        st.number_input(
            label="Request Total",
            disabled=True,
            value=task.threads * task.request_per_thread,
        )
    with col4:
        task.content_length = st.number_input(
            label="Content Length",
            value=task.content_length,
            step=1,
            min_value=1,
            max_value=204800,
        )
    with col5:
        task.max_tokens = st.number_input(
            label="Max Tokens",
            value=task.max_tokens,
            step=1,
            min_value=1,
            max_value=204800,
        )
    with col6:
        task.temperature = st.text_input(label="Temperature", value=task.temperature)
    with col7:
        task.timeout = st.number_input(
            label="Timeout (ms)",
            value=task.timeout,
            step=1,
            min_value=100,
            max_value=60 * 60 * 1000,
        )

    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
    with col1:
        task.model_type = st.selectbox(
            label="💡 Model Type",
            options=MODEL_TYPES,
            index=MODEL_TYPES.index(task.model_type) if task.model_type else 0,
        )
    with col2:
        if task.model_type == MODEL_TYPE_AOAI:
            task.azure_endpoint = st.text_input(
                label="Azure Endpoint",
                value=task.azure_endpoint,
                placeholder="https://xxx.openai.azure.com",
            )
        if task.model_type == MODEL_TYPE_DS_OLLAMA:
            task.azure_endpoint = st.text_input(
                label="Endpoint",
                value=task.azure_endpoint,
            )
        if task.model_type == MODEL_TYPE_DS_FOUNDRY:
            task.azure_endpoint = st.text_input(
                label="Endpoint",
                value=task.azure_endpoint,
                placeholder="https://xxxxx.services.ai.azure.com/models",
            )
        if task.model_type == MODEL_TYPE_API:
            task.azure_endpoint = st.text_input(
                label="Endpoint",
                value=task.azure_endpoint,
                placeholder="http://6.6.6.6:8080/v1/completions",
            )
    with col3:
        if task.model_type == MODEL_TYPE_AOAI:
            task.model_id = st.selectbox(
                label="Model ID",
                options=MODEL_TYPE_AOAI_MODELS,
                index=(
                    MODEL_TYPE_AOAI_MODELS.index(task.model_id)
                    if task.model_id and task.model_id in MODEL_TYPE_AOAI_MODELS
                    else 0
                ),
            )
        if task.model_type == MODEL_TYPE_DS_OLLAMA:
            task.model_id = st.selectbox(
                label="Model ID",
                options=MODEL_TYPE_DS_MODELS,
                index=(
                    MODEL_TYPE_DS_MODELS.index(task.model_id)
                    if task.model_id and task.model_id in MODEL_TYPE_DS_MODELS
                    else 0
                ),
            )
        if task.model_type == MODEL_TYPE_DS_FOUNDRY:
            task.model_id = st.text_input(
                label="Model ID",
                value=task.model_id,
            )
        if task.model_type == MODEL_TYPE_API:
            task.model_id = st.text_input(
                label="Model ID",
                value=task.model_id,
            )
    with col4:
        if task.model_type == MODEL_TYPE_AOAI:
            task.deployment_name = st.text_input(
                label="Deployment Name",
                value=task.deployment_name,
            )
        if task.model_type != MODEL_TYPE_AOAI:
            task.enable_think = st.selectbox(
                label="Enable Think (DeepSeek)",
                options=[True, False],
                index=(
                    [True, False].index(task.enable_think) if task.enable_think else 1
                ),
            )
    with col5:
        if task.model_type == MODEL_TYPE_AOAI:
            task.api_version = st.text_input(
                label="API Version",
                value=task.api_version,
                placeholder="2024-08-01-preview",
            )

    try:
        index = MESSAGE_TYPES.index(task.message_type)
    except:
        index = 0

    message_type = st.selectbox(
        label="Message Type",
        options=MESSAGE_TYPES,
        index=index,
    )

    messages = task.messages

    if task.message_type != message_type:
        if message_type == MESSAGE_COMPLETE:
            messages = template_complete(DEFAULT_MESSAGES_COMPLETE)
        elif message_type == MESSAGE_ASSISTANT:
            messages = template_complete(DEFAULT_MESSAGES_ASSISTANT)
        elif message_type == MESSAGE_VISION:
            messages = template_vision(DEFAULT_MESSAGES_VISION)

    else:
        if task.message_type == MESSAGE_COMPLETE:
            messages = template_complete(task.messages)
        elif task.message_type == MESSAGE_ASSISTANT:
            messages = template_complete(task.messages)
        elif task.message_type == MESSAGE_VISION:
            messages = template_vision(task.messages)

    task.message_type = message_type

    if message_type != MESSAGE_VISION:
        with st.expander("Messages"):
            st.json(messages)

    if not edit:
        create_update_btn = st.button(
            label="➕ Create",
            use_container_width=True,
        )
        if create_update_btn:
            return create_update(task, edit, messages)

    if edit:
        create_update(task, edit, messages)
        col2, col3, col4, col5 = st.columns(4)
        with col2:
            run_btn = st.button(
                label="🚀 Run",
                key=f"run_task_{task.id}",
                disabled=task.status in [1, 2],
                use_container_width=True,
            )
        if run_btn:
            cache = TaskCache()
            queue_len = cache.len()
            if queue_len > 0:
                st.warning(
                    f"Other tasks({queue_len}) are still running, please wait..."
                )
            else:
                if truncate_table(task.id):
                    queue_task(task)
                    st.success("Pending for running...")

        with col3:
            stop_btn = st.button(
                label="⛔ Stop",
                key=f"stop_task_{task.id}",
                disabled=task.status in [0, 3, 4, 5],
                use_container_width=True,
            )
        if stop_btn:
            stop_task(task)
            st.success("Stop Succeed")
        with col4:
            rebuild_btn = st.button(
                label="🪛 Rebuild Data Table",
                key=f"rebuild_task_{task.id}",
                disabled=task.status in (1, 2),
                use_container_width=True,
            )
        if rebuild_btn:
            delete_task_tables(task.id)
            if create_task_tables(task.id):
                rebuild_task(task.id)
                st.success("Rebuild Succeed")
        with col5:
            delete_btn = st.button(
                label="🗑️ Delete",
                key=f"delete_task_{task.id}",
                disabled=task.status in (1, 2),
                use_container_width=True,
            )
        if delete_btn:
            delete_task_tables(task.id)
            delete_task(task)
            st.success("Deleted")
