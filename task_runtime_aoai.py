from dotenv import load_dotenv
from helper import data_id, so_far_ms, time_now
from serialize import chunk_enqueue
from logger import logger
from tables import Chunks, Requests

load_dotenv()


def deal_aoai(runtime, request: Requests) -> Requests:
    response = runtime.client.chat.completions.create(
        messages=runtime.task.query,
        model=runtime.task.model_id,
        stream=True,
        temperature=runtime.task.temperature,
        max_tokens=runtime.task.content_length
    )

    for chunk in response:
        if len(chunk.choices) == 0:
            continue

        task_chunk = Chunks(
            id=data_id(),
            task_id=runtime.task.id,
            thread_num=runtime.thread_num,
            request_id=request.id,
            token_len=0,
            characters_len=0,
            created_at=time_now(),
            user_id=runtime.task.user_id,
            chunk_content=chunk.choices[0].delta.content,
        )

        if not request.first_token_latency_ms:
            request.first_token_latency_ms = so_far_ms(
                request.start_req_time)
            task_chunk.last_token_latency_ms = 0
            runtime.last_token_time = time_now()
        else:
            task_chunk.last_token_latency_ms = so_far_ms(
                runtime.last_token_time
            )
            runtime.last_token_time = time_now()

        request.chunks_count += 1

        if task_chunk.chunk_content:
            logger.info(task_chunk.chunk_content)
            request.response += task_chunk.chunk_content
            task_chunk.token_len += len(
                runtime.encoding.encode(task_chunk.chunk_content))
            task_chunk.characters_len += len(task_chunk.chunk_content)

            request.output_token_count += len(
                runtime.encoding.encode(task_chunk.chunk_content))

        task_chunk.request_latency_ms = so_far_ms(
            request.start_req_time
        )

        task_chunk.chunk_index = request.chunks_count

        chunk_enqueue(runtime.redis, task_chunk)

    return request
