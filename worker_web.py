import os
import streamlit as st
from dotenv import load_dotenv
from helper import create_db
from page_home import home_page
from page_user import register_user
from tables import create_tables, init_user
from task_loads import get_authenticator
from config import APP_STARTED_AT, APP_VERSION

load_dotenv()


def page_title():
    """Configure and render the page title and logo."""
    title = "LLM Perf"
    st.set_page_config(
        page_title=title,
        page_icon="avatars/favicon.ico",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.image("avatars/logo.svg", width=100)
    st.title(title)


if __name__ == "__main__":
    page_title()

    if os.path.exists("init.lock"):
        authenticator = get_authenticator()

        col1, col2 = st.columns(2)
        with col1:
            try:
                authenticator.login(
                    fields={
                        "Form name": "Login",
                        "Username": "Alias",
                        "Password": "Password",
                        "Login": "Login",
                    },
                )
                if st.session_state["authentication_status"] is False:
                    st.error("Alias/Password is incorrect")
            except Exception as e:
                st.error(e)
                st.info(
                    "User information is not available, please clean your browser cache."
                )

        with col2:
            if not st.session_state["authentication_status"]:
                register_user()

        if st.session_state["authentication_status"]:
            st.write(
                f'[Home](/)， Welcome `{st.session_state["name"]}`, `{st.session_state["email"]}`, [llmperf](https://github.com/theodoreniu/llmperf): `{APP_VERSION}` App started at: `{APP_STARTED_AT}`'
            )
            col1, col2 = st.columns([10, 2])
            with col1:
                authenticator.logout()
            home_page()

    elif st.button("Initialize Database", key="init_db"):
        try:
            create_db()
            create_tables()
            init_user()
            with open("init.lock", "w") as f:
                f.write("ok")
        except Exception as e:
            st.error(e)
