from time import sleep
from helper import redis_client
from serialize import chunk_dequeue, request_dequeue
from logger import logger
from task_loads import add_chunk, add_request, error_task, find_task, succeed_task, task_request_failed, task_request_succeed
from theodoretools.bot import feishu_text


def check_status(task_id: int):
    task = find_task(task_id)

    target_requests = task.request_per_thread * task.threads
    total_requested = task.request_succeed + task.request_failed

    if task.request_failed == target_requests:
        error_task(task, "All requests failed")
        if task.feishu_token:
            feishu_text(
                f"All requests failed task: {task.name}",
                task.feishu_token
            )
        return

    if total_requested == target_requests:
        succeed_task(task)
        if task.feishu_token:
            feishu_text(
                f"Task {task.name} succeed",
                task.feishu_token
            )
        return


if __name__ == "__main__":

    while (True):

        redis = redis_client()

        try:
            chunk = chunk_dequeue(redis)
            if chunk:
                logger.info(chunk.__dict__)
                add_chunk(chunk)

            request = request_dequeue(redis)
            if request:
                logger.info(request.__dict__)
                add_request(request)

                if request.success == 1:
                    task_request_succeed(request.task_id)
                else:
                    task_request_failed(request.task_id)

                check_status(request.task_id)

            if not chunk and not request:
                sleep(1)

        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
        finally:
            redis.close()
