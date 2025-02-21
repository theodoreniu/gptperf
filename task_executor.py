
import json
import os
from task_loads import TaskTable, error_task, succeed_task
from task_runtime import TaskRuntime
from theodoretools.bot import feishu_text
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from config import aoai, ds
import traceback
import tiktoken
from openai import AzureOpenAI


def safe_create_and_run_task(task: TaskTable, thread_num: int,  encoding: tiktoken.Encoding, client):
    task_runtime = TaskRuntime(
        task=task, thread_num=thread_num, encoding=encoding, client=client)
    task_runtime.latency()


def task_executor(task: TaskTable):

    if task.feishu_token:
        feishu_text(
            f"start to run {task.source_location} {task.target_location} {task.request_per_thread} {task.threads} {task.deployment_type} {task.model_id}",
            task.feishu_token
        )

    encoding = tiktoken.get_encoding("cl100k_base")

    if task.model_type == aoai:
        encoding = tiktoken.encoding_for_model(task.model_id)
    else:
        # todo: change to ds
        encoding = tiktoken.encoding_for_model('gpt-4o')

    client = AzureOpenAI(
        api_version=task.api_version,
        azure_endpoint=task.azure_endpoint,
        azure_deployment=task.deployment_name,
        api_key=task.api_key,
    )

    with ThreadPoolExecutor(max_workers=task.threads) as executor:
        futures = [
            executor.submit(safe_create_and_run_task, task,
                            thread_index + 1, encoding, client)
            for thread_index in range(task.threads)
            for _ in range(task.request_per_thread)
        ]

    for future in futures:
        try:
            future.result()
            succeed_task(task)
        except Exception as e:
            print(f"Threads Failed: {e}")

    return
    # get min latency, max latency, p50, p90, p99
    with open(task.log_file, "r") as f:
        data = [json.loads(line) for line in f]

        # count times
        times = len(data)

        first_token_latency_ms = [
            item["first_token_latency_ms"] for item in data]
        last_token_latency_ms = [
            item["last_token_latency_ms"] for item in data]
        response_latency_ms = [item["response_latency_ms"]
                               for item in data]
        cost_req_time_ms = [item['cost_req_time'] for item in data]
        input_token_count = [item['input_token_count'] for item in data]
        output_token_count = [item['output_token_count'] for item in data]

        tokens_every_second_data = []
        for item in data:
            tokens_every_second_data.extend(
                item["tokens_every_second_data"])

        characters_every_second_data = []
        for item in data:
            characters_every_second_data.extend(
                item["characters_every_second_data"])

        with open(task.report_file, "a") as f:
            f.write(
                f"\n=================== base information ===================")
            f.write(f"\nsource_location: {task.source_location}")
            f.write(f"\ntarget_location: {task.target_location}")
            f.write(f"\request_per_thread: {task.request_per_thread}")
            f.write(f"\nnum_threads: {task.threads}")
            f.write(f"\nmodel id: {os.getenv('AZURE_MODEL_ID')}")
            f.write(f"\nDeployment type: Global Standard")
            f.write(
                f"\n2M tokens per minute quota available for your deployment")
            f.write(f"\n===================")
            f.write(
                f"\nMin first token latency: {int(min(first_token_latency_ms))}")
            f.write(
                f"\nMax first token latency: {int(max(first_token_latency_ms))}")
            f.write(f"\n===================")
            f.write(
                f"\nMin last token latency from first token: {int(min(last_token_latency_ms))}"
            )
            f.write(
                f"\nMax last token latency from first token: {int(max(last_token_latency_ms))}"
            )
            f.write(f"\n===================")
            f.write(
                f"\nMin response latency: {int(min(response_latency_ms))}")
            f.write(
                f"\nMax response latency: {int(max(response_latency_ms))}")
            f.write(f"\n===================")
            f.write(
                f"\nMin tokens every second: {int(min(tokens_every_second_data))}")
            # f.write(f"\nAvg tokens every second: {int(avg(tokens_every_second_data))}")
            f.write(
                f"\nMax tokens every second: {int(max(tokens_every_second_data))}")
            f.write(f"\n===================")
            f.write(
                f"\nMin characters every second: {int(min(characters_every_second_data))}"
            )
            # f.write(f"\nAvg characters every second: {int(avg(characters_every_second_data))}")
            f.write(
                f"\nMax characters every second: {int(max(characters_every_second_data))}"
            )

            # get first token latency p50, p90, p99
            f.write(f"\n===================")
            f.write(
                f"\nP50 first token latency: {int(np.percentile(first_token_latency_ms, 50))}"
            )
            f.write(
                f"\nP90 first token latency: {int(np.percentile(first_token_latency_ms, 90))}"
            )
            f.write(
                f"\nP99 first token latency: {int(np.percentile(first_token_latency_ms, 99))}"
            )
            f.write(
                f"\nP999 first token latency: {int(np.percentile(first_token_latency_ms, 99.9))}"
            )

            # get last token latency p50, p90, p99
            f.write(f"\n===================")
            f.write(
                f"\nP50 last token latency: {int(np.percentile(last_token_latency_ms, 50))}"
            )
            f.write(
                f"\nP90 last token latency: {int(np.percentile(last_token_latency_ms, 90))}"
            )
            f.write(
                f"\nP99 last token latency: {int(np.percentile(last_token_latency_ms, 99))}"
            )
            f.write(
                f"\nP999 last token latency: {int(np.percentile(last_token_latency_ms, 99.9))}"
            )

            # get response latency p50, p90, p99
            f.write(f"\n===================")
            f.write(
                f"\nP50 response latency: {int(np.percentile(response_latency_ms, 50))}"
            )
            f.write(
                f"\nP90 response latency: {int(np.percentile(response_latency_ms, 90))}"
            )
            f.write(
                f"\nP99 response latency: {int(np.percentile(response_latency_ms, 99))}"
            )
            f.write(
                f"\nP999 response latency: {int(np.percentile(response_latency_ms, 99.9))}"
            )

            f.write(f"\n===================")
            f.write(
                f"\nP50 tokens every second: {int(np.percentile(tokens_every_second_data, 50))}"
            )
            f.write(
                f"\nP90 tokens every second: {int(np.percentile(tokens_every_second_data, 90))}"
            )
            f.write(
                f"\nP99 tokens every second: {int(np.percentile(tokens_every_second_data, 99))}"
            )
            f.write(
                f"\nP999 tokens every second: {int(np.percentile(tokens_every_second_data, 99.9))}"
            )

            f.write(f"\n===================")
            f.write(
                f"\nP50 characters every second: {int(np.percentile(characters_every_second_data, 50))}"
            )
            f.write(
                f"\nP90 characters every second: {int(np.percentile(characters_every_second_data, 90))}"
            )
            f.write(
                f"\nP99 characters every second: {int(np.percentile(characters_every_second_data, 99))}"
            )
            f.write(
                f"\nP999 characters every second: {int(np.percentile(characters_every_second_data, 99.9))}"
            )
            f.write(f"\n===================")
            f.write(f"\nRequest Times: {len(cost_req_time_ms)}")
            f.write(f"\nAvg latency ms: {int(np.mean(cost_req_time_ms))}")
            f.write(
                f"\nP50 latency ms: {int(np.percentile(cost_req_time_ms, 50))}")
            f.write(
                f"\nP99 latency ms: {int(np.percentile(cost_req_time_ms, 99))}")

            f.write(f"\n===================")
            f.write(f"\nInput tokens: {int(np.sum(input_token_count))}")
            f.write(f"\nOutput tokens: {int(np.sum(output_token_count))}")

        feishu_text(task.report_file)
