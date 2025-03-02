from datetime import datetime
import os

app_url = os.getenv("APP_URL", "http://localhost:9876")

app_version = "0.0.2"

app_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

not_support_stream = [
    "o1-mini",
    # 以下 stream 为 true 不报错，只能拿到空字符串
    "o1",
    "o3-mini",
]

aoai = "AOAI"
aoai_models = ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o3", "o3-mini"]

ds = "DeepSeek (Ollama)"
ds_foundry = "DeepSeek (AI Foundry)"
ds_models = [
    "deepseek-r1:1.5b",
    "deepseek-r1:7b",
    "deepseek-r1:8b",
    "deepseek-r1:14b",
    "deepseek-r1:32b",
    "deepseek-r1:70b",
    "deepseek-r1:671b",
    "deepseek-coder:latest",
]

MODEL_TYPE_API = "API"
model_types = [aoai, ds, ds_foundry, MODEL_TYPE_API]

deployment_types = [
    "Global Standard",
    "Data Zone Standard",
    "Global Batch",
    "Data Zone Batch",
]


MESSAGE_COMPLETE = "Complete"
MESSAGE_ASSISTANT = "Assistant"
MESSAGE_VISION = "Vision"
MESSAGE_TYPES = [
    MESSAGE_COMPLETE,
    MESSAGE_ASSISTANT,
    MESSAGE_VISION,
]

DEFAULT_MESSAGES_COMPLETE = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a story about 50 words."},
]

DEFAULT_MESSAGES_ASSISTANT = [
    {"role": "assistant", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a story about 50 words."},
]


DEFAULT_MESSAGES_VISION = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
            },
        ],
    }
]
