import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    BigInteger,
    Float,
    Text,
    Index,
    JSON,
)
from helper import format_milliseconds, get_mysql_session, time_now
from logger import logger
from sqlalchemy import create_engine
from helper import sql_string
import streamlit as st
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import threading
from config import DEFAULT_MESSAGES_COMPLETE

Base = declarative_base()

created_table_classes = {}

table_creation_lock = threading.Lock()


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True)
    email = Column(String(150), unique=True)
    name = Column(String(50))
    password = Column(String(30))
    role = Column(String(20))
    enable_user = Column(Boolean)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time_now()))


class Tasks(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (Index("idx_user_id", "user_id"),)
    name = Column(String(1024))
    desc = Column(String(1024))
    model_type = Column(String(1024))
    api_version = Column(String(1024))
    azure_endpoint = Column(String(1024))
    deployment_name = Column(String(1024))
    api_key = Column(String(1024))
    model_id = Column(String(1024))
    user_id = Column(Integer)
    messages = Column(JSON)
    source_location = ""
    target_location = ""
    deployment_type = Column(String(1024))
    feishu_token = Column(String(1024))
    message_type = Column(String(1024))
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
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time_now()))
    updated_at = Column(
        BigInteger,
        nullable=False,
        default=lambda: int(time_now()),
        onupdate=lambda: int(time_now()),
    )

    @property
    def messages_loads(self):
        if self.messages:
            return self.messages
        else:
            return DEFAULT_MESSAGES_COMPLETE

    @property
    def progress_percentage(self):
        """Calculate and return the task progress as a percentage, capped at 100."""
        request_total = self.threads * self.request_per_thread
        request_done = self.request_failed + self.request_succeed
        return min(100, round((request_done / request_total) * 100))

    @property
    def status_text(self):
        if self.status == 0:
            return "Created"
        if self.status == 1:
            return "Queue"
        if self.status == 2:
            return "Running"
        if self.status == 3:
            return "Failed"
        if self.status == 4:
            return "Completed"
        if self.status == 5:
            return "Stoped"
        return "N/A"


def create_request_table_class(task_id: int):
    table_name = f"requests_{task_id}"

    if table_name in created_table_classes:
        return created_table_classes[table_name]

    with table_creation_lock:
        if table_name in created_table_classes:
            return created_table_classes[table_name]

    class Requests(Base):
        """Database model for storing request data associated with a specific task.

        Contains request metadata, timing information, and processing results.
        """

        __tablename__ = table_name
        __table_args__ = (Index("idx_success", "success"), {"extend_existing": True})
        id = Column(String(48), primary_key=True)
        task_id = Column(Integer)
        user_id = Column(Integer)
        thread_num = Column(Integer)
        input_token_count = Column(Integer, default=0)
        output_token_count = Column(Integer, default=0)
        response = Column(Text)
        chunks_count = Column(Integer, default=0)
        first_token_latency_ms = Column(Integer)
        last_token_latency_ms = Column(Integer)
        request_index = Column(Integer)
        request_latency_ms = Column(Integer)
        success = Column(Integer)
        end_req_time = Column(BigInteger, nullable=True)
        start_req_time = Column(BigInteger, nullable=True)
        created_at = Column(BigInteger, nullable=False, default=lambda: int(time_now()))
        completed_at = Column(
            BigInteger, nullable=True, default=lambda: int(time_now())
        )

        @property
        def start_req_time_fmt(self) -> str:
            """Return the start_req_time timestamp formatted as a human-readable string."""
            return format_milliseconds(self.start_req_time)

        @property
        def end_req_time_fmt(self) -> str:
            """Return the end_req_time timestamp formatted as a human-readable string."""
            return format_milliseconds(self.end_req_time)

        @property
        def completed_at_fmt(self) -> str:
            """Return the completed_at timestamp formatted as a human-readable string."""
            return format_milliseconds(self.completed_at)

        @property
        def created_at_fmt(self) -> str:
            """Return the created_at timestamp formatted as a human-readable string."""
            return format_milliseconds(self.created_at)

    created_table_classes[table_name] = Requests

    return Requests


def create_chunk_table_class(task_id: int):
    table_name = f"chunks_{task_id}"

    if table_name in created_table_classes:
        return created_table_classes[table_name]

    with table_creation_lock:
        if table_name in created_table_classes:
            return created_table_classes[table_name]

    class Chunks(Base):
        """Database model for storing chunk data associated with a specific task.

        Contains chunk metadata, timing information, and processing results.
        """

        __tablename__ = table_name
        __table_args__ = (
            Index("chunk_request_id", "request_id"),
            {"extend_existing": True},
        )
        id = Column(String(48), primary_key=True)
        task_id = Column(Integer)
        request_id = Column(String(48))
        chunk_index = Column(Integer)
        thread_num = Column(Integer)
        chunk_content = Column(String(1024))
        token_len = Column(Integer)
        characters_len = Column(Integer)
        request_latency_ms = Column(Integer)
        tpot = Column(Integer)
        last_token_latency_ms = Column(Integer)
        created_at = Column(BigInteger, nullable=False, default=lambda: int(time_now()))

        @property
        def created_at_fmt(self) -> str:
            """Return the created_at timestamp formatted as a human-readable string."""
            return format_milliseconds(self.created_at)

    created_table_classes[table_name] = Chunks

    return Chunks


