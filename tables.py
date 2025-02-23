

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Float, Text
from datetime import datetime
from helper import get_mysql_session, time_now
from logger import logger
from sqlalchemy import create_engine
from helper import sql_string
import streamlit as st

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True)
    email = Column(String(150), unique=True)
    name = Column(String(50))
    password = Column(String(30))
    role = Column(String(20))
    enable_user = Column(Boolean)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))


class Tasks(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(1024))
    desc = Column(String(1024))
    model_type = Column(String(1024))
    api_version = Column(String(1024))
    azure_endpoint = Column(String(1024))
    deployment_name = Column(String(1024))
    api_key = Column(String(1024))
    model_id = Column(String(1024))
    user_id = Column(Integer)
    system_prompt = Column(Text)
    user_prompt = Column(Text)
    source_location = ""
    target_location = ""
    deployment_type = Column(String(1024))
    feishu_token = Column(String(1024))
    request_per_thread = Column(Integer)
    content_length = Column(Integer)
    temperature = Column(Float)
    timeout = Column(Integer)
    threads = Column(Integer)
    status = Column(Integer)
    error_message = Column(String(1024))
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
        result = round(percentage)
        if result > 100:
            result = 100
        return result

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
            return 'Completed'
        return 'NA'


class Requests(Base):
    __tablename__ = 'tasks_requests'
    id = Column(String(48), primary_key=True)
    task_id = Column(Integer)
    user_id = Column(Integer)
    thread_num = Column(Integer)
    input_token_count = Column(Integer, default=0)
    output_token_count = Column(Integer, default=0)
    response = Column(String(1024))
    chunks_count = Column(Integer, default=0)
    first_token_latency_ms = Column(Integer)
    last_token_latency_ms = Column(Integer)
    request_index = Column(Integer)
    request_latency_ms = Column(Integer)
    success = Column(Integer)
    end_req_time = Column(BigInteger, nullable=True)
    start_req_time = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))
    completed_at = Column(BigInteger, nullable=True,
                          default=lambda: int(time_now()))

    @property
    def start_req_time_fmt(self):
        timestamp_sec = self.start_req_time / 1000
        dt_object = datetime.fromtimestamp(timestamp_sec)
        return dt_object.strftime('%Y-%m-%d %H:%M:%S')


class Chunks(Base):
    __tablename__ = 'tasks_requests_chunks'
    id = Column(String(48), primary_key=True)
    task_id = Column(Integer)
    thread_num = Column(Integer)
    request_id = Column(String(1024))
    chunk_index = Column(Integer)
    user_id = Column(Integer)
    chunk_content = Column(String(1024))
    token_len = Column(Integer)
    characters_len = Column(Integer)
    request_latency_ms = Column(Integer)
    last_token_latency_ms = Column(Integer)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))


def create_tables():
    engine = create_engine(sql_string)

    try:
        Base.metadata.create_all(engine)
        st.success("Tables created")
    except Exception as e:
        st.error(f"Tables create failed: {e}")


def init_user():
    session = get_mysql_session()
    try:
        admin = Users(
            username="admin",
            email="admin@test.com",
            name="Admin",
            password="admin",
            role="admin",
            enable_user=True
        )
        session.add(admin)
        session.commit()
        st.success("Admin user created")
    except Exception as e:
        st.error(f"Admin user create failed: {e}")
    finally:
        session.close()
