
import streamlit as st
from dotenv import load_dotenv
from helper import get_mysql_session
from page_task_edit import task_form
from serialize import chunk_len
from tables import Tasks
from report import task_report
from task_loads import current_user, is_admin, load_all_requests
import pandas as pd
from logger import logger


load_dotenv()


def task_page(task_id: int):

    task = None

    session = get_mysql_session()

    if is_admin():
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task_id
        ).first()
    else:
        task = session.query(
            Tasks
        ).filter(
            Tasks.id == task_id,
            Tasks.user_id == current_user().id
        ).first()

    session.close()

    if not task:
        st.error("task not found")
        return

    progress_percentage = f"`{task.progress_percentage}%`"
    if task.status < 2:
        progress_percentage = ''

    st.markdown(
        f"## {task.status_icon} {task.name} `{task.status_text}` {progress_percentage}")

    if task.status > 1 and task.progress_percentage > 0:
        st.progress(task.progress_percentage)

    if task.error_message:
        st.error(f"📣 {task.error_message}")

    with st.container(
        border=True
    ):
        task_form(task, True)

    if task.status > 1:

        with st.spinner(text="Loading Report..."):
            try:
                data = task_report(task)
                df = pd.DataFrame.from_dict(data, orient='index')
                queue_len = chunk_len()
                st.markdown("## 📊 Report")
                if queue_len > 0:
                    st.markdown(
                        f"`{queue_len}` chunks in queue, please wait them to finish and refresh report.")
                st.table(df)
            except Exception as e:
                st.error(e)

        with st.spinner(text="Loading Failed Requests..."):
            render_requests(task, 0, '❌ Failed Requests')

        with st.spinner(text="Loading Succeed Requests..."):
            render_requests(task, 1, '✅ Succeed Requests')


def render_requests(task, status, title):
    try:
        requests = load_all_requests(task.id, status)

        count = len(requests)
        if count > 0:
            st.markdown(f"## {title} ({count})")

            with st.container(
                border=True,
                height=450 if len(requests) > 10 else None
            ):
                for request in requests:
                    st.markdown(
                        f'`{request.start_req_time_fmt}` {request.id} <a href="/?request_id={request.id}&task_id={task.id}" target="_blank">👀 Log</a>',
                        unsafe_allow_html=True
                    )
    except Exception as e:
        logger.error(e)
        st.error(e)
