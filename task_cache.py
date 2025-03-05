import os
from dotenv import load_dotenv
import json
from redis import Redis
from logger import logger
from tables import (
    create_chunk_table_class,
    create_log_table_class,
    create_request_table_class,
)

requests_queue_name = "requests"
chunks_queue_name = "chunks"
logs_queue_name = "logs"

load_dotenv()


class TaskCache:
    def __init__(self):
        self.redis: Redis = self.connect()
        logger.info("TaskCache initialized")

    def get_task(self, task_id: int):
        return self.redis.get(f"task_{task_id}")

    def delete_task(self, task_id: int):
        return self.redis.delete(f"task_{task_id}")

    def update_task_status(self, task_id: int, status: int):
        self.redis.set(f"task_{task_id}", status)

    def to_dict(self, obj):
        return {
            column.name: getattr(obj, column.name) for column in obj.__table__.columns
        }

    def serialize(self, task):
        task_dict = self.to_dict(task)
        return json.dumps(task_dict)

    def deserialize(self, task_dict, instance):
        for key, value in task_dict.items():
            setattr(instance, key, value)
        return instance

    def request_enqueue(self, task):
        task_json = self.serialize(task)
        self.redis.rpush(requests_queue_name, task_json)

    def request_dequeue(self):
        if task_json := self.redis.lpop(requests_queue_name):
            task_dict = json.loads(task_json.decode("utf-8"))
            Requests = create_request_table_class(task_dict["task_id"])
            return self.deserialize(task_dict, Requests())
        return None

    def request_len(self) -> int:
        return self.redis.llen(requests_queue_name)

    def chunk_enqueue(self, task):
        task_json = self.serialize(task)
        self.redis.rpush(chunks_queue_name, task_json)

    def chunk_dequeue(self):
        if task_json := self.redis.lpop(chunks_queue_name):
            task_dict = json.loads(task_json.decode("utf-8"))
            Chunks = create_chunk_table_class(task_dict["task_id"])
            return self.deserialize(task_dict, Chunks())
        return None

    def chunk_len(self) -> int:
        return self.redis.llen(chunks_queue_name)

    def log_enqueue(self, task):
        task_json = self.serialize(task)
        self.redis.rpush(logs_queue_name, task_json)

    def log_dequeue(self):
        if task_json := self.redis.lpop(logs_queue_name):
            task_dict = json.loads(task_json.decode("utf-8"))
            Logs = create_log_table_class(task_dict["task_id"])
            return self.deserialize(task_dict, Logs())
        return None

    def log_len(self) -> int:
        return self.redis.llen(logs_queue_name)

    def len(self):
        return self.request_len() + self.chunk_len() + self.log_len()

    def close(self):
        self.redis.close()

    def connect(self):
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", 6379)
        pwd = os.getenv("REDIS_PWD", "")
        if pwd:
            return Redis(host=host, port=port, db=0, password=pwd)
        return Redis(host=host, port=port, db=0)

    def reset(self):
        self.close()
        self.redis = self.connect()
