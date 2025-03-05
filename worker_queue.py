from time import sleep
from helper import get_mysql_session, redis_client
from serialize import chunk_dequeue, request_dequeue, log_dequeue
from logger import logger
from tables import Tasks
from task_loads import (
    error_task,
    succeed_task,
)
from theodoretools.bot import feishu_text
from config import APP_URL
import copy
from sqlalchemy import update


def check_status(session, task_id: int):
    task = session.query(Tasks).filter(Tasks.id == task_id).first()

    target_requests = task.request_per_thread * task.threads
    total_requested = task.request_succeed + task.request_failed

    if task.request_failed == target_requests:
        error_task(task, "All requests failed")
        if task.feishu_token:
            feishu_text(
                f"All requests failed task: {task.name}: {APP_URL}/?task_id={task.id}",
                task.feishu_token,
            )
        return

    if total_requested == target_requests:
        succeed_task(task)
        if task.feishu_token:
            feishu_text(
                f"Task {task.name} succeed: {APP_URL}/?task_id={task.id}",
                task.feishu_token,
            )
        return


if __name__ == "__main__":

    session = get_mysql_session()
    redis = redis_client()

    while True:

        try:
            chunk = chunk_dequeue(redis)
            if chunk:
                # logger.info(chunk.__dict__)
                session.add(copy.deepcopy(chunk))
                session.commit()

            log = log_dequeue(redis)
            if log:
                # logger.info(log.__dict__)
                session.add(copy.deepcopy(log))
                session.commit()

            request = request_dequeue(redis)
            if request:
                # logger.info(request.__dict__)
                session.add(copy.deepcopy(request))
                session.commit()

                if request.success == 1:
                    session.execute(
                        update(Tasks)
                        .where(Tasks.id == request.task_id)
                        .values(request_succeed=Tasks.request_succeed + 1)
                    )
                    session.commit()
                else:
                    session.execute(
                        update(Tasks)
                        .where(Tasks.id == request.task_id)
                        .values(request_failed=Tasks.request_failed + 1)
                    )
                    session.commit()

                check_status(session, request.task_id)

            if not chunk and not request:
                sleep(1)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            session.rollback()
            session.close()
            redis.close()
            session = get_mysql_session()
            redis = redis_client()