def create_log_table_class(task_id: int):
    table_name = f"logs_{task_id}"

    if table_name in created_table_classes:
        return created_table_classes[table_name]

    with table_creation_lock:
        if table_name in created_table_classes:
            return created_table_classes[table_name]

    class Logs(Base):
        """Database model for storing log data associated with a specific task.

        Contains log data.
        """

        __tablename__ = table_name
        __table_args__ = (
            Index("log_request_id", "request_id"),
            {"extend_existing": True},
        )
        id = Column(String(48), primary_key=True)
        task_id = Column(Integer)
        thread_num = Column(Integer)
        request_id = Column(String(48))
        log_message = Column(Text)
        log_data = Column(JSON, nullable=True)
        created_at = Column(BigInteger, nullable=False, default=lambda: int(time_now()))

        @property
        def created_at_fmt(self) -> str:
            """Return the created_at timestamp formatted as a human-readable string."""
            return format_milliseconds(self.created_at)

    created_table_classes[table_name] = Logs

    return Logs


def create_task_tables(task_id: int) -> bool:
    engine = create_engine(sql_string)

    Chunks = create_chunk_table_class(task_id)
    Requests = create_request_table_class(task_id)
    Logs = create_log_table_class(task_id)

    try:
        Base.metadata.create_all(engine)
        st.success(f"Table {Chunks.__tablename__} created")
        st.success(f"Table {Requests.__tablename__} created")
        st.success(f"Table {Logs.__tablename__} created")
        return True
    except Exception as e:
        st.error(f"Table {Chunks.__tablename__} create failed: {e}")
        st.error(f"Table {Requests.__tablename__} create failed: {e}")
        st.error(f"Table {Logs.__tablename__} create failed: {e}")
        logger.error(f"Table {Chunks.__tablename__} create failed: {e}")
        logger.error(f"Table {Requests.__tablename__} create failed: {e}")
        logger.error(f"Table {Logs.__tablename__} create failed: {e}")
        return False


def truncate_table(task_id: int) -> bool:
    engine = create_engine(sql_string)
    Session = sessionmaker(bind=engine)
    session = Session()

    Chunks = create_chunk_table_class(task_id)
    Requests = create_request_table_class(task_id)
    Logs = create_log_table_class(task_id)
    try:
        session.execute(text(f"TRUNCATE TABLE {Chunks.__tablename__};"))
        session.execute(text(f"TRUNCATE TABLE {Requests.__tablename__};"))
        session.execute(text(f"TRUNCATE TABLE {Logs.__tablename__};"))
        return True
    except Exception as e:
        st.error(f"DB truncate failed: {e}")
        logger.error(f"DB truncate failed: {e}")
        return False
    finally:
        session.close()


def delete_task_tables(task_id: int) -> bool:
    engine = create_engine(sql_string)

    Chunks = create_chunk_table_class(task_id)
    Requests = create_request_table_class(task_id)
    Logs = create_log_table_class(task_id)
    try:
        Chunks.__table__.drop(engine)
        Requests.__table__.drop(engine)
        Logs.__table__.drop(engine)
        st.success(f"Table {Chunks.__tablename__} deleted")
        st.success(f"Table {Requests.__tablename__} deleted")
        st.success(f"Table {Logs.__tablename__} deleted")
        return True
    except Exception as e:
        st.error(f"Table {Chunks.__tablename__} deletion failed: {e}")
        st.error(f"Table {Requests.__tablename__} deletion failed: {e}")
        st.error(f"Table {Logs.__tablename__} deletion failed: {e}")
        logger.error(f"Table {Chunks.__tablename__} deletion failed: {e}")
        logger.error(f"Table {Requests.__tablename__} deletion failed: {e}")
        logger.error(f"Table {Logs.__tablename__} deletion failed: {e}")
        return False


def create_tables():
    engine = create_engine(sql_string)

    try:
        Base.metadata.create_all(engine)
        st.success("Tables created")
    except Exception as e:
        st.error(f"Tables create failed: {e}")
        logger.error(f"Tables create failed: {e}")


def init_user():
    session = get_mysql_session()
    try:
        admin = Users(
            username="admin",
            email="admin@test.com",
            name="Admin",
            password="admin",
            role="admin",
            enable_user=True,
        )
        session.add(admin)
        session.commit()
        st.success("Admin user created")
    except Exception as e:
        st.error(f"Admin user create failed: {e}")
    finally:
        session.close()
