from dotenv import load_dotenv
from helper import data_id, so_far_ms, time_now
from serialize import chunk_enqueue
from ollama import Client
from tables import Chunks
from logger import logger

load_dotenv()


def deal_ds(runtime, task_request: Chunks) -> Chunks:

    client = Client(
        host=runtime.task.azure_endpoint,
        headers={
            'api-key': runtime.task.api_key
        },
    )

    stream = client.chat(
        model=runtime.task.model_id,
        messages=runtime.task.query,
        stream=True,
        options={
            "temperature": runtime.task.temperature
        },
    )

    for chunk in stream:
        task_chunk = Chunks(
            id=data_id(),
            task_id=runtime.task.id,
            thread_num=runtime.thread_num,
            request_id=task_request.id,
            token_len=0,
            characters_len=0,
            created_at=time_now(),
            user_id=runtime.task.user_id,
            chunk_content=chunk['message']['content'],
        )

        if not task_request.first_token_latency_ms:
            task_request.first_token_latency_ms = so_far_ms(
                task_request.start_req_time)
            task_chunk.last_token_latency_ms = 0
            runtime.last_token_time = time_now()
        else:
            task_chunk.last_token_latency_ms = so_far_ms(
                runtime.last_token_time
            )
            runtime.last_token_time = time_now()

        if task_chunk.chunk_content:
            logger.info(task_chunk.chunk_content)
            task_request.response += task_chunk.chunk_content
            task_chunk.token_len += len(
                runtime.encoding.encode(task_chunk.chunk_content))
            task_chunk.characters_len += len(task_chunk.chunk_content)

            task_request.output_token_count += len(
                runtime.encoding.encode(task_chunk.chunk_content))

        task_request.chunks_count += 1

        task_chunk.request_latency_ms = so_far_ms(
            task_request.start_req_time
        )

        task_chunk.chunk_index = task_request.chunks_count

        chunk_enqueue(runtime.redis, task_chunk)

    return task_request
