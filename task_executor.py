
from task_loads import TaskTable, succeed_task
from task_runtime import TaskRuntime
from theodoretools.bot import feishu_text
from concurrent.futures import ThreadPoolExecutor
from config import aoai
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
