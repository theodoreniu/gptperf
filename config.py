from datetime import datetime
import os

APP_URL = os.getenv("APP_URL", "http://localhost:9876")

APP_VERSION = "0.0.2"

APP_STARTED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
