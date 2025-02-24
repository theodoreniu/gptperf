import json
from redis import Redis

from helper import redis_client
from tables import create_chunk_table_class, create_request_table_class


from logger import logger

requests_queue_name = "requests"
chunks_queue_name = "chunks"


def to_dict(obj):
    result = {}
    for column in obj.__table__.columns:
        result[column.name] = getattr(obj, column.name)
    return result


def serialize(task):
    dict = to_dict(task)

    return json.dumps(dict)


def deserialize(task_dict, instance):
    for key, value in task_dict.items():
        setattr(instance, key, value)
    return instance


def request_enqueue(redis_client: Redis, task):
    task_json = serialize(task)
    redis_client.rpush(requests_queue_name, task_json)


def request_dequeue(redis_client: Redis):
    task_json = redis_client.lpop(requests_queue_name)
    if task_json:
        task_dict = json.loads(task_json.decode("utf-8"))
        Requests = create_request_table_class(task_dict["task_id"])
        task = deserialize(task_dict, Requests())
        return task
    return None


def request_len() -> int:
    redis = redis_client()
    return redis.llen(requests_queue_name)


def chunk_enqueue(redis_client: Redis, task):
    task_json = serialize(task)
    redis_client.rpush(chunks_queue_name, task_json)


def chunk_dequeue(redis_client: Redis):
    task_json = redis_client.lpop(chunks_queue_name)
    if task_json:
        task_dict = json.loads(task_json.decode("utf-8"))
        Chunks = create_chunk_table_class(task_dict["task_id"])
        task = deserialize(task_dict, Chunks())
        return task
    return None


def chunk_len() -> int:
    redis = redis_client()
    return redis.llen(chunks_queue_name)
