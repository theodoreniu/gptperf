from time import sleep
from helper import get_mysql_session, redis_client
from sqlalchemy.orm.session import Session
from sqlalchemy import update
from serialize import chunk_dequeue, request_dequeue
from tables import Requests, Tasks
from logger import logger
from task_loads import succeed_task


def check_status(session: Session, request: Requests):
    task = session.query(
        Tasks
    ).filter(
        Tasks.id == request.task_id
    ).first()

    target_requests = task.request_per_thread * task.threads
    total_requested = task.request_succeed + task.request_failed

    if total_requested == target_requests:
        succeed_task(session, task)


if __name__ == "__main__":

    while (True):
        session = get_mysql_session()
        redis = redis_client()

        try:
            chunk = chunk_dequeue(redis)
            if chunk:
                logger.info(chunk.__dict__)
                session.add(chunk)
                session.commit()

            request = request_dequeue(redis)
            if request:
                logger.info(request.__dict__)
                session.add(request)
                session.commit()
                if request.success:
                    session.execute(
                        update(
                            Tasks
                        ).where(
                            Tasks.id == request.task_id
                        ).values(
                            request_succeed=Tasks.request_succeed + 1
                        )
                    )
                    check_status(session, request)
                else:
                    session.execute(
                        update(
                            Tasks
                        ).where(
                            Tasks.id == request.task_id
                        ).values(
                            request_failed=Tasks.request_failed + 1
                        )
                    )
                    check_status(session, request)

            if not chunk and not request:
                logger.info("waitting for sql ...")
                sleep(3)

        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            sleep(3)
        finally:
            session.close()
            redis.close()
