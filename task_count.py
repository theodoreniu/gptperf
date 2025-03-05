import traceback
import streamlit as st
from task_loads import sql_query
from tables import Tasks
from logger import logger


def report_number(sql_string: str, index: int):

    try:
        res = sql_query(sql_string)
        for item in res:
            if item[index] is None:
                return "N/A"
            return int(item[index])
    except Exception as e:
        logger.error(e)
        error_info = traceback.format_exc()
        st.error(error_info, icon="🚨")

    return "N/A"


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
