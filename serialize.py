import json
from redis import Redis
import logging
from tables.chunks import Chunks
from tables.requests import Requests


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


def deserialize(task_json, instance) -> Requests | Chunks:
    task_dict = json.loads(task_json.decode('utf-8'))
    for key, value in task_dict.items():
        setattr(instance, key, value)
    return instance


def request_enqueue(redis_client: Redis, task: Requests):
    task_json = serialize(task)
    redis_client.rpush(requests_queue_name, task_json)


def request_dequeue(redis_client: Redis) -> Requests | None:
    task_json = redis_client.lpop(requests_queue_name)
    if task_json:
        task = deserialize(task_json, Requests())
        return task
    return None


def chunk_enqueue(redis_client: Redis, task: Chunks):
    task_json = serialize(task)
    redis_client.rpush(chunks_queue_name, task_json)


def chunk_dequeue(redis_client: Redis) -> Chunks | None:
    task_json = redis_client.lpop(chunks_queue_name)
    if task_json:
        task = deserialize(task_json, Chunks())
        return task
    return None
