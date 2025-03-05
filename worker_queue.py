from time import sleep
from helper import get_mysql_session
from logger import logger
from tables import Tasks
from theodoretools.bot import feishu_text
from config import APP_URL
import copy
from sqlalchemy import update
from sqlalchemy.orm.session import Session
from task_cache import TaskCache


def check_status(db: Session, task_id: int):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()

    target_requests = task.request_per_thread * task.threads
    total_requested = task.request_succeed + task.request_failed

    if task.request_failed == target_requests:
        db.execute(
            update(Tasks)
            .where(Tasks.id == task_id)
            .values(status=3, error_message="All requests failed")
        )
        db.commit()

        if task.feishu_token:
            feishu_text(
                f"All requests failed task: {task.name}: {APP_URL}/?task_id={task.id}",
                task.feishu_token,
            )
        return

    if total_requested == target_requests:
        db.execute(
            update(Tasks).where(Tasks.id == task_id).values(status=4, error_message="")
        )
        db.commit()
        if task.feishu_token:
            feishu_text(
                f"Task {task.name} succeed: {APP_URL}/?task_id={task.id}",
                task.feishu_token,
            )
        return


if __name__ == "__main__":

    db = get_mysql_session()
    cache = TaskCache()

    while True:

        try:
            chunk = cache.chunk_dequeue()
            if chunk:
                # logger.info(chunk.__dict__)
                db.add(copy.deepcopy(chunk))
                db.commit()

            log = cache.log_dequeue()
            if log:
                # logger.info(log.__dict__)
                db.add(copy.deepcopy(log))
                db.commit()

            request = cache.request_dequeue()
            if request:
                # logger.info(request.__dict__)
                db.add(copy.deepcopy(request))
                db.commit()

                if request.success == 1:
                    db.execute(
                        update(Tasks)
                        .where(Tasks.id == request.task_id)
                        .values(request_succeed=Tasks.request_succeed + 1)
                    )
                    db.commit()
                else:
                    db.execute(
                        update(Tasks)
                        .where(Tasks.id == request.task_id)
                        .values(request_failed=Tasks.request_failed + 1)
                    )
                    db.commit()

                check_status(db, request.task_id)

            if not chunk and not request:
                sleep(1)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            cache.reset()
            db.rollback()
            db.close()
            db = get_mysql_session()
