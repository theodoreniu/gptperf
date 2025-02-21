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

load_dotenv()


engine = create_engine(sql_string)


class TaskRuntime:

    def __init__(
        self,
        task: TaskTable,
        thread_num: int,
        encoding: tiktoken.Encoding,
        client
    ):
        self.task = task
        self.last_token_time = None
        self.thread_num = thread_num
        self.encoding = encoding
        self.client = client

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

    def latency(self):
        print(f"Task {self.task.id}")

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
        )

        try:
            task_request.input_token_count = self.num_tokens_from_messages(
                self.task)

            task_request.start_req_time = time_now()

            response = self.client.chat.completions.create(
                messages=self.task.query,
                model=self.task.model_id,
                stream=True,
            )

            self.last_token_time = time_now()

            for chunk in response:
                if len(chunk.choices) > 0:

                    task_chunk = TaskRequestChunkTable(
                        task_id=self.task.id,
                        thread_num=self.thread_num,
                        request_id=task_request.id,
                        token_len=0,
                        characters_len=0,
                        created_at=time_now(),
                    )

                    delta = chunk.choices[0].delta

                    if delta.content:
                        task_request.response += delta.content
                    else:
                        print("no content")

                    # if delta.content:
                    task_request.chunks_count += 1

                    if not task_request.first_token_latency_ms:
                        task_request.first_token_latency_ms = so_far_ms(
                            task_request.created_at)

                    if delta.role:
                        print(delta.role + ": ", end="", flush=True)

                    if delta.content:
                        task_chunk.token_len += len(
                            self.encoding.encode(delta.content))
                        task_chunk.characters_len += len(delta.content)

                        print(delta.content, end="", flush=True)

                        task_request.output_token_count += len(
                            self.encoding.encode(chunk.choices[0].delta.content))

                    task_chunk.last_token_latency_ms = so_far_ms(
                        self.last_token_time
                    )

                    task_chunk.request_latency_ms = so_far_ms(
                        task_request.start_req_time
                    )

                    task_chunk.chunk_content = delta.content
                    task_chunk.chunk_index = task_request.chunks_count

                    self.last_token_time = time_now()

                    session.add(task_chunk)
                    session.commit()

            task_request.end_req_time = time_now()
            task_request.cost_req_time_ms = (
                task_request.end_req_time - task_request.start_req_time)

            if task_request.first_token_latency_ms:
                task_request.last_token_latency_ms = so_far_ms(
                    self.last_token_time
                )

                task_request.response_latency_ms = so_far_ms(
                    task_request.created_at
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
