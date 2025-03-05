"""Page handler for displaying detailed request information and associated chunks."""

import json
import streamlit as st
from dotenv import load_dotenv
from helper import get_mysql_session
from tables import Tasks, create_request_table_class
from task_loads import current_user, is_admin, load_all_chunks, load_all_logs


load_dotenv()


def request_page(task_id: int, request_id: str):
    """Display detailed information about a specific request.

    Args:
        task_id: ID of the task this request belongs to
        request_id: ID of the request to display
    """
    request = None

    session = get_mysql_session()
    Requests = create_request_table_class(task_id)

    task = session.query(Tasks).filter(Tasks.id == task_id).first()

    if is_admin():
        request = session.query(Requests).filter(Requests.id == request_id).first()
    else:
        request = (
            session.query(Requests)
            .filter(Requests.id == request_id, Requests.user_id == current_user().id)
            .first()
        )

    session.close()

    if not request:
        st.error("request not found")
        return

    st.markdown(f"## 🌍 Request `{request.id}`")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"task_id: `{request.task_id}`")
        with col2:
            st.markdown(f"success: `{request.success}`")
        with col3:
            st.markdown(f"thread_num: `{request.thread_num}`")
        with col4:
            st.markdown(f"request_index: `{request.request_index}`")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"input_token_count: `{request.input_token_count}`")
        with col2:
            st.markdown(f"output_token_count: `{request.output_token_count}`")
        with col3:
            st.markdown(f"chunks_count: `{request.chunks_count}`")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"Time To First Token (TTFT): `{request.first_token_latency_ms}`"
            )
        with col2:
            st.markdown(f"Time between Token (TBT): `{request.last_token_latency_ms}`")
        with col3:
            st.markdown(f"request_latency_ms: `{request.request_latency_ms}`")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"created_at_fmt: `{request.created_at_fmt}`")
        with col2:
            st.markdown(f"start_req_time_fmt: `{request.start_req_time_fmt}`")
        with col3:
            st.markdown(f"end_req_time_fmt: `{request.end_req_time_fmt}`")
        with col4:
            st.markdown(f"completed_at_fmt: `{request.completed_at_fmt}`")

        st.markdown("input:")
        st.text_area(
            label="input: ",
            value=json.dumps(task.messages, indent=2, ensure_ascii=False),
            height=250,
            disabled=True,
            label_visibility="hidden",
        )

        st.markdown("output:")
        st.text_area(
            label="response: ",
            value=request.response,
            height=250,
            disabled=True,
            label_visibility="hidden",
        )

    render_chunks(task_id, request_id, "🚀 Chunks")

    render_logs(task_id, request_id, "📒 Logs")


def render_chunks(task_id: int, request_id: str, title):
    """Render a table of chunks associated with a request.

    Args:
        task_id: ID of the task
        request_id: ID of the request to show chunks for
        title: Title to display above the chunks table
    """
    try:
        chunks = load_all_chunks(task_id, request_id)
        chunk_list = []

        for chunk in chunks:
            chunk_list.append(
                {
                    "created_at": chunk.created_at_fmt,
                    "chunk_index": chunk.chunk_index,
                    "chunk_content": chunk.chunk_content,
                    "token_len": chunk.token_len,
                    "request_latency_ms": chunk.request_latency_ms,
                    "last_token_latency_ms": chunk.last_token_latency_ms,
                }
            )

        count = len(chunks)
        if count > 0:
            st.markdown(f"## {title} ({count})")
            st.dataframe(chunk_list, use_container_width=True)
    except Exception as e:
        st.error(e)


def render_logs(task_id: int, request_id: str, title):
    """Render a table of chunks associated with a request.

    Args:
        task_id: ID of the task
        request_id: ID of the request to show chunks for
        title: Title to display above the chunks table
    """
    try:
        logs = load_all_logs(task_id, request_id)
        log_list = []

        for log in logs:
            log_list.append(
                {
                    "Created At": log.created_at_fmt,
                    "Log Message": log.log_message,
                    "Log Data": log.log_data,
                }
            )

        count = len(logs)
        if count > 0:
            st.markdown(f"## {title} ({count})")
            st.dataframe(log_list, use_container_width=True)
    except Exception as e:
        st.error(e)
