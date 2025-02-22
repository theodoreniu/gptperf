

import os

from typing import List
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from tables import TaskRequestChunkTable, TaskRequestTable, TaskTable

load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DB")

sql_string = f'mysql+pymysql://{user}:{password}@{host}/{database}'

engine = create_engine(sql_string)


def sql_query(sql: str):
    print(sql)

    Session = sessionmaker(bind=engine)
    session = Session()
    session.execute(text(sql))

    return session.execute(text(sql))


def truncate_table(table_name: str):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.execute(text(f"TRUNCATE TABLE {table_name};"))
    session.commit()


def sql_commit(sql: str):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.execute(text(sql))
    session.commit()


def update_status(task: TaskTable, status: int):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(TaskTable).filter(
        TaskTable.id == task.id).update({TaskTable.status: status})
    session.commit()


def queue_task(task: TaskTable):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(TaskTable).filter(
        TaskTable.id == task.id).update(
            {
                TaskTable.status: 1,
                TaskTable.request_succeed: 0,
                TaskTable.request_failed: 0,
            }
    )
    session.commit()


def run_task(task: TaskTable):
    update_status(task, 2)


def error_task(task: TaskTable, message: str):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(
        TaskTable
    ).filter(
        TaskTable.id == task.id
    ).update(
        {
            TaskTable.status: 3,
            TaskTable.error_message: message,
        }
    )
    session.commit()


def succeed_task(task: TaskTable):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(TaskTable).filter(
        TaskTable.id == task.id
    ).update(
        {
            TaskTable.status: 4,
            TaskTable.error_message: "",
        }
    )
    session.commit()


def delete_task(task: TaskTable):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.delete(task)
    session.commit()


def delete_task_data(task: TaskTable):
    sql_commit(
        f'delete from {TaskRequestTable.__tablename__} where task_id = {task.id}')
    sql_commit(
        f'delete from {TaskRequestChunkTable.__tablename__} where task_id = {task.id}')


def add_task(task: TaskTable) -> TaskTable:
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(task)
    session.commit()
    return task


def load_all_tasks() -> List[TaskTable]:
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(
        TaskTable
    ).order_by(
        TaskTable.created_at.desc()
    ).all()

    session.close()

    return results


def load_all_requests(task: TaskTable, success: int) -> List[TaskRequestTable]:
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(
        TaskRequestTable
    ).filter(
        TaskRequestTable.task_id == task.id,
        TaskRequestTable.success == success
    ).order_by(
        TaskRequestTable.request_index.desc()
    ).limit(
        10000
    ).all()

    session.close()

    return results


def load_all_chunks(request: TaskRequestChunkTable) -> List[TaskRequestChunkTable]:
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(
        TaskRequestChunkTable
    ).filter(
        TaskRequestChunkTable.request_id == request.id,
    ).order_by(
        TaskRequestChunkTable.created_at.asc()
    ).limit(
        10000
    ).all()

    session.close()

    return results


def load_queue_tasks() -> List[TaskTable]:
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(
        TaskTable
    ).filter(
        TaskTable.status == 1
    ).order_by(
        TaskTable.created_at.desc()
    ).limit(1).all()

    session.close()

    return results


def find_task(task_id: int) -> TaskTable | None:
    Session = sessionmaker(bind=engine)
    session = Session()
    task = session.query(
        TaskTable
    ).filter(
        TaskTable.id == task_id
    ).first()

    session.close()

    return task


def find_request(request_id: int) -> TaskRequestTable | None:
    Session = sessionmaker(bind=engine)
    session = Session()
    request = session.query(
        TaskRequestTable
    ).filter(
        TaskRequestTable.id == request_id
    ).first()

    session.close()

    return request
