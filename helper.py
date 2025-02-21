import os
import streamlit as st


def is_admin():
    if not os.path.exists("./config.yaml"):
        return True

    if (
        "authentication_status" in st.session_state
        and st.session_state["authentication_status"]
    ):
        return st.session_state["username"].lower() == "admin"

    return True
