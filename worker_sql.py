from time import sleep
from helper import get_mysql_session, redis_client


import logging

from sqlalchemy import text, update
from serialize import chunk_dequeue, request_dequeue
from tables import TaskTable


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    session = get_mysql_session()
    redis_client = redis_client()

    while (True):
        chunk = chunk_dequeue(redis_client)
        if chunk:
            logger.info(chunk.__dict__)
            session.add(chunk)
            session.commit()

        request = request_dequeue(redis_client)
        if request:
            logger.info(request.__dict__)
            session.add(request)
            session.commit()

            if request.success:
                session.execute(
                    update(
                        TaskTable
                    ).where(
                        TaskTable.id == request.task_id
                    ).values(
                        request_succeed=TaskTable.request_succeed + 1
                    )
                )
            else:
                session.execute(
                    update(
                        TaskTable
                    ).where(
                        TaskTable.id == request.task_id
                    ).values(
                        request_failed=TaskTable.request_failed + 1
                    )
                )

        if not chunk and not request:
            logger.info("sleep 5 seconds for sql...")
            sleep(5)
