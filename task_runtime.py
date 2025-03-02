import traceback
from dotenv import load_dotenv
import redis
import tiktoken
from helper import pad_number, so_far_ms, time_now
from serialize import request_enqueue
from config import MODEL_TYPE_API, aoai, ds, ds_foundry, not_support_stream
from tables import (
    Tasks,
    create_chunk_table_class,
    create_log_table_class,
    create_request_table_class,
)
from logger import logger
from openai import AzureOpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from serialize import chunk_enqueue, log_enqueue
from ollama import Client
from task_loads import find_task
import threading
import requests
import json
import uuid

load_dotenv()


class TaskRuntime:

    def __init__(
        self, task: Tasks, thread_num: int, request_index: int, redis: redis.Redis
    ):
        self.task = task
        self.last_token_time = None
        self.thread_num = thread_num
        self.request_index = request_index
        self.redis = redis
        self.stream = False if self.task.model_id in not_support_stream else True
        self.Chunks = create_chunk_table_class(task.id)
        self.Logs = create_log_table_class(task.id)

        Requests = create_request_table_class(task.id)
        self.request = Requests(
            id=f"{pad_number(thread_num, task.threads)}{pad_number(request_index, task.request_per_thread)}",
            task_id=self.task.id,
            thread_num=self.thread_num,
            response="",
            chunks_count=0,
            created_at=time_now(),
            output_token_count=0,
            request_index=self.request_index,
            user_id=self.task.user_id,
        )
        self.log(f"Request {self.request.id} started")

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
        log_enqueue(self.redis, log_item)

    def run_with_timeout(self, method, timeout):
        event = threading.Event()
        error_info = None

        def target():
            nonlocal error_info
            try:
                method()
            except Exception as e:
                error_info = traceback.format_exc()
            finally:
                event.set()

        thread = threading.Thread(target=target)
        thread.start()

        event.wait(timeout)

        if thread.is_alive():
            raise TimeoutError(f"Timeout occurred while executing {method.__name__}")
        elif error_info:
            raise Exception(f"An error occurred in {method.__name__}:\n{error_info}")

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

        try:
            encoding = tiktoken.get_encoding("cl100k_base")

            if self.task.model_type == aoai:
                encoding = tiktoken.encoding_for_model(self.task.model_id)
            else:
                encoding = tiktoken.encoding_for_model("gpt-4o")

            return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return 0

    def latency(self):

        try:
            task = find_task(self.task.id)
            if not task:
                raise Exception("Task not found or was deleted")

            if task.status == 5:
                raise Exception("Task stoped")

            self.request.input_token_count = self.num_tokens_from_messages()

            self.request.start_req_time = time_now()

            timeout = self.task.timeout / 1000
            if self.task.model_type == aoai:
                self.run_with_timeout(self.request_aoai, timeout)
            elif self.task.model_type == ds:
                self.run_with_timeout(self.request_ds, timeout)
            elif self.task.model_type == ds_foundry:
                self.run_with_timeout(self.request_ds_foundry, timeout)
            elif self.task.model_type == MODEL_TYPE_API:
                self.run_with_timeout(self.request_api, timeout)
            else:
                raise Exception(f"Model type {self.task.model_type} not supported")

            self.request.end_req_time = time_now()
            self.request.request_latency_ms = (
                self.request.end_req_time - self.request.start_req_time
            )

            if self.request.first_token_latency_ms:
                self.request.last_token_latency_ms = so_far_ms(self.last_token_time)

            self.request.success = 1
        except TimeoutError as e:
            self.request.success = 0
            self.request.response = (
                f"No response within the limited time: {self.task.timeout} ms"
            )
            logger.error(f"Timeout Error: {e}", exc_info=True)
        except Exception as e:
            self.request.success = 0
            self.request.response = traceback.format_exc()
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            self.request.completed_at = time_now()
            request_enqueue(self.redis, self.request)

    def request_ds(self):
        self.log(f"client init start")
        client = Client(
            host=self.task.azure_endpoint,
            headers={"api-key": self.task.api_key if self.task.api_key else ""},
            timeout=self.task.timeout / 1000,
        )

        self.log(f"client request start")
        stream = client.chat(
            model=self.task.model_id,
            messages=self.task.messages_loads,
            stream=True,
            options={"temperature": self.task.temperature},
        )

        self.log(f"loop stream start")
        for chunk in stream:
            self.request.chunks_count += 1

            content = chunk["message"]["content"]
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
                logger.info(content)
                self.request.response += content
                token_len = self.encode(content)
                characters_len = len(content)

                self.request.output_token_count += token_len

            chunk_item = self.Chunks(
                id=f"{self.request.id}{pad_number(self.request.chunks_count, 1000000)}",
                chunk_index=self.request.chunks_count,
                thread_num=self.thread_num,
                task_id=self.task.id,
                request_id=self.request.id,
                token_len=token_len,
                characters_len=characters_len,
                created_at=time_now(),
                chunk_content=content,
                request_latency_ms=so_far_ms(self.request.start_req_time),
                last_token_latency_ms=last_token_latency_ms,
            )

            chunk_enqueue(self.redis, chunk_item)

        self.log(f"loop stream end")

    def request_ds_foundry(self):
        self.log(f"client init start")
        client = ChatCompletionsClient(
            endpoint=self.task.azure_endpoint,
            credential=AzureKeyCredential(self.task.api_key),
        )

        self.log(f"client request start")
        response = client.complete(
            stream=True,
            messages=self.task.messages_loads,
            max_tokens=self.task.content_length,
            model=self.task.model_id,
            temperature=self.task.temperature,
            timeout=self.task.timeout / 1000,
        )

        self.log(f"loop stream start")
        for update in response:

            if update.choices:
                self.request.chunks_count += 1

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

                content = update.choices[0].delta.content

                token_len = 0
                characters_len = 0

                if content:

                    logger.info(content)

                    self.request.response += content
                    token_len = self.encode(content)
                    characters_len = len(content)

                    self.request.output_token_count += token_len

                task_chunk = self.Chunks(
                    id=f"{self.request.id}{pad_number(self.request.chunks_count, 1000000)}",
                    chunk_index=self.request.chunks_count,
                    thread_num=self.thread_num,
                    task_id=self.task.id,
                    request_id=self.request.id,
                    token_len=token_len,
                    characters_len=characters_len,
                    created_at=time_now(),
                    chunk_content=content,
                    request_latency_ms=so_far_ms(self.request.start_req_time),
                    last_token_latency_ms=last_token_latency_ms,
                )

                chunk_enqueue(self.redis, task_chunk)

        self.log(f"loop stream end")
        client.close()

    def request_aoai(self):
        self.log(f"client init start")
        client = AzureOpenAI(
            api_version=self.task.api_version,
            azure_endpoint=self.task.azure_endpoint,
            azure_deployment=self.task.deployment_name,
            api_key=self.task.api_key,
            timeout=self.task.timeout / 1000,
        )

        self.log(f"client request start")
        response = None

        if self.task.model_id in ["o3-mini", "o1-mini", "o1"]:
            response = client.chat.completions.create(
                messages=self.task.messages_loads,
                model=self.task.model_id,
                stream=self.stream,
                # temperature=self.task.temperature,
                max_completion_tokens=self.task.content_length,
            )
        else:
            response = client.chat.completions.create(
                messages=self.task.messages_loads,
                model=self.task.model_id,
                stream=self.stream,
                temperature=self.task.temperature,
                max_tokens=self.task.content_length,
            )

        self.log(f"loop stream start")
        if not self.stream:
            self.request.response = response.choices[0].message.content

            self.request.first_token_latency_ms = so_far_ms(self.request.start_req_time)

            self.request.request_latency_ms = so_far_ms(self.request.start_req_time)

            self.request.chunks_count = 1

            self.request.output_token_count = self.encode(self.request.response)

        if self.stream:
            for chunk in response:
                if len(chunk.choices) == 0:
                    continue

                self.request.chunks_count += 1
                content = chunk.choices[0].delta.content

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
                    logger.info(content)

                    self.request.response += content

                    token_len = self.encode(content)
                    characters_len = len(content)

                    self.request.output_token_count += token_len

                task_chunk = self.Chunks(
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

                chunk_enqueue(self.redis, task_chunk)

        self.log(f"loop stream end")
        client.close()

    def request_api(self):
        self.log(f"client init start")
        headers = {"Content-Type": "application/json"}

        data = {
            "model": self.task.model_id,
            "prompt": "What is the largest planet?",
            "max_tokens": self.task.content_length,
            "stream": True,
        }

        self.log(f"client request start", data)
        response = requests.post(
            url=self.task.azure_endpoint,
            headers=headers,
            data=json.dumps(data),
            stream=True,
            timeout=self.task.timeout / 1000,
        )

        self.log(f"client response start")
        logger.info(response.text)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    self.request.response += line
                    logger.info(chunk)
        else:
            logger.error(response)

        self.log(f"loop stream end")
        return
        client = AzureOpenAI(
            api_version=self.task.api_version,
            azure_endpoint=self.task.azure_endpoint,
            azure_deployment=self.task.deployment_name,
            api_key=self.task.api_key,
            timeout=self.task.timeout / 1000,
        )

        response = client.chat.completions.create(
            messages=self.task.messages_loads,
            model=self.task.model_id,
            stream=self.stream,
            temperature=self.task.temperature,
            max_tokens=self.task.content_length,
        )

        if not self.stream:
            self.request.response = response.choices[0].message.content

            self.request.first_token_latency_ms = so_far_ms(self.request.start_req_time)

            self.request.request_latency_ms = so_far_ms(self.request.start_req_time)

            self.request.chunks_count = 1

            self.request.output_token_count = self.encode(self.request.response)

        if self.stream:
            for chunk in response:
                if len(chunk.choices) == 0:
                    continue

                self.request.chunks_count += 1
                content = chunk.choices[0].delta.content

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
                    logger.info(content)

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

                chunk_enqueue(self.redis, task_chunk)

        client.close()
