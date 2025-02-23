

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger
from datetime import datetime
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


class Requests(Base):
    __tablename__ = 'tasks_requests'
    id = Column(String, primary_key=True)
    task_id = Column(Integer)
    thread_num = Column(Integer)
    input_token_count = Column(Integer, default=0)
    output_token_count = Column(Integer, default=0)
    response = Column(String)
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
