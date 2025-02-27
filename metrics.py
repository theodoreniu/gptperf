"""Provides statistical metrics calculation functions for task performance analysis."""

import numpy as np
import streamlit as st
from task_loads import sql_query
from tables import Tasks
from config import not_support_stream
from logger import logger


def format_number(number: int):
    return number
    # return f"{number:,}"


def report_number(sql_string: str, index: int):
    """Calculate statistical metrics from SQL query results.

    Args:
        sql_string: SQL query to execute
        index: Column index to analyze from results

    Returns:
        dict: Statistical metrics including percentiles, avg, min, max
    """
    try:
        logger.info(sql_string)

        res = sql_query(sql_string)

        if request_count := [int(item[index]) for item in res]:

            return {
                "P50": format_number(int(np.percentile(request_count, 50))),
                "P90": format_number(int(np.percentile(request_count, 90))),
                "P99": format_number(int(np.percentile(request_count, 99))),
                "P999": format_number(int(np.percentile(request_count, 99.9))),
                "Avg": format_number(int(np.mean(request_count))),
                "Min": format_number(min(request_count)),
                "Max": format_number(max(request_count)),
            }

    except Exception as e:
        logger.error(e)
        st.error(e)

    return {
        "P50": None,
        "P90": None,
        "P99": None,
        "P999": None,
        "Avg": None,
        "Min": None,
        "Max": None,
    }


def task_metrics(task: Tasks):
    """Generate performance metrics for a given task.

    Args:
        task: Task object containing execution details

    Returns:
        dict: Collection of performance metrics
    """
    stream = task.model_id not in not_support_stream

    chunks = f"chunks_{task.id}"
    requests = f"requests_{task.id}"

    if stream:
        return {
            "Concurrency": report_number(
                f"SELECT COUNT(DISTINCT thread_num) AS request_count FROM {requests}",
                0,
            ),
            "Threads Per Sec": report_number(
                f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, COUNT(DISTINCT thread_num) AS request_count FROM {chunks} GROUP BY timestamp_seconds ORDER BY timestamp_seconds",
                1,
            ),
            "Threads Per Minute": report_number(
                f"SELECT ROUND((created_at / 60000)) AS timestamp_seconds, COUNT(DISTINCT thread_num) AS request_count FROM {chunks} GROUP BY timestamp_seconds ORDER BY timestamp_seconds",
                1,
            ),
            "Requests Per Sec": report_number(
                f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, COUNT(DISTINCT id) AS request_count FROM {requests} WHERE success = 1 GROUP BY timestamp_seconds ORDER BY timestamp_seconds",
                1,
            ),
            "Request Per Minute": report_number(
                f"SELECT ROUND((created_at / 60000)) AS timestamp_seconds, COUNT(DISTINCT id) AS request_count FROM {requests} WHERE success = 1 GROUP BY timestamp_seconds ORDER BY timestamp_seconds",
                1,
            ),
            "Input Token Per Sec": report_number(
                f"SELECT ROUND((start_req_time / 1000)) AS timestamp_seconds, sum(input_token_count) AS input_token_count FROM {requests} WHERE success = 1 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
                1,
            ),
            "Input Token Per Minute": report_number(
                f"SELECT ROUND((start_req_time / 60000)) AS timestamp_seconds, sum(input_token_count) AS input_token_count FROM {requests} WHERE success = 1 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
                1,
            ),
            "Output Token Per Sec": report_number(
                f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, sum(token_len) AS token_count FROM {chunks} WHERE token_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
                1,
            ),
            "Output Token Per Minute": report_number(
                f"SELECT ROUND((created_at / 60000)) AS timestamp_seconds, sum(token_len) AS token_count FROM {chunks} WHERE token_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
                1,
            ),
            "Output Characters Per Sec": report_number(
                f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, sum(characters_len) AS characters_count FROM {chunks} WHERE characters_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
                1,
            ),
            "Output Characters Per Minute": report_number(
                f"SELECT ROUND((created_at / 60000)) AS timestamp_seconds, sum(characters_len) AS characters_count FROM {chunks} WHERE characters_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
                1,
            ),
            "Time To First Token (TTFT) Per Request": report_number(
                f"SELECT first_token_latency_ms FROM {requests} WHERE first_token_latency_ms is not null;",
                0,
            ),
            "Time Between Tokens (TBT) Per Request": report_number(
                f"SELECT last_token_latency_ms FROM {requests} WHERE last_token_latency_ms is not null;",
                0,
            ),
            "Request Latency Per Request": report_number(
                f"SELECT request_latency_ms FROM {requests} WHERE request_latency_ms is not null;",
                0,
            ),
            "Input Token Per Request": report_number(
                f"SELECT input_token_count FROM {requests} WHERE success = 1 and input_token_count is not null;",
                0,
            ),
            "Chunks Per Request": report_number(
                f"SELECT chunks_count FROM {requests} WHERE success = 1 and chunks_count is not null;",
                0,
            ),
            "Output Token Per Request": report_number(
                f"SELECT output_token_count FROM {requests} WHERE success = 1 and output_token_count is not null;",
                0,
            ),
        }

    return {
        "Concurrency": report_number(
            f"SELECT ROUND((start_req_time / 1000)) AS timestamp_seconds, COUNT(DISTINCT thread_num) AS request_count FROM {requests} WHERE start_req_time is not null GROUP BY timestamp_seconds ORDER BY timestamp_seconds",
            1,
        ),
        "Request Per Sec": report_number(
            f"SELECT ROUND((start_req_time / 1000)) AS timestamp_seconds, COUNT(DISTINCT id) AS request_count FROM {requests} WHERE start_req_time is not null GROUP BY timestamp_seconds ORDER BY timestamp_seconds",
            1,
        ),
        "Output Token Per Sec": report_number(
            f"SELECT ROUND((start_req_time / 1000)) AS timestamp_seconds, sum(output_token_count) AS token_count FROM {requests} WHERE start_req_time is not null and output_token_count > 0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;",
            1,
        ),
        "Time To First Token (TTFT)": report_number(
            f"SELECT first_token_latency_ms FROM {requests} WHERE first_token_latency_ms is not null;",
            0,
        ),
        "Time Between Tokens (TBT)": report_number(
            f"SELECT last_token_latency_ms FROM {requests} WHERE last_token_latency_ms is not null;",
            0,
        ),
        "Request Latency": report_number(
            f"SELECT request_latency_ms FROM {requests} WHERE request_latency_ms is not null;",
            0,
        ),
        "Chunks Count": report_number(
            f"SELECT chunks_count FROM {requests} WHERE success = 1 and chunks_count is not null;",
            0,
        ),
        "Output Token Count": report_number(
            f"SELECT output_token_count FROM {requests} WHERE success = 1 and output_token_count is not null;",
            0,
        ),
    }
