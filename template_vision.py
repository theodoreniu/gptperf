import streamlit as st


def template_vision(messages: list):
    st.session_state.messages = messages

    with st.form(key="new_message_form"):
        new_role = st.selectbox("Select Role:", ["system", "user", "assistant"])
        new_text = st.text_area("Message Content:")
        new_image_url = st.text_area("Image URL:")

        submit_button = st.form_submit_button(label="Add Message")

        if submit_button:

            content = []
            if new_text:
                content.append({"type": "text", "text": new_text})
            if new_image_url:
                content.append(
                    {"type": "image_url", "image_url": {"url": new_image_url}}
                )
            if content:

                st.session_state.messages.append({"role": new_role, "content": content})
                st.success("Message added successfully!")

    st.write("Current Messages:")

    for idx, message in enumerate(st.session_state.messages):
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

        with col1:
            role = st.selectbox(
                "Role:",
                ["system", "user", "assistant"],
                key=f"role_{idx}",
                index=["system", "user", "assistant"].index(message["role"]),
            )

        with col2:

            new_content = []
            for content in message.get("content", []):
                if content.get("type") == "text":
                    new_text = st.text_area(
                        "Message Content:",
                        value=content.get("text", ""),
                        key=f'text_{idx}_{content.get("text", "")}',
                    )
                    new_content.append({"type": "text", "text": new_text})
                elif content.get("type") == "image_url":
                    new_image_url = st.text_area(
                        "Image URL:",
                        value=content.get("image_url", {}).get("url", ""),
                        key=f'image_{idx}_{content.get("image_url", {}).get("url", "")}',
                    )
                    new_content.append(
                        {"type": "image_url", "image_url": {"url": new_image_url}}
                    )

        with col3:
            if st.button("Update", key=f"update_{idx}"):

                st.session_state.messages[idx] = {"role": role, "content": new_content}
                st.success("Updated")

        with col4:
            if st.button("Delete", key=f"delete_{idx}"):

                st.session_state.messages.pop(idx)
                st.success("Deleted")

    return st.session_state.messages
