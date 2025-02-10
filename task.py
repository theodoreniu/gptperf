import datetime
import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import threading
import tiktoken
from config import system_prompt

load_dotenv()

file_lock = threading.Lock()
encoding = tiktoken.get_encoding("cl100k_base")

deployment_type = os.getenv("DEPLOYMENT_TYPE")

source_location = os.getenv("SOURCE_LOCATION")
target_location = os.getenv("TARGET_LOCATION")

encoding = tiktoken.encoding_for_model(os.getenv("AZURE_MODEL_ID"))


def num_tokens_from_messages(messages):
    tokens_per_message = 3
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    num_tokens += 3
    return num_tokens


class GptTask:

    def __init__(
        self,
        api_version,
        azure_endpoint,
        azure_deployment,
        api_key,
        model,
        query,
        log_file,
    ):
        self.api_version = api_version
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.api_key = api_key
        self.model = model
        self.query = query
        self.task_created_at = datetime.datetime.now()
        self.first_token_time = None
        self.first_token_latency_ms = None
        self.last_token_time = None
        self.last_token_latency_ms = None
        self.response_latency_ms = None
        self.log_file = log_file
        self.characters_every_second = {}
        self.characters_every_second_data = []
        self.tokens_every_second = {}
        self.tokens_every_second_data = []
        self.input_token_count = 0
        self.output_token_count = 0
        self.start_req_time = None
        self.end_req_time = None

    def latency(self):
        client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint,
            azure_deployment=self.azure_deployment,
            api_key=self.api_key,
        )

        self.start_req_time = datetime.datetime.now()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.query},
        ]

        self.input_token_count = num_tokens_from_messages(messages)

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.query},
            ],
            model=self.model,
            stream=True,
        )

        response_count = 0
        last_token_time2 = datetime.datetime.now()
        for chunk in response:
            if len(chunk.choices) > 0:
                delta = chunk.choices[0].delta

                if not delta.content:
                    print("no content")
                    # continue

                last_token_latency_ms = (
                    datetime.datetime.now() - last_token_time2
                ).total_seconds() * 1000
                request_latency_ms = (
                    datetime.datetime.now() - self.start_req_time
                ).total_seconds() * 1000
                last_token_time2 = datetime.datetime.now()

                # if delta.content:
                response_count += 1

                if response_count < 10:
                    with open(
                        f"reports/{source_location}_{target_location}_{deployment_type}_package_{response_count}.log",
                        "a",
                    ) as f_log:
                        f_log.write(
                            "last_token_latency_ms: "
                            + str(last_token_latency_ms)
                            + " content: "
                            + delta.content
                            + "\n"
                        )
                    with open(
                        f"reports/{source_location}_{target_location}_{deployment_type}_package_request_{response_count}.log",
                        "a",
                    ) as f_log:
                        f_log.write(
                            "request_latency_ms: "
                            + str(request_latency_ms)
                            + " content: "
                            + delta.content
                            + "\n"
                        )

                if self.first_token_time is None:
                    self.first_token_time = datetime.datetime.now()
                    self.first_token_latency_ms = (
                        self.first_token_time - self.task_created_at
                    ).total_seconds() * 1000

                # current second
                current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                if delta.role:
                    self.tokens_every_second[current_time] = (
                        self.tokens_every_second.get(current_time, 0)
                        + len(encoding.encode(delta.role))
                    )
                    self.characters_every_second[current_time] = (
                        self.characters_every_second.get(current_time, 0)
                        + len(delta.role)
                    )
                    print(delta.role + ": ", end="", flush=True)
                if delta.content:
                    self.tokens_every_second[current_time] = (
                        self.tokens_every_second.get(current_time, 0)
                        + len(encoding.encode(delta.content))
                    )
                    self.characters_every_second[current_time] = (
                        self.characters_every_second.get(current_time, 0)
                        + len(delta.content)
                    )
                    print(delta.content, end="", flush=True)
                    self.output_token_count += len(
                        encoding.encode(chunk.choices[0].delta.content))

        self.end_req_time = datetime.datetime.now()
        self.cost_req_time = (
            self.end_req_time - self.start_req_time).total_seconds() * 1000

        if self.first_token_time is not None:
            self.last_token_time = datetime.datetime.now()
            self.last_token_latency_ms = (
                self.last_token_time - self.first_token_time
            ).total_seconds() * 1000
            self.response_latency_ms = (
                self.last_token_time - self.task_created_at
            ).total_seconds() * 1000
            self.tokens_every_second_data = list(
                self.tokens_every_second.values())
            self.characters_every_second_data = list(
                self.characters_every_second.values()
            )

    def append_to_jsonl(self):
        message = json.dumps(
            {
                "api_version": self.api_version,
                "azure_endpoint": self.azure_endpoint,
                "azure_deployment": self.azure_deployment,
                "model": self.model,
                "task_created_at": self.task_created_at.isoformat(),
                "first_token_latency_ms": self.first_token_latency_ms,
                "last_token_latency_ms": self.last_token_latency_ms,
                "response_latency_ms": self.response_latency_ms,
                # "tokens_every_second": self.tokens_every_second,
                "tokens_every_second_data": self.tokens_every_second_data,
                # "characters_every_second": self.characters_every_second,
                "characters_every_second_data": self.characters_every_second_data,
                "cost_req_time": self.cost_req_time,
                "input_token_count": self.input_token_count,
                "output_token_count": self.output_token_count,
            }
        )

        with file_lock:
            with open(self.log_file, "a") as f:
                f.write(message + "\n")
