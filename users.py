

from sqlalchemy.ext.declarative import declarative_base

from helper import time_now
import streamlit_authenticator as stauth
from typing import List
from dotenv import load_dotenv
from helper import time_now
import streamlit as st
import logging
from sqlalchemy.orm.session import Session
from tables.users import Users


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

Base = declarative_base()


def register_user(session):
    with st.container(border=True):
        st.markdown("### Register User")

        user = Users()
        col1, col2, col3 = st.columns(3)
        with col1:
            user.username = st.text_input("User Name")
        with col2:
            user.name = st.text_input("Name")
        with col3:
            user.email = st.text_input("E-mail")

        col1, col2 = st.columns(2)
        with col1:
            user.password = st.text_input("Password", type='password')
        with col2:
            password = st.text_input("Password Repeat", type='password')

        if st.button('Register'):
            if not user.username:
                st.error("Username is required.")
                return
            if not user.name:
                st.error("name is required.")
                return
            if not user.email:
                st.error("email is required.")
                return
            if not user.password:
                st.error("password is required.")
                return
            if user.password != password:
                st.error("password wrong.")
                return

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
    users = load_all_users(session)
    credentials = {
        "usernames": {
        }
    }
    for user in users:
        credentials['usernames'][user.username] = {
            "email": user.email,
            "name": user.name,
            "password": user.password,
        }

    return stauth.Authenticate(
        credentials=credentials,
        cookie_name='random_cookie_name',
        cookie_key='random_signature_key_llm',
        cookie_expiry_days=30,
    )


def is_admin():
    if (
        "authentication_status" in st.session_state
        and st.session_state["authentication_status"]
    ):
        return st.session_state["username"].lower() == "admin"

    return True
