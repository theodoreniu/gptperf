import json

from redis import Redis
from tables import TaskRequestChunkTable, TaskRequestTable


import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

requests_queue_name = 'requests'
chunks_queue_name = 'chunks'


def to_dict(obj):
    result = {}
    for column in obj.__table__.columns:
        result[column.name] = getattr(obj, column.name)
    return result


def serialize(task):
    dict = to_dict(task)

    return json.dumps(dict)


def deserialize(task_json, instance) -> TaskRequestTable | TaskRequestChunkTable:
    task_dict = json.loads(task_json.decode('utf-8'))
    for key, value in task_dict.items():
        setattr(instance, key, value)
    return instance


def request_enqueue(redis_client: Redis, task: TaskRequestTable):
    task_json = serialize(task)
    redis_client.rpush(requests_queue_name, task_json)


def request_dequeue(redis_client: Redis) -> TaskRequestTable | None:
    task_json = redis_client.lpop(requests_queue_name)
    if task_json:
        task = deserialize(task_json, TaskRequestTable())
        return task
    return None


def chunk_enqueue(redis_client: Redis, task: TaskRequestChunkTable):
    task_json = serialize(task)
    redis_client.rpush(chunks_queue_name, task_json)


def chunk_dequeue(redis_client: Redis) -> TaskRequestChunkTable | None:
    task_json = redis_client.lpop(chunks_queue_name)
    if task_json:
        task = deserialize(task_json, TaskRequestChunkTable())
        return task
    return None
