

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger

from helper import time_now

import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

Base = declarative_base()


class Chunks(Base):
    __tablename__ = 'tasks_requests_chunks'
    id = Column(String, primary_key=True)
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
