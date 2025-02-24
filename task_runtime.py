from time import sleep
from dotenv import load_dotenv
import tiktoken
from helper import data_id, redis_client, so_far_ms, time_now
from serialize import request_enqueue
from config import aoai, ds, ds_foundry, not_support_stream
from azure.core.exceptions import HttpResponseError
from tables import Tasks
from logger import logger
from openai import AzureOpenAI, OpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import SystemMessage, UserMessage

from serialize import chunk_enqueue
from ollama import Client
from tables import Chunks, Requests
from task_loads import find_task


load_dotenv()


class TaskRuntime:

    def __init__(
        self,
        task: Tasks,
        thread_num: int,
        encoding: tiktoken.Encoding,
        request_index: int
    ):
        self.task = task
        self.last_token_time = None
        self.thread_num = thread_num
        self.encoding = encoding
        self.request_index = request_index
        self.redis = redis_client()
        self.stream = False if self.task.model_id in not_support_stream else True

    def num_tokens_from_messages(self, task: Tasks):
        if task.model_type != aoai:
            return 0

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
            task = find_task(self.task.id)
            if task.status == 5:
                raise Exception("Task stoped")

            request.input_token_count = self.num_tokens_from_messages(
                self.task
            )

            request.start_req_time = time_now()

            if self.task.model_type == aoai:
                request = self.deal_aoai(request)
            elif self.task.model_type == ds:
                request = self.deal_ds(request)
            elif self.task.model_type == ds_foundry:
                request = self.deal_ds_foundry(request)
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
        finally:
            request.completed_at = time_now()
            request_enqueue(self.redis, request)

    def deal_ds(self, request: Requests) -> Requests:

        client = Client(
            host=self.task.azure_endpoint,
            headers={
                'api-key': self.task.api_key if self.task.api_key else ''
            },
            timeout=self.task.timeout / 1000,
        )

        stream = client.chat(
            model=self.task.model_id,
            messages=self.task.query,
            stream=True,
            options={
                "temperature": self.task.temperature
            },
        )

        for chunk in stream:
            task_chunk = Chunks(
                id=data_id(),
                task_id=self.task.id,
                thread_num=self.thread_num,
                request_id=request.id,
                token_len=0,
                characters_len=0,
                created_at=time_now(),
                user_id=self.task.user_id,
                chunk_content=chunk['message']['content'],
            )

            if not request.first_token_latency_ms:
                request.first_token_latency_ms = so_far_ms(
                    request.start_req_time)
                task_chunk.last_token_latency_ms = 0
                self.last_token_time = time_now()
            else:
                task_chunk.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )
                self.last_token_time = time_now()

            if task_chunk.chunk_content:
                logger.info(task_chunk.chunk_content)
                request.response += task_chunk.chunk_content
                task_chunk.token_len += len(
                    self.encoding.encode(task_chunk.chunk_content))
                task_chunk.characters_len += len(task_chunk.chunk_content)

                request.output_token_count += len(
                    self.encoding.encode(task_chunk.chunk_content))

            request.chunks_count += 1

            task_chunk.request_latency_ms = so_far_ms(
                request.start_req_time
            )

            task_chunk.chunk_index = request.chunks_count

            chunk_enqueue(self.redis, task_chunk)

        return request

    def deal_ds_foundry(self, request: Requests) -> Requests:

        client = ChatCompletionsClient(
            endpoint=self.task.azure_endpoint,
            credential=AzureKeyCredential(self.task.api_key),
        )

        response = client.complete(
            stream=True,
            messages=[
                SystemMessage(content=self.task.system_prompt),
                UserMessage(content=self.task.user_prompt)
            ],
            max_tokens=self.task.content_length,
            model=self.task.model_id,
            temperature=self.task.temperature,
            timeout=self.task.timeout / 1000,
        )

        for update in response:

            if update.choices:

                task_chunk = Chunks(
                    id=data_id(),
                    task_id=self.task.id,
                    thread_num=self.thread_num,
                    request_id=request.id,
                    token_len=0,
                    characters_len=0,
                    created_at=time_now(),
                    user_id=self.task.user_id,
                    chunk_content=update.choices[0].delta.content,
                )

                if not request.first_token_latency_ms:
                    request.first_token_latency_ms = so_far_ms(
                        request.start_req_time)
                    task_chunk.last_token_latency_ms = 0
                    self.last_token_time = time_now()
                else:
                    task_chunk.last_token_latency_ms = so_far_ms(
                        self.last_token_time
                    )
                    self.last_token_time = time_now()

                if task_chunk.chunk_content:

                    logger.info(task_chunk.chunk_content)

                    request.response += task_chunk.chunk_content
                    task_chunk.token_len += len(
                        self.encoding.encode(task_chunk.chunk_content))
                    task_chunk.characters_len += len(task_chunk.chunk_content)

                    request.output_token_count += len(
                        self.encoding.encode(task_chunk.chunk_content))

                request.chunks_count += 1

                task_chunk.request_latency_ms = so_far_ms(
                    request.start_req_time
                )

                task_chunk.chunk_index = request.chunks_count

                chunk_enqueue(self.redis, task_chunk)

        client.close()

        return request

    def deal_aoai(self, request: Requests) -> Requests:

        client = AzureOpenAI(
            api_version=self.task.api_version,
            azure_endpoint=self.task.azure_endpoint,
            azure_deployment=self.task.deployment_name,
            api_key=self.task.api_key,
            timeout=self.task.timeout / 1000,
        )

        response = None

        if self.task.model_id in ["o3-mini", "o1-mini", "o1"]:
            response = client.chat.completions.create(
                messages=self.task.query,
                model=self.task.model_id,
                stream=self.stream,
                # TODO not support yet
                # temperature=self.task.temperature,
                max_completion_tokens=self.task.content_length
            )
        else:
            response = client.chat.completions.create(
                messages=self.task.query,
                model=self.task.model_id,
                stream=self.stream,
                temperature=self.task.temperature,
                max_tokens=self.task.content_length
            )

        if not self.stream:
            request.response = response.choices[0].message.content

            request.first_token_latency_ms = so_far_ms(
                request.start_req_time
            )

            request.request_latency_ms = so_far_ms(
                request.start_req_time
            )

            request.chunks_count = 1

            request.output_token_count += len(
                self.encoding.encode(request.response)
            )

        if self.stream:
            for chunk in response:
                if len(chunk.choices) == 0:
                    continue

                task_chunk = Chunks(
                    id=data_id(),
                    task_id=self.task.id,
                    thread_num=self.thread_num,
                    request_id=request.id,
                    token_len=0,
                    characters_len=0,
                    created_at=time_now(),
                    user_id=self.task.user_id,
                    chunk_content=chunk.choices[0].delta.content,
                )

                if not request.first_token_latency_ms:
                    request.first_token_latency_ms = so_far_ms(
                        request.start_req_time)
                    task_chunk.last_token_latency_ms = 0
                    self.last_token_time = time_now()
                else:
                    task_chunk.last_token_latency_ms = so_far_ms(
                        self.last_token_time
                    )
                    self.last_token_time = time_now()

                request.chunks_count += 1

                if task_chunk.chunk_content:
                    logger.info(task_chunk.chunk_content)
                    request.response += task_chunk.chunk_content
                    task_chunk.token_len += len(
                        self.encoding.encode(task_chunk.chunk_content))
                    task_chunk.characters_len += len(task_chunk.chunk_content)

                    request.output_token_count += len(
                        self.encoding.encode(task_chunk.chunk_content))

                task_chunk.request_latency_ms = so_far_ms(
                    request.start_req_time
                )

                task_chunk.chunk_index = request.chunks_count

                chunk_enqueue(self.redis, task_chunk)

        client.close()

        return request
