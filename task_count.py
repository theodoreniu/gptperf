import streamlit as st
from task_loads import sql_query
from tables import Tasks
from logger import logger


def format_number(number: int):
    return number
    # return f"{number:,}"


def report_number(sql_string: str, index: int):

    try:
        res = sql_query(sql_string)
        if request_count := [int(item[index]) for item in res]:
            return request_count[0]
    except Exception as e:
        logger.error(e)
        st.error(e)

    return {}


def task_count(task: Tasks):

    requests = f"requests_{task.id}"

    return {
        "Duration Seconds": report_number(
            f"SELECT (MAX(end_req_time) - MIN(start_req_time)) / 1000 AS seconds FROM {requests};",
            0,
        ),
        "Input Token Total": report_number(
            f"SELECT SUM(input_token_count) AS input_token_count FROM {requests}",
            0,
        ),
        "Output Token Total": report_number(
            f"SELECT SUM(output_token_count) AS output_token_count FROM {requests}",
            0,
        ),
    }
