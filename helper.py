import os
import uuid
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy import create_engine
from dotenv import load_dotenv
import re
import streamlit as st
from sqlalchemy import text


load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DB")

db_string = f"mysql+pymysql://{user}:{password}@{host}"
sql_string = f"{db_string}/{database}"


def format_milliseconds(timestamp_ms):
    if not timestamp_ms:
        return "N/A"

    seconds, milliseconds = divmod(timestamp_ms, 1000)
    dt = datetime.fromtimestamp(seconds)
    return dt.strftime(f"%Y-%m-%d %H:%M:%S.{milliseconds:03d}")


def pad_number(num1, num2):
    num2_length = len(str(num2))
    return str(num1).zfill(num2_length)


def create_db():
    engine = create_engine(db_string)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        session.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS {database} DEFAULT CHARACTER SET = 'utf8mb4';"
            )
        )
        st.success(f"DB created")
    except Exception as e:
        st.error(f"DB create failed: {e}")
    finally:
        session.close()


def check_username(s):
    pattern = r"^[a-z][a-z0-9.]*$"
    return bool(re.match(pattern, s))


def so_far_ms(time):
    return 0 if not time else time_now() - time


def time_now():
    return datetime.now().timestamp() * 1000


def get_mysql_session() -> Session:
    return sessionmaker(bind=create_engine(sql_string))()


def data_id():
    return str(uuid.uuid4()).replace("-", "")


def task_status_icon(status: int):
    if status == 0:
        return "🟤"
    if status == 1:
        return "🟣"
    if status == 2:
        return "🔵"
    if status == 3:
        return "🔴"
    if status == 4:
        return "🟢"
    if status == 5:
        return "⛔"
    return "🟤"
