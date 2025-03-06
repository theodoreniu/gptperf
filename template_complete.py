import streamlit as st


def template_complete(messages):

    st.session_state.messages = messages

    with st.form(key="new_message_form"):
        new_role = st.selectbox("Select Role:", ["system", "user", "assistant"])
        new_content = st.text_area("Message Content:", height=100)
        submit_button = st.form_submit_button(label="Add Message")

        if submit_button and new_content:
            st.session_state.messages.append({"role": new_role, "content": new_content})
            st.success("Message added successfully!")

    st.write("Current Messages:")

    for idx, message in enumerate(st.session_state.messages):
        col1, col2, col3 = st.columns([1, 4, 1])

        with col1:
            role = st.selectbox(
                "Role:",
                ["system", "user", "assistant"],
                key=f"role_{idx}",
                index=["system", "user", "assistant"].index(message["role"]),
            )

        with col2:
            content = st.text_area(
                "Message Content:", value=message["content"], key=f"content_{idx}"
            )

        st.session_state.messages[idx] = {"role": role, "content": content}

        with col3:
            if st.button("Delete", key=f"delete_{idx}"):
                st.session_state.messages.pop(idx)
                st.success("Deleted")

    return st.session_state.messages
