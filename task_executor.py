from tables import Tasks
from task_cache import TaskCache
from task_runtime import TaskRuntime
from theodoretools.bot import feishu_text
from concurrent.futures import ThreadPoolExecutor
from logger import logger
from config import APP_URL


def safe_create_and_run_task(
    task: Tasks, thread_num: int, request_index: int, cache: TaskCache
):
    task_runtime = TaskRuntime(
        task=task, thread_num=thread_num, request_index=request_index, cache=cache
    )
    task_runtime.latency()


def task_executor(task: Tasks):

    if task.feishu_token:
        feishu_text(
            f"start to run {task.name}: {APP_URL}/?task_id={task.id}", task.feishu_token
        )

    cache = TaskCache()

    try:
        with ThreadPoolExecutor(max_workers=task.threads) as executor:
            futures = [
                executor.submit(
                    safe_create_and_run_task,
                    task,
                    thread_index + 1,
                    request_index + 1,
                    cache,
                )
                for thread_index in range(task.threads)
                for request_index in range(task.request_per_thread)
            ]

            for future in futures:
                try:
                    logger.info(future.result())
                except Exception as e:
                    logger.error(f"Threads Error: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Task Error: {e}", exc_info=True)
        raise e
    finally:
        cache.close()
