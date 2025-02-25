
import streamlit as st
from dotenv import load_dotenv
from helper import get_mysql_session
from tables import create_request_table_class
from task_loads import current_user, is_admin, load_all_chunks


load_dotenv()


def request_page(task_id: int, request_id: str):

    request = None

    session = get_mysql_session()
    Requests = create_request_table_class(task_id)

    if is_admin():
        request = session.query(
            Requests
        ).filter(
            Requests.id == request_id
        ).first()
    else:
        request = session.query(
            Requests
        ).filter(
            Requests.id == request_id,
            Requests.user_id == current_user().id
        ).first()

    session.close()

    if not request:
        st.error("request not found")
        return

    st.markdown(f"## 🌍 Request `{request.id}`")
    with st.container(
        border=True
    ):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"user_id: `{request.user_id}`")
        with col2:
            st.markdown(f"task_id: `{request.task_id}`")
        with col3:
            st.markdown(f"success: `{request.success}`")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"input_token_count: `{request.input_token_count}`")
        with col2:
            st.markdown(f"output_token_count: `{request.output_token_count}`")
        with col3:
            st.markdown(f"chunks_count: `{request.chunks_count}`")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"first_token_latency_ms: `{request.first_token_latency_ms}`")
        with col2:
            st.markdown(
                f"last_token_latency_ms: `{request.last_token_latency_ms}`")
        with col3:
            st.markdown(f"request_latency_ms: `{request.request_latency_ms}`")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"thread_num: `{request.thread_num}`")
        with col2:
            st.markdown(f"request_index: `{request.request_index}`")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"created_at_fmt: `{request.created_at_fmt}`")
        with col2:
            st.markdown(f"completed_at_fmt: `{request.completed_at_fmt}`")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"start_req_time_fmt: `{request.start_req_time_fmt}`")
        with col2:
            st.markdown(f"end_req_time_fmt: `{request.end_req_time_fmt}`")

        st.markdown(f"response:")
        st.text_area(
            label="response: ",
            value=request.response,
            height=250,
            disabled=True,
            label_visibility="hidden"
        )

    render_chunks(task_id, request_id, '🚀 Chunks')


def render_chunks(task_id: int, request_id: str,  title):
    try:
        chunks = load_all_chunks(task_id, request_id)

        list = []

        for chunk in chunks:
            list.append({
                "id": chunk.id,
                "created_at": chunk.created_at_fmt,
                "chunk_index": chunk.chunk_index,
                "chunk_content": chunk.chunk_content,
                "token_len": chunk.token_len,
                "request_latency_ms": chunk.request_latency_ms,
                "last_token_latency_ms": chunk.last_token_latency_ms
            })

        count = len(chunks)
        if count > 0:
            st.markdown(f"## {title} ({count})")
            st.dataframe(list, use_container_width=True)
    except Exception as e:
        st.error(e)
