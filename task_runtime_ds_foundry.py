from dotenv import load_dotenv
from helper import data_id, so_far_ms, time_now
from serialize import chunk_enqueue
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from tables import Chunks, Requests
from azure.ai.inference.models import SystemMessage, UserMessage
from logger import logger

load_dotenv()


def deal_ds_foundry(runtime, request: Requests) -> Chunks:

    client = ChatCompletionsClient(
        endpoint=runtime.task.azure_endpoint,
        credential=AzureKeyCredential(runtime.task.api_key),
    )

    response = client.complete(
        stream=True,
        messages=[
            SystemMessage(content=runtime.task.system_prompt),
            UserMessage(content=runtime.task.user_prompt)
        ],
        max_tokens=runtime.task.content_length,
        model=runtime.task.model_id,
        temperature=runtime.task.temperature,
    )

    for update in response:
        if update.choices:
            task_chunk = Chunks(
                id=data_id(),
                task_id=runtime.task.id,
                thread_num=runtime.thread_num,
                request_id=request.id,
                token_len=0,
                characters_len=0,
                created_at=time_now(),
                user_id=runtime.task.user_id,
                chunk_content=update.choices[0].delta.content,
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

            if task_chunk.chunk_content:
                logger.info(task_chunk.chunk_content)
                request.response += task_chunk.chunk_content
                task_chunk.token_len += len(
                    runtime.encoding.encode(task_chunk.chunk_content))
                task_chunk.characters_len += len(task_chunk.chunk_content)

                request.output_token_count += len(
                    runtime.encoding.encode(task_chunk.chunk_content))

            request.chunks_count += 1

            task_chunk.request_latency_ms = so_far_ms(
                request.start_req_time
            )

            task_chunk.chunk_index = request.chunks_count

            chunk_enqueue(runtime.redis, task_chunk)

    return request
