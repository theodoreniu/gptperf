from time import sleep
from helper import get_mysql_session, redis_client
from sqlalchemy import update
from serialize import chunk_dequeue, request_dequeue
from tables import Requests, Tasks
from logger import logger
from task_loads import add_chunk, add_request, error_task, succeed_task, task_request_failed, task_request_succeed


def check_status(request: Requests):
    session = get_mysql_session()
    task = session.query(
        Tasks
    ).filter(
        Tasks.id == request.task_id
    ).first()
    session.close()

    target_requests = task.request_per_thread * task.threads
    total_requested = task.request_succeed + task.request_failed

    if task.request_failed == target_requests:
        error_task(task, "All requests failed")
        return

    if total_requested == target_requests:
        succeed_task(task)
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

                if request.success:
                    task_request_succeed(request)
                else:
                    task_request_failed(request)
                check_status(request)

            if not chunk and not request:
                logger.info("waitting for sql ...")
                sleep(3)

        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            sleep(3)
        finally:
            redis.close()
