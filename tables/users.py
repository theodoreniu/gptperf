

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from sqlalchemy import Column, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base
from helper import time_now
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


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    email = Column(String)
    name = Column(String)
    password = Column(String)
    enable_user = Column(Boolean)
    created_at = Column(BigInteger, nullable=False,
                        default=lambda: int(time_now()))
