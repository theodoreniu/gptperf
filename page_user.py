from helper import check_username, time_now

from dotenv import load_dotenv
import streamlit as st

from tables import Users
from task_loads import add_user


load_dotenv()


def register_user():
    user = Users(role="user", created_at=time_now())

    with st.container(border=True):
        st.markdown("### Registration")

        col1, col2 = st.columns(2)
        with col1:
            user.username = st.text_input("Alias")
        with col2:
            user.name = st.text_input("Name")

        col1, col2 = st.columns(2)
        with col1:
            user.password = st.text_input("Password", type="password")
        with col2:
            password = st.text_input("Password Repeat", type="password")

        btn = st.button("Summit")

    if btn:
        if not user.username:
            st.error("Alias is required.")
            return
        if not user.name:
            st.error("name is required.")
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

        user.email = f"{user.username}@microsoft.com"
        add_user(user)
        st.success("Register")
