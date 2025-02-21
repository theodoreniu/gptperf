

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

Base = declarative_base()


class TaskTable(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    desc = Column(String)
    model_type = Column(String)
    api_version = Column(String)
    azure_endpoint = Column(String)
    deployment_name = Column(String)
    api_key = Column(String)
    model_id = Column(String)
    system_prompt = Column(String)
    user_prompt = Column(String)
    source_location = ""
    target_location = ""
    deployment_type = Column(String)
    feishu_token = Column(String)
    request_per_thread = Column(Integer)
    threads = Column(Integer)
    status = Column(Integer)
    created_at = Column(String)
    error_message = Column(String)
    enable_think = Column(Boolean)

    @property
    def query(self):
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]

    @property
    def status_icon(self):
        if self.status == 0:
            return '🟤'
        if self.status == 1:
            return '🟣'
        if self.status == 2:
            return '🟠'
        if self.status == 3:
            return '🔴'
        if self.status == 4:
            return '🟢'
        return '🟤'

    @property
    def status_text(self):
        if self.status == 0:
            return 'Created'
        if self.status == 1:
            return 'Queue'
        if self.status == 2:
            return 'Running'
        if self.status == 3:
            return 'Error'
        if self.status == 4:
            return 'Succeed'
        return 'NA'


class TaskRequestTable(Base):
    __tablename__ = 'tasks_requests'
    id = Column(String, primary_key=True)
    task_id = Column(Integer)
    thread_num = Column(Integer)
    input_token_count = Column(Integer)
    output_token_count = Column(Integer)
    response = Column(String)
    created_at = Column(String)
    completed_at = Column(String)
    first_token_latency_ms = Column(Integer)
    last_token_latency_ms = Column(Integer)
    response_latency_ms = Column(Integer)
    cost_req_time_ms = Column(Integer)
    success = Column(Integer)


class TaskRequestChunkTable(Base):
    __tablename__ = 'tasks_requests_chunks'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    thread_num = Column(Integer)
    request_id = Column(String)
    chunk_index = Column(Integer)
    chunk_content = Column(String)
    token_len = Column(Integer)
    characters_len = Column(Integer)
    created_at = Column(String)
    request_latency_ms = Column(Integer)
    last_token_latency_ms = Column(Integer)
