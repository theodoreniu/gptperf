

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Float
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


class Tasks(Base):
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
    content_length = Column(Integer)
    temperature = Column(Float)
    timeout = Column(Integer)
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
