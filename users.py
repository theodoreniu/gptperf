

from logger import logger
from sqlalchemy.ext.declarative import declarative_base

from helper import check_username, get_mysql_session, time_now
import streamlit_authenticator as stauth
from typing import List
from dotenv import load_dotenv
from helper import time_now
import streamlit as st

from sqlalchemy.orm.session import Session
from tables import Users


load_dotenv()


Base = declarative_base()


def register_user(session):
    user = Users()

    with st.container(border=True):
        st.markdown("### Registration")

        col1, col2 = st.columns(2)
        with col1:
            user.username = st.text_input("Alias")
        with col2:
            user.name = st.text_input("Name")

        col1, col2 = st.columns(2)
        with col1:
            user.password = st.text_input("Password", type='password')
        with col2:
            password = st.text_input("Password Repeat", type='password')

        btn = st.button('Summit')

    if btn:
        if not user.username:
            st.error("Alias is required.")
            return
        if not user.name:
            st.error("name is required.")
            return
            return
        if not user.password:
            st.error("password is required.")
            return
        if user.password != password:
            st.error("passwords do not match")
            return

        # username must be a-z0-9.
        if not check_username(user.username):
            st.error("username must start with [a-z][a-z0-9.")
            return

        if len(user.username) < 3:
            st.error("username must be at least 3 characters")
            return

        if len(user.password) < 5:
            st.error("password must be at least 5 characters")
            return

        if len(user.password) > 20:
            st.error("password must be at most 20 characters")
            return

        if len(user.username) > 20:
            st.error("username must be at most 20 characters")
            return

        # username must be unique
        if session.query(Users).filter(Users.username == user.username).first():
            st.error("username already exists.")
            return

        user.email = f"{user.username}@microsoft.com"
        user.created_at = time_now()
        session.add(user)
        session.commit()
        st.success("Registed")


def load_all_users(session) -> List[Users]:
    results = session.query(
        Users
    ).order_by(
        Users.created_at.desc()
    ).all()

    return results


def get_authenticator(session: Session):

    users = session.query(
        Users
    ).order_by(
        Users.created_at.desc()
    ).all()

    session.close()

    credentials = {
        "usernames": {
        }
    }

    for user in users:
        credentials['usernames'][user.username] = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "password": user.password,
            "roles": [user.role]
        }

    return stauth.Authenticate(
        credentials=credentials,
        cookie_name='random_cookie_name_perf',
        cookie_key='random_signature_key_llm_perf',
        cookie_expiry_days=30,
    )


def is_admin(session: Session) -> bool:
    return current_user(session).role == "admin" if current_user(session) else False


def current_user(session: Session) -> Users | None:

    if 'user' in st.session_state:
        return st.session_state['user']

    if (
        "authentication_status" in st.session_state
        and st.session_state["authentication_status"]
    ):

        st.session_state['user'] = session.query(
            Users
        ).filter(
            Users.username == st.session_state["username"]
        ).first()

    return st.session_state['user'] if 'user' in st.session_state else None
