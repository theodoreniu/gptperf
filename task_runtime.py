import traceback
from dotenv import load_dotenv
import tiktoken
from helper import pad_number, so_far_ms, time_now
from tables import (
    Tasks,
    create_chunk_table_class,
    create_log_table_class,
    create_request_table_class,
)
from logger import logger
import uuid
import requests
import json
from task_cache import TaskCache

load_dotenv()


class TaskRuntime:

    def __init__(
        self, task: Tasks, thread_num: int, request_index: int, cache: TaskCache
    ):
        self.task = task
        self.last_token_time = None
        self.thread_num = thread_num
        self.request_index = request_index
        self.cache = cache
        self.stream = bool(self.task.stream)
        self.Chunks = create_chunk_table_class(task.id)
        self.Logs = create_log_table_class(task.id)

        Requests = create_request_table_class(task.id)
        self.request = Requests(
            id=f"{pad_number(thread_num, task.threads)}{pad_number(request_index, task.request_per_thread)}",
            task_id=self.task.id,
            thread_num=self.thread_num,
            response="",
            chunks_count=0,
            success=1,
            created_at=time_now(),
            output_token_count=0,
            request_index=self.request_index,
            user_id=self.task.user_id,
        )
        self.log("request created")

    def log(self, log_message: str, log_data: dict = None):
        log_item = self.Logs(
            id=f"{uuid.uuid4()}",
            task_id=self.task.id,
            thread_num=self.thread_num,
            request_id=self.request.id,
            log_message=log_message,
            log_data=log_data,
            created_at=time_now(),
        )
        self.cache.log_enqueue(log_item)

    def num_tokens_from_messages(self):
        tokens_per_message = 3
        num_tokens = 0
        for message in self.task.messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if value:
                    num_tokens += self.encode(value)
        num_tokens += 3
        return num_tokens

    def encode(self, text):
        if not text:
            return 0

        encoding = tiktoken.get_encoding("cl100k_base")

        try:
            encoding = tiktoken.encoding_for_model(self.task.model_id)
            return len(encoding.encode(text))
        except Exception as e:
            # todo: update this
            logger.error(f"Error encoding text: {e}")
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            return len(encoding.encode(text))

    def latency(self):

        try:
            task_status = self.cache.get_task(self.task.id)
            if not task_status:
                raise Exception("Task not found or was deleted")

            if int(task_status) == 5:
                raise Exception("Task was stopped")

            self.request.input_token_count = self.num_tokens_from_messages()

            self.request.start_req_time = time_now()

            self.request_api()

            self.request.end_req_time = time_now()
            self.request.request_latency_ms = (
                self.request.end_req_time - self.request.start_req_time
            )

            if self.request.first_token_latency_ms:
                self.request.last_token_latency_ms = so_far_ms(self.last_token_time)
        except TimeoutError as e:
            self.request.success = 0
            self.request.response = f"timeout: {self.task.timeout} ms"
            logger.error(f"Timeout Error: {e}", exc_info=True)
        except Exception as e:
            self.request.success = 0
            self.request.response = traceback.format_exc()
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            self.request.completed_at = time_now()
            self.cache.request_enqueue(self.request)

    def request_api(self):
        self.log(f"client init start")

        headers = {
            "Content-Type": "application/json",
            # sglang
            "Authorization": f"Bearer {self.task.api_key}",
            # aoai
            "api-key": self.task.api_key or "",
        }

        data = {
            "model": self.task.model_id,
            "messages": self.task.messages_loads,
            "stream": self.stream,
        }

        if not self.task.enable_think:
            data["format"] = "json"

        if self.task.model_id in ["o3-mini", "o1-mini", "o1"]:
            data["max_completion_tokens"] = self.task.max_tokens
        else:
            data["max_tokens"] = self.task.max_tokens
            data["temperature"] = self.task.temperature

        self.request.data = data

        response = requests.post(
            url=self.task.azure_endpoint,
            headers=headers,
            json=data,
            timeout=self.task.timeout / 1000,
            stream=self.stream,
        )

        if response.status_code > 300:
            self.request.response = response.text
            self.request.success = 0
            self.request.completed_at = time_now()
            return

        if not self.stream:
            response = json.loads(response.text)
            self.request.response = response["choices"][0]["message"]["content"]
            self.request.first_token_latency_ms = so_far_ms(self.request.start_req_time)
            self.request.request_latency_ms = so_far_ms(self.request.start_req_time)
            self.request.chunks_count = 1
            self.request.output_token_count = self.encode(self.request.response)
            return

        self.log(f"loop stream start")
        for line in response.iter_lines():
            if not line:
                continue

            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data: "):
                decoded_line = decoded_line[len("data: ") :]
            if decoded_line.strip() == "[DONE]":
                break
            if decoded_line:
                chunk = json.loads(decoded_line)

                if len(chunk["choices"]) == 0:
                    continue

                self.request.chunks_count += 1

                if (
                    "delta" not in chunk["choices"][0]
                    or "content" not in chunk["choices"][0]["delta"]
                ):
                    continue

                content = chunk["choices"][0]["delta"]["content"]

                last_token_latency_ms = None
                if not self.request.first_token_latency_ms:
                    self.request.first_token_latency_ms = so_far_ms(
                        self.request.start_req_time
                    )
                    last_token_latency_ms = 0
                    self.last_token_time = time_now()
                else:
                    last_token_latency_ms = so_far_ms(self.last_token_time)
                    self.last_token_time = time_now()

                token_len = 0
                characters_len = 0
                if content:
                    # logger.info(content)

                    self.request.response += content

                    token_len = self.encode(content)
                    characters_len = len(content)

                    self.request.output_token_count += token_len

                Chunks = create_chunk_table_class(self.task.id)

                task_chunk = Chunks(
                    id=f"{self.request.id}{pad_number(self.request.chunks_count, 1000000)}",
                    chunk_index=self.request.chunks_count,
                    thread_num=self.thread_num,
                    task_id=self.task.id,
                    request_id=self.request.id,
                    token_len=token_len,
                    characters_len=characters_len,
                    created_at=time_now(),
                    chunk_content=content,
                    last_token_latency_ms=last_token_latency_ms,
                    request_latency_ms=so_far_ms(self.request.start_req_time),
                )

                self.cache.chunk_enqueue(task_chunk)

        self.log(f"loop stream end")
