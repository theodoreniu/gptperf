import datetime
import uuid
from dotenv import load_dotenv
from openai import AzureOpenAI
import tiktoken
from sqlalchemy import update
from helper import so_far_ms, time_now
from tables import TaskRequestChunkTable, TaskRequestTable
from task_loads import TaskTable, sql_string
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import traceback
from config import aoai, ds
from ollama import chat, pull, Client

load_dotenv()


engine = create_engine(sql_string)


class TaskRuntime:

    def __init__(
        self,
        task: TaskTable,
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

    def num_tokens_from_messages(self, task: TaskTable):
        messages = task.query
        tokens_per_message = 3
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(value))
        num_tokens += 3
        return num_tokens

    def deal_aoai(self, task_request: TaskRequestChunkTable, session) -> TaskRequestChunkTable:
        response = self.client.chat.completions.create(
            messages=self.task.query,
            model=self.task.model_id,
            stream=True,
            temperature=self.task.temperature,
            max_tokens=self.task.content_length
        )

        for chunk in response:
            if len(chunk.choices) == 0:
                continue

            task_chunk = TaskRequestChunkTable(
                task_id=self.task.id,
                thread_num=self.thread_num,
                request_id=task_request.id,
                token_len=0,
                characters_len=0,
                created_at=time_now(),
            )

            if not task_request.first_token_latency_ms:
                task_request.first_token_latency_ms = so_far_ms(
                    task_request.start_req_time)
                task_chunk.last_token_latency_ms = 0
                self.last_token_time = time_now()
            else:
                task_chunk.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )

            task_request.chunks_count += 1

            delta = chunk.choices[0].delta
            task_chunk.chunk_content = delta.content

            if task_chunk.chunk_content:
                print(task_chunk.chunk_content, end="", flush=True)
                task_request.response += task_chunk.chunk_content
                task_chunk.token_len += len(
                    self.encoding.encode(task_chunk.chunk_content))
                task_chunk.characters_len += len(task_chunk.chunk_content)

                task_request.output_token_count += len(
                    self.encoding.encode(task_chunk.chunk_content))

            task_chunk.request_latency_ms = so_far_ms(
                task_request.start_req_time
            )

            task_chunk.chunk_index = task_request.chunks_count

            self.last_token_time = time_now()

            session.add(task_chunk)
            session.commit()
        return task_request

    def deal_ds(self, task_request: TaskRequestChunkTable, session) -> TaskRequestChunkTable:

        client = Client(
            host=self.task.azure_endpoint,
            headers={
                'api-key': self.task.api_key
            },
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
            task_chunk = TaskRequestChunkTable(
                task_id=self.task.id,
                thread_num=self.thread_num,
                request_id=task_request.id,
                token_len=0,
                characters_len=0,
                created_at=time_now(),
            )

            if not task_request.first_token_latency_ms:
                task_request.first_token_latency_ms = so_far_ms(
                    task_request.start_req_time)
                task_chunk.last_token_latency_ms = 0
                self.last_token_time = time_now()
            else:
                task_chunk.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )

            task_chunk.chunk_content = chunk['message']['content']

            if task_chunk.chunk_content:
                print(task_chunk.chunk_content, end="", flush=True)
                task_request.response += task_chunk.chunk_content
                task_chunk.token_len += len(
                    self.encoding.encode(task_chunk.chunk_content))
                task_chunk.characters_len += len(task_chunk.chunk_content)

                task_request.output_token_count += len(
                    self.encoding.encode(task_chunk.chunk_content))

            task_request.chunks_count += 1

            task_chunk.request_latency_ms = so_far_ms(
                task_request.start_req_time
            )

            task_chunk.chunk_index = task_request.chunks_count

            self.last_token_time = time_now()

            session.add(task_chunk)
            session.commit()
        return task_request

    def latency(self):

        Session = sessionmaker(bind=engine)
        session = Session()

        task_request = TaskRequestTable(
            id=uuid.uuid4(),
            task_id=self.task.id,
            thread_num=self.thread_num,
            response="",
            chunks_count=0,
            created_at=time_now(),
            output_token_count=0,
            request_index=self.request_index
        )

        try:
            task_request.input_token_count = self.num_tokens_from_messages(
                self.task)

            task_request.start_req_time = time_now()

            if self.task.model_type == aoai:
                task_request = self.deal_aoai(task_request, session)
            else:
                task_request = self.deal_ds(task_request, session)

            task_request.end_req_time = time_now()
            task_request.request_latency_ms = (
                task_request.end_req_time - task_request.start_req_time)

            if task_request.first_token_latency_ms:
                task_request.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )

            task_request.success = 1
            session.execute(
                update(TaskTable).where(TaskTable.id == self.task.id).values(
                    request_succeed=TaskTable.request_succeed + 1)
            )
        except Exception as e:
            task_request.success = 0
            task_request.response = f"{e}"
            session.execute(
                update(TaskTable).where(TaskTable.id == self.task.id).values(
                    request_failed=TaskTable.request_failed + 1)
            )
            traceback.print_exc()

        task_request.completed_at = time_now()
        session.add(task_request)
        session.commit()
