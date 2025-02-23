from dotenv import load_dotenv
import tiktoken
from helper import data_id, redis_client, so_far_ms, time_now
from serialize import request_enqueue
from config import aoai, ds, ds_foundry
from tables import Requests
from tables import Tasks
from logger import logger
from task_runtime_aoai import deal_aoai
from task_runtime_ds import deal_ds
from task_runtime_ds_foundry import deal_ds_foundry

load_dotenv()


class TaskRuntime:

    def __init__(
        self,
        task: Tasks,
        thread_num: int,
        encoding: tiktoken.Encoding,
        client,
        request_index: int
    ):
        self.task = task
        self.last_token_time = None
        self.thread_num = thread_num
        self.encoding = encoding
        self.client = client
        self.request_index = request_index
        self.redis = redis_client()

    def num_tokens_from_messages(self, task: Tasks):
        messages = task.query
        tokens_per_message = 3
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(value))
        num_tokens += 3
        return num_tokens

    def latency(self):

        task_request = Requests(
            id=data_id(),
            task_id=self.task.id,
            thread_num=self.thread_num,
            response="",
            chunks_count=0,
            created_at=time_now(),
            output_token_count=0,
            request_index=self.request_index,
            user_id=self.task.user_id,
        )

        try:
            task_request.input_token_count = self.num_tokens_from_messages(
                self.task)

            task_request.start_req_time = time_now()

            if self.task.model_type == aoai:
                task_request = deal_aoai(self, task_request)
            elif self.task.model_type == ds:
                task_request = deal_ds(self, task_request)
            elif self.task.model_type == ds_foundry:
                task_request = deal_ds_foundry(self, task_request)
            else:
                raise Exception(
                    f"Model type {self.task.model_type} not supported")

            task_request.end_req_time = time_now()
            task_request.request_latency_ms = (
                task_request.end_req_time - task_request.start_req_time)

            if task_request.first_token_latency_ms:
                task_request.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )

            task_request.success = 1

        except Exception as e:
            task_request.success = 0
            task_request.response = f"{e}"
            logger.error(f'Error: {e}', exc_info=True)

        task_request.completed_at = time_now()
        request_enqueue(self.redis, task_request)
