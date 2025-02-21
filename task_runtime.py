import datetime
import json
import uuid
from dotenv import load_dotenv
from openai import AzureOpenAI
import tiktoken

from tables import TaskRequestChunkTable, TaskRequestTable
from task_loads import TaskTable, sql_string
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
load_dotenv()


encoding = tiktoken.get_encoding("cl100k_base")

engine = create_engine(sql_string)
Session = sessionmaker(bind=engine)
session = Session()


def num_tokens_from_messages(task: TaskTable):
    encoding = tiktoken.encoding_for_model(task.model_id)
    messages = task.query
    tokens_per_message = 3
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    num_tokens += 3
    return num_tokens


class TaskRuntime:

    def __init__(
        self,
        task: TaskTable,
        thread_num: int,
    ):
        self.task = task
        self.task_created_at = datetime.datetime.now()
        self.first_token_latency_ms = None
        self.last_token_time = None
        self.last_token_latency_ms = None
        self.response_latency_ms = None
        self.input_token_count = 0
        self.output_token_count = 0
        self.start_req_time = None
        self.end_req_time = None
        self.thread_num = thread_num
        self.request_id = uuid.uuid4()

    def latency(self):
        print(
            f"Task {self.task.source_location} -> {self.task.target_location} -> {self.task.deployment_type}"
        )

        client = AzureOpenAI(
            api_version=self.task.api_version,
            azure_endpoint=self.task.azure_endpoint,
            azure_deployment=self.task.deployment_name,
            api_key=self.task.api_key,
        )

        self.start_req_time = datetime.datetime.now()

        self.input_token_count = num_tokens_from_messages(self.task)
        encoding = tiktoken.encoding_for_model(self.task.model_id)
        response = client.chat.completions.create(
            messages=self.task.query,
            model=self.task.model_id,
            stream=True,
        )

        response_count = 0
        self.last_token_time = datetime.datetime.now()
        response_string = ""

        for chunk in response:
            if len(chunk.choices) > 0:
                delta = chunk.choices[0].delta

                if delta.content:
                    response_string += delta.content
                else:
                    print("no content")

                # if delta.content:
                response_count += 1

                if self.first_token_latency_ms is None:
                    self.first_token_latency_ms = (
                        datetime.datetime.now() - self.task_created_at
                    ).total_seconds() * 1000

                token_len = 0
                characters_len = 0

                if delta.role:
                    print(delta.role + ": ", end="", flush=True)

                if delta.content:
                    token_len += len(encoding.encode(delta.content))
                    characters_len += len(delta.content)

                    print(delta.content, end="", flush=True)

                    self.output_token_count += len(
                        encoding.encode(chunk.choices[0].delta.content))

                last_token_latency_ms = (
                    datetime.datetime.now() - self.last_token_time
                ).total_seconds() * 1000

                request_latency_ms = (
                    datetime.datetime.now() - self.start_req_time
                ).total_seconds() * 1000

                self.last_token_time = datetime.datetime.now()

                session.add(TaskRequestChunkTable(
                    task_id=self.task.id,
                    thread_num=self.thread_num,
                    request_id=self.request_id,
                    chunk_index=response_count,
                    chunk_content=delta.content,
                    token_len=token_len,
                    characters_len=characters_len,
                    created_at=datetime.datetime.now().isoformat(),
                    last_token_latency_ms=last_token_latency_ms,
                    request_latency_ms=request_latency_ms
                ))
                session.commit()

        self.end_req_time = datetime.datetime.now()
        self.cost_req_time = (
            self.end_req_time - self.start_req_time).total_seconds() * 1000

        if self.first_token_latency_ms is not None:
            self.last_token_latency_ms = (
                datetime.datetime.now() - self.last_token_time
            ).total_seconds() * 1000
            self.response_latency_ms = (
                datetime.datetime.now() - self.task_created_at
            ).total_seconds() * 1000

        session.add(TaskRequestTable(
            id=self.request_id,
            task_id=self.task.id,
            thread_num=self.thread_num,
            response=response_string,
            created_at=self.task_created_at.isoformat(),
            completed_at=datetime.datetime.now().isoformat(),
            output_token_count=self.output_token_count,
            input_token_count=self.input_token_count,
            first_token_latency_ms=self.first_token_latency_ms,
            last_token_latency_ms=self.last_token_latency_ms,
            response_latency_ms=self.response_latency_ms,
            cost_req_time_ms=self.cost_req_time,
            success=1,
        ))
        session.commit()
