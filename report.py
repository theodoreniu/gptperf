
from tables import Tasks
from task_loads import sql_query
import numpy as np
import streamlit as st
from config import not_support_stream
from logger import logger


def report_number(sql_string: str, index: int):
    try:
        logger.info(sql_string)

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
        logger.error(e)
        st.error(e)

    return {
        "p50": None,
        "p90": None,
        "p99": None,
        "p999": None,
        "avg": None,
        "min": None,
        "max": None,
    }


def task_report(task: Tasks):

    stream = False if task.model_id in not_support_stream else True

    chunks = f'chunks_{task.id}'
    reuqests = f'reuqests_{task.id}'

    if stream:
        return {
            "tps": report_number(f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, COUNT(DISTINCT request_id) AS request_count FROM {chunks} GROUP BY timestamp_seconds ORDER BY timestamp_seconds", 1),

            "token / second": report_number(f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, sum(token_len) AS token_count FROM {chunks} WHERE token_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;", 1),

            "characters / second": report_number(f"SELECT ROUND((created_at / 1000)) AS timestamp_seconds, sum(characters_len) AS characters_count FROM {chunks} WHERE characters_len>0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;", 1),

            "first_token_latency_ms": report_number(f"SELECT first_token_latency_ms FROM {reuqests} WHERE first_token_latency_ms is not null;", 0),

            "last_token_latency_ms": report_number(f"SELECT last_token_latency_ms FROM {reuqests} WHERE last_token_latency_ms is not null;", 0),

            "request_latency_ms": report_number(f"SELECT request_latency_ms FROM {reuqests} WHERE request_latency_ms is not null;", 0),

            "chunks_count": report_number(f"SELECT chunks_count FROM {reuqests} WHERE success = 1 and chunks_count is not null;", 0),

            "output_token_count": report_number(f"SELECT output_token_count FROM {reuqests} WHERE success = 1 and output_token_count is not null;", 0),
        }

    return {
        "tps": report_number(f"SELECT ROUND((start_req_time / 1000)) AS timestamp_seconds, COUNT(DISTINCT id) AS request_count FROM {reuqests} WHERE start_req_time is not null GROUP BY timestamp_seconds ORDER BY timestamp_seconds", 1),

        "token / second": report_number(f"SELECT ROUND((start_req_time / 1000)) AS timestamp_seconds, sum(output_token_count) AS token_count FROM {reuqests} WHERE start_req_time is not null and output_token_count > 0 GROUP BY timestamp_seconds ORDER BY timestamp_seconds;", 1),

        "first_token_latency_ms": report_number(f"SELECT first_token_latency_ms FROM {reuqests} WHERE first_token_latency_ms is not null;", 0),

        "last_token_latency_ms": report_number(f"SELECT last_token_latency_ms FROM {reuqests} WHERE last_token_latency_ms is not null;", 0),

        "request_latency_ms": report_number(f"SELECT request_latency_ms FROM {reuqests} WHERE request_latency_ms is not null;", 0),

        "chunks_count": report_number(f"SELECT chunks_count FROM {reuqests} WHERE success = 1 and chunks_count is not null;", 0),

        "output_token_count": report_number(f"SELECT output_token_count FROM {reuqests} WHERE success = 1 and output_token_count is not null;", 0),
    }
