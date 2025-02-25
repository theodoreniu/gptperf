from datetime import datetime
import os

app_url = os.getenv('APP_URL', 'https://perf.azuretsp.com')

app_version = '0.0.1'

app_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

not_support_stream = [
    "o1-mini",
    # 以下 stream 为 true 不报错，只能拿到空字符串
    "o1",
    "o3-mini",
]

aoai = 'AOAI'
aoai_models = [
    'gpt-4o',
    'gpt-4o-mini',
    'o1',
    'o1-mini',
    'o3',
    'o3-mini'
]

ds = 'DeepSeek (Ollama)'
ds_foundry = 'DeepSeek (AI Foundry)'
ds_models = [
    'deepseek-r1:1.5b',
    'deepseek-r1:7b',
    'deepseek-r1:8b',
    'deepseek-r1:14b',
    'deepseek-r1:32b',
    'deepseek-r1:70b',
    'deepseek-r1:671b',
    'deepseek-coder:latest'
]

model_types = [
    aoai,
    ds,
    ds_foundry
]

deployment_types = [
    'Global Standard',
    'Data Zone Standard',
    'Global Batch',
    'Data Zone Batch'
]
