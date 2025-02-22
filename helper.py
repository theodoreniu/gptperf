import os
import streamlit as st
from datetime import datetime

import streamlit as st
import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DB")

sql_string = f'mysql+pymysql://{user}:{password}@{host}/{database}'


def is_admin():
    if not os.path.exists("./config.yaml"):
        return True

    if (
        "authentication_status" in st.session_state
        and st.session_state["authentication_status"]
    ):
        return st.session_state["username"].lower() == "admin"

    return True


def so_far_ms(time):
    return time_now() - time


def time_now():
    return datetime.now().timestamp() * 1000


def get_mysql_session():
    engine = create_engine(sql_string)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session
