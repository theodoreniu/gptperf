from task_loads import TaskTable, sql_query
import numpy as np
import streamlit as st


def report_number(sql_string: str, index: int):
    try:
        res = sql_query(sql_string)

        request_count = [int(item[index]) for item in res]

        if len(request_count) > 0:

            return {
                "p50": int(np.percentile(request_count, 50)),
                "p90": int(np.percentile(request_count, 90)),
                "p99": int(np.percentile(request_count, 99)),
                "p999": int(np.percentile(request_count, 99.9)),
                "avg": int(np.mean(request_count)),
                "min": min(request_count),
                "max": max(request_count)
            }

    except Exception as e:
        st.error(e)

    return None


def task_report(task: TaskTable):
    return {
        "tps": report_number(f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, COUNT(DISTINCT request_id) AS request_count FROM tasks_requests_chunks WHERE task_id={task.id} GROUP BY timestamp_seconds ORDER BY timestamp_seconds", 1),

        "token / second": report_number(f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, sum(token_len) AS token_count FROM tasks_requests_chunks WHERE task_id = {task.id} and token_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;", 1),

        "characters / second": report_number(f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, sum(characters_len) AS characters_count FROM tasks_requests_chunks WHERE task_id = {task.id} and characters_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;", 1),

        "first_token_latency_ms": report_number(f"SELECT first_token_latency_ms FROM tasks_requests WHERE first_token_latency_ms is not null and task_id = {task.id};", 0),

        "request_latency_ms": report_number(f"SELECT request_latency_ms FROM tasks_requests WHERE request_latency_ms is not null and task_id = {task.id};", 0),

        "chunks_count": report_number(f"SELECT chunks_count FROM tasks_requests WHERE chunks_count is not null and task_id = {task.id};", 0),

        "output_token_count": report_number(f"SELECT output_token_count FROM tasks_requests WHERE output_token_count is not null and task_id = {task.id};", 0),
    }
