import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from helper import format_milliseconds, get_mysql_session, task_status_icon
from page_task_edit import task_form
from serialize import chunk_len
from tables import Tasks
from task_count import task_count
from task_metrics import task_metrics
from task_diff import diff_tasks
from task_loads import current_user, is_admin, load_all_requests, load_all_tasks
from logger import logger


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
        requests = load_all_requests(task.id)
        render_count(task)
        render_metrics(task)
        render_charts(requests)
        render_requests(task, requests, 0, "❌ Failed Requests")
        render_requests(task, requests, 1, "✅ Succeed Requests")

    if task.status == 4:
        diff_tasks_page(task)


def render_count(task):
    counts = task_count(task)
    if counts:
        st.markdown("## 🪧 Overview")
        with st.container(border=True):
            for count in counts:
                st.write(f"{count}: `{counts[count]}`")

            st.write(f"Request Failed: `{task.request_failed}`")
            st.write(f"Request Succeed: `{task.request_succeed}`")


def diff_tasks_page(current_task: Tasks):
    tasks = load_all_tasks()
    tasks = [task for task in tasks if task.id != current_task.id]
    if len(tasks) > 1:
        st.markdown("## 🔰 Diff Tasks")

        options = ["NONE"]
        for task in tasks:
            options.append(f"{task.id} - {task.name}")

        col1, col2 = st.columns(2)
        with col1:
            task_selected = st.selectbox(
                f"Select task to compare with `{current_task.name}`",
                options,
                index=0,
            )
        with col2:
            compare_field = st.selectbox(
                "Select field to compare",
                ["first_token_latency_ms", "request_latency_ms"],
                index=0,
            )

        if task_selected:
            if task_selected != "NONE":
                task_selected_id = int(task_selected.split(" - ")[0])
                with st.spinner("Comparing tasks..."):
                    diff_tasks(current_task.id, task_selected_id, compare_field)


def render_charts(requests):
    requests = [request for request in requests if request.success == 1]
    if len(requests) > 0:
        first_token_latency_ms_array = []
        request_latency_ms_array = []
        chunks_count_array = []

        for request in requests:
            first_token_latency_ms_array.append(request.first_token_latency_ms)
            request_latency_ms_array.append(request.request_latency_ms)
            chunks_count_array.append(
                (request.chunks_count, request.output_token_count)
            )

        if len(first_token_latency_ms_array) > 0 and len(chunks_count_array) > 0:
            st.markdown("## 📉 Charts")

        if len(first_token_latency_ms_array) > 0:
            with st.container(border=True):
                st.markdown("#### First Token Latency")
                st.line_chart(
                    pd.DataFrame(
                        first_token_latency_ms_array,
                        columns=["First Token Latency"],
                    )
                )

        if len(request_latency_ms_array) > 0:
            with st.container(border=True):
                st.markdown("#### Request Latency")
                st.line_chart(
                    pd.DataFrame(request_latency_ms_array, columns=["Request Latency"])
                )

        if len(chunks_count_array) > 0:
            with st.container(border=True):
                st.markdown("#### Chunks Count / Output Token Count")
                st.bar_chart(
                    pd.DataFrame(
                        chunks_count_array,
                        columns=["Chunks Count", "Output Token Count"],
                    )
                )


def render_metrics(task):
    """Display task metrics and queue information."""
    with st.spinner(text="Loading Report..."):
        try:
            data = task_metrics(task)
            df = pd.DataFrame.from_dict(data, orient="index")
            queue_len = chunk_len()
            st.markdown("## 📊 Metrics")
            st.markdown(f"Name: `{task.name}`")
            if queue_len > 0:
                st.markdown(
                    f"`{queue_len}` chunks in queue, please wait them to finish and refresh report."
                )

            st.table(df)
        except Exception as e:
            st.error(e)


def render_requests(task, requests, status, title):
    try:
        requests = [request for request in requests if request.success == status]
        count = len(requests)
        if count > 0:
            st.markdown(f"## {title} ({count})")

            with st.container(border=True, height=450 if len(requests) > 10 else None):
                for request in requests:
                    st.markdown(
                        f'`{format_milliseconds(request.start_req_time)}` {request.id} | {request.output_token_count} <a href="/?request_id={request.id}&task_id={task.id}" target="_blank">👀 Log</a>',
                        unsafe_allow_html=True,
                    )
    except Exception as e:
        logger.error(e)
        st.error(e)
