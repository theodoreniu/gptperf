import json
from redis import Redis

from helper import redis_client
from tables import (
    create_chunk_table_class,
    create_log_table_class,
    create_request_table_class,
)


from logger import logger

requests_queue_name = "requests"
chunks_queue_name = "chunks"
logs_queue_name = "logs"


def to_dict(obj):
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}


def serialize(task):
    task_dict = to_dict(task)
    return json.dumps(task_dict)


def deserialize(task_dict, instance):
    for key, value in task_dict.items():
        setattr(instance, key, value)
    return instance


def request_enqueue(redis_client: Redis, task):
    task_json = serialize(task)
    redis_client.rpush(requests_queue_name, task_json)


def request_dequeue(redis_client: Redis):
    if task_json := redis_client.lpop(requests_queue_name):
        task_dict = json.loads(task_json.decode("utf-8"))
        Requests = create_request_table_class(task_dict["task_id"])
        return deserialize(task_dict, Requests())
    return None


def request_len() -> int:
    redis = redis_client()
    return redis.llen(requests_queue_name)


def chunk_enqueue(redis_client: Redis, task):
    task_json = serialize(task)
    redis_client.rpush(chunks_queue_name, task_json)


def chunk_dequeue(redis_client: Redis):
    if task_json := redis_client.lpop(chunks_queue_name):
        task_dict = json.loads(task_json.decode("utf-8"))
        Chunks = create_chunk_table_class(task_dict["task_id"])
        return deserialize(task_dict, Chunks())
    return None


def chunk_len() -> int:
    redis = redis_client()
    return redis.llen(chunks_queue_name)


def log_enqueue(redis_client: Redis, task):
    task_json = serialize(task)
    redis_client.rpush(logs_queue_name, task_json)


def log_dequeue(redis_client: Redis):
    if task_json := redis_client.lpop(logs_queue_name):
        task_dict = json.loads(task_json.decode("utf-8"))
        Logs = create_log_table_class(task_dict["task_id"])
        return deserialize(task_dict, Logs())
    return None


def log_len() -> int:
    redis = redis_client()
    return redis.llen(logs_queue_name)


def redis_len():
    return request_len() + chunk_len() + log_len()
