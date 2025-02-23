
import streamlit as st
from dotenv import load_dotenv
from helper import time_now
from page_task_edit import task_form
from tables import Tasks
from report import task_report
from task_loads import load_all_requests
import pandas as pd
from sqlalchemy.orm.session import Session
from logger import logger
from users import current_user, is_admin


load_dotenv()


def task_page(session: Session, task_id: int):

    task = None

    if is_admin(session):
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
            Tasks.user_id == current_user(session).id
        ).first()

    if not task:
        st.error("task not found")
        return

    if task.status > 1:
        st.progress(task.progress_percentage)

    st.markdown(
        f"## {task.status_icon} {task.name} `{task.status_text}` `{task.progress_percentage}%`")

    task_form(task, session, True)

    if task.error_message:
        st.error(task.error_message)

    if task.status > 1:

        with st.spinner(text="Loading Report..."):
            try:
                start_time = time_now()
                data = task_report(session, task)
                end_time = time_now()
                cost_time = round(end_time-start_time, 2)
                df = pd.DataFrame.from_dict(data, orient='index')
                st.markdown("## 📊 Report")
                st.text(f"Query {cost_time} ms")
                st.table(df)
            except Exception as e:
                st.error(e)

        with st.spinner(text="Loading Failed Requests..."):
            render_requests(session, task, 0, '❌ Failed Requests')

        with st.spinner(text="Loading Succeed Requests..."):
            render_requests(session, task, 1, '✅ Succeed Requests')


def render_requests(session: Session, task, status, title):
    try:
        start_time = time_now()
        requests = load_all_requests(session, task, status)
        end_time = time_now()
        cost_time = round(end_time-start_time, 2)
        count = len(requests)
        if count > 0:
            st.markdown(f"## {title} ({count})")
            st.text(f"Query {cost_time} ms")

            with st.container(
                border=True, height=400
            ):
                for request in requests:
                    st.markdown(
                        f'`{request.start_req_time_fmt}` {request.id} `{request.request_index}/{request.thread_num}` <a href="/?request_id={request.id}" target="_blank">Logs</a>',
                        unsafe_allow_html=True
                    )
    except Exception as e:
        logger.error(e)
        st.error(e)
