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

        request = Requests(
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
            request.input_token_count = self.num_tokens_from_messages(
                self.task)

            request.start_req_time = time_now()

            if self.task.model_type == aoai:
                request = deal_aoai(self, request)
            elif self.task.model_type == ds:
                request = deal_ds(self, request)
            elif self.task.model_type == ds_foundry:
                request = deal_ds_foundry(self, request)
            else:
                raise Exception(
                    f"Model type {self.task.model_type} not supported")

            request.end_req_time = time_now()
            request.request_latency_ms = (
                request.end_req_time - request.start_req_time)

            if request.first_token_latency_ms:
                request.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )

            request.success = 1

        except Exception as e:
            request.success = 0
            request.response = f"{e}"
            logger.error(f'Error: {e}', exc_info=True)

        request.completed_at = time_now()
        request_enqueue(self.redis, request)
