

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base
from helper import time_now


Base = declarative_base()


class TaskTable(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    error_message = Column(String)
    enable_think = Column(Boolean)
    request_succeed = Column(Integer, default=0)
    request_failed = Column(Integer, default=0)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(
        time_now()), onupdate=lambda: int(time_now()))

    def get_created_at_datetime(self):
        return datetime.fromtimestamp(self.created_at / 1000)

    def get_updated_at_datetime(self):
        return datetime.fromtimestamp(self.updated_at / 1000)

    @property
    def query(self):
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]

    @property
    def progress_percentage(self):
        request_total = self.threads * self.request_per_thread
        request_done = self.request_failed + self.request_succeed

        percentage = (request_done / request_total) * 100
        return round(percentage)

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
            if self.request_succeed == 0:
                return '🔴'
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
            if self.request_succeed == 0:
                return 'Failed'
            return 'Succeed'
        return 'NA'


class TaskRequestTable(Base):
    __tablename__ = 'tasks_requests'
    id = Column(String, primary_key=True)
    task_id = Column(Integer)
    thread_num = Column(Integer)
    input_token_count = Column(Integer, default=0)
    output_token_count = Column(Integer, default=0)
    response = Column(String)
    response_count = Column(Integer, default=0)
    first_token_latency_ms = Column(Integer)
    last_token_latency_ms = Column(Integer)
    response_latency_ms = Column(Integer)
    cost_req_time_ms = Column(Integer)
    success = Column(Integer)
    end_req_time = Column(BigInteger, nullable=True)
    start_req_time = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))
    completed_at = Column(BigInteger, nullable=True,
                          default=lambda: int(time_now()))


class TaskRequestChunkTable(Base):
    __tablename__ = 'tasks_requests_chunks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer)
    thread_num = Column(Integer)
    request_id = Column(String)
    chunk_index = Column(Integer)
    chunk_content = Column(String)
    token_len = Column(Integer)
    characters_len = Column(Integer)
    request_latency_ms = Column(Integer)
    last_token_latency_ms = Column(Integer)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))
