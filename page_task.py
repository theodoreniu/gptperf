import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from helper import get_mysql_session, task_status_icon
from page_task_edit import task_form
from serialize import chunk_len
from tables import Tasks
from metrics import task_metrics
from task_loads import current_user, is_admin, load_all_requests
from logger import logger
import numpy as np


load_dotenv()


def task_page(task_id: int):

    task = None

    session = get_mysql_session()

    if is_admin():
        task = session.query(Tasks).filter(Tasks.id == task_id).first()
    else:
        task = (
            session.query(Tasks)
            .filter(Tasks.id == task_id, Tasks.user_id == current_user().id)
            .first()
        )

    session.close()

    if not task:
        st.error("task not found")
        return

    progress_percentage = f"`{task.progress_percentage}%`"
    if task.status < 2:
        progress_percentage = ""

    st.markdown(
        f"## {task_status_icon(task.status)} {task.name} `{task.status_text}` {progress_percentage}"
    )

    if task.status > 1 and task.progress_percentage > 0:
        st.progress(task.progress_percentage)

    if task.error_message:
        st.error(f"📣 {task.error_message}")

    with st.container(border=True):
        task_form(task, True)

    if task.status > 1:
        display_metrics(task)
        render_charts(task)
        render_requests(task, 0, "❌ Failed Requests")
        render_requests(task, 1, "✅ Succeed Requests")


def render_charts(task):
    st.markdown("## 📉 Charts")

    first_token_latency_ms_array = []
    chunks_count_array = []
    requests = load_all_requests(task.id, 1)
    for request in requests:
        first_token_latency_ms_array.append(
            (request.first_token_latency_ms, request.request_latency_ms)
        )
        chunks_count_array.append((request.chunks_count, request.output_token_count))

    st.line_chart(
        pd.DataFrame(
            first_token_latency_ms_array,
            columns=["First Token Latency", "Request Latency"],
        )
    )

    st.bar_chart(
        pd.DataFrame(chunks_count_array, columns=["Chunks Count", "Output Token Count"])
    )


def display_metrics(task):
    """Display task metrics and queue information."""
    with st.spinner(text="Loading Report..."):
        try:
            data = task_metrics(task)
            df = pd.DataFrame.from_dict(data, orient="index")
            queue_len = chunk_len()
            st.markdown("## 📊 Metrics")
            if queue_len > 0:
                st.markdown(
                    f"`{queue_len}` chunks in queue, please wait them to finish and refresh report."
                )

            st.table(df)
        except Exception as e:
            st.error(e)


def render_requests(task, status, title):
    try:
        requests = load_all_requests(task.id, status)

        count = len(requests)
        if count > 0:
            st.markdown(f"## {title} ({count})")

            with st.container(border=True, height=450 if len(requests) > 10 else None):
                for request in requests:
                    st.markdown(
                        f'`{request.start_req_time_fmt}` {request.id} <a href="/?request_id={request.id}&task_id={task.id}" target="_blank">👀 Log</a>',
                        unsafe_allow_html=True,
                    )
    except Exception as e:
        logger.error(e)
        st.error(e)
