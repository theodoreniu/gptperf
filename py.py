import json
import sys
from dotenv import load_dotenv
import numpy as np
import os
from task import GptTask
from concurrent.futures import ThreadPoolExecutor
import argparse
from config import user_prompt
from theodoretools.bot import feishu_text

load_dotenv()

deployment_type = os.getenv("DEPLOYMENT_TYPE")
source_location = os.getenv("SOURCE_LOCATION")
target_location = os.getenv("TARGET_LOCATION")


def create_and_run_task(log_file):
    task = GptTask(
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_API_BASE"),
        azure_deployment=os.getenv("AZURE_API_DEPLOYMENT"),
        api_key=os.getenv("AZURE_API_KEY"),
        model=os.getenv("AZURE_MODEL_ID"),
        query=user_prompt,
        log_file=log_file,
    )
    task.latency()
    task.append_to_jsonl()


if __name__ == "__main__":
    # exit
    parser = argparse.ArgumentParser()
    parser.add_argument("request_total", help="request_total")
    parser.add_argument("num_threads", help="num_threads")
    args = parser.parse_args()

    request_total = int(args.request_total)
    num_threads = int(args.num_threads)

    log_file = f"reports/{source_location}_{target_location}_{deployment_type}_{request_total}_{num_threads}_latency.jsonl"
    report_file = f"reports/{source_location}_{target_location}_{deployment_type}_{request_total}_{num_threads}_latency.report.txt"

    if os.path.exists(log_file):
        os.remove(log_file)

    if os.path.exists(report_file):
        os.remove(report_file)

    if not os.path.exists(log_file):
        feishu_text(
            f"start to run {source_location} {target_location} {request_total} {num_threads}"
        )
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for _ in range(request_total):
                executor.submit(create_and_run_task, log_file)

    # get min latency, max latency, p50, p90, p99
    with open(log_file, "r") as f:
        data = [json.loads(line) for line in f]

        # count times
        times = len(data)

        first_token_latency_ms = [
            item["first_token_latency_ms"] for item in data]
        last_token_latency_ms = [
            item["last_token_latency_ms"] for item in data]
        response_latency_ms = [item["response_latency_ms"] for item in data]
        cost_req_time_ms = [item['cost_req_time'] for item in data]
        input_token_count = [item['input_token_count'] for item in data]
        output_token_count = [item['output_token_count'] for item in data]

        tokens_every_second_data = []
        for item in data:
            tokens_every_second_data.extend(item["tokens_every_second_data"])

        characters_every_second_data = []
        for item in data:
            characters_every_second_data.extend(
                item["characters_every_second_data"])

        with open(report_file, "a") as f:
            f.write(f"\n=================== base information ===================")
            f.write(f"\nsource_location: {source_location}")
            f.write(f"\ntarget_location: {target_location}")
            f.write(f"\nrequest_total: {request_total}")
            f.write(f"\nnum_threads: {num_threads}")
            f.write(f"\nmodel id: {os.getenv('AZURE_MODEL_ID')}")
            f.write(f"\nDeployment type: Global Standard")
            f.write(f"\n2M tokens per minute quota available for your deployment")
            f.write(f"\n===================")
            f.write(
                f"\nMin first token latency: {int(min(first_token_latency_ms))}")
            f.write(
                f"\nMax first token latency: {int(max(first_token_latency_ms))}")
            f.write(f"\n===================")
            f.write(
                f"\nMin last token latency from first token: {int(min(last_token_latency_ms))}"
            )
            f.write(
                f"\nMax last token latency from first token: {int(max(last_token_latency_ms))}"
            )
            f.write(f"\n===================")
            f.write(f"\nMin response latency: {int(min(response_latency_ms))}")
            f.write(f"\nMax response latency: {int(max(response_latency_ms))}")
            f.write(f"\n===================")
            f.write(
                f"\nMin tokens every second: {int(min(tokens_every_second_data))}")
            # f.write(f"\nAvg tokens every second: {int(avg(tokens_every_second_data))}")
            f.write(
                f"\nMax tokens every second: {int(max(tokens_every_second_data))}")
            f.write(f"\n===================")
            f.write(
                f"\nMin characters every second: {int(min(characters_every_second_data))}"
            )
            # f.write(f"\nAvg characters every second: {int(avg(characters_every_second_data))}")
            f.write(
                f"\nMax characters every second: {int(max(characters_every_second_data))}"
            )

            # get first token latency p50, p90, p99
            f.write(f"\n===================")
            f.write(
                f"\nP50 first token latency: {int(np.percentile(first_token_latency_ms, 50))}"
            )
            f.write(
                f"\nP90 first token latency: {int(np.percentile(first_token_latency_ms, 90))}"
            )
            f.write(
                f"\nP99 first token latency: {int(np.percentile(first_token_latency_ms, 99))}"
            )
            f.write(
                f"\nP999 first token latency: {int(np.percentile(first_token_latency_ms, 99.9))}"
            )

            # get last token latency p50, p90, p99
            f.write(f"\n===================")
            f.write(
                f"\nP50 last token latency: {int(np.percentile(last_token_latency_ms, 50))}"
            )
            f.write(
                f"\nP90 last token latency: {int(np.percentile(last_token_latency_ms, 90))}"
            )
            f.write(
                f"\nP99 last token latency: {int(np.percentile(last_token_latency_ms, 99))}"
            )
            f.write(
                f"\nP999 last token latency: {int(np.percentile(last_token_latency_ms, 99.9))}"
            )

            # get response latency p50, p90, p99
            f.write(f"\n===================")
            f.write(
                f"\nP50 response latency: {int(np.percentile(response_latency_ms, 50))}"
            )
            f.write(
                f"\nP90 response latency: {int(np.percentile(response_latency_ms, 90))}"
            )
            f.write(
                f"\nP99 response latency: {int(np.percentile(response_latency_ms, 99))}"
            )
            f.write(
                f"\nP999 response latency: {int(np.percentile(response_latency_ms, 99.9))}"
            )

            f.write(f"\n===================")
            f.write(
                f"\nP50 tokens every second: {int(np.percentile(tokens_every_second_data, 50))}"
            )
            f.write(
                f"\nP90 tokens every second: {int(np.percentile(tokens_every_second_data, 90))}"
            )
            f.write(
                f"\nP99 tokens every second: {int(np.percentile(tokens_every_second_data, 99))}"
            )
            f.write(
                f"\nP999 tokens every second: {int(np.percentile(tokens_every_second_data, 99.9))}"
            )

            f.write(f"\n===================")
            f.write(
                f"\nP50 characters every second: {int(np.percentile(characters_every_second_data, 50))}"
            )
            f.write(
                f"\nP90 characters every second: {int(np.percentile(characters_every_second_data, 90))}"
            )
            f.write(
                f"\nP99 characters every second: {int(np.percentile(characters_every_second_data, 99))}"
            )
            f.write(
                f"\nP999 characters every second: {int(np.percentile(characters_every_second_data, 99.9))}"
            )
            f.write(f"\n===================")
            f.write(f"\nRequest Times: {len(cost_req_time_ms)}")
            f.write(f"\nAvg latency ms: {int(np.mean(cost_req_time_ms))}")
            f.write(
                f"\nP50 latency ms: {int(np.percentile(cost_req_time_ms, 50))}")
            f.write(
                f"\nP99 latency ms: {int(np.percentile(cost_req_time_ms, 99))}")

            f.write(f"\n===================")
            f.write(f"\nInput tokens: {int(np.sum(input_token_count))}")
            f.write(f"\nOutput tokens: {int(np.sum(output_token_count))}")

        feishu_text(report_file)
