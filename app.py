import streamlit as st
from crew_operations import crew_operations
st.set_page_config(page_title="Academic Agent - Unified Personal AI Workspace", page_icon=":robot_face:", layout="centered")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
container = st.container(height=500)
with container:
    for entry in st.session_state.get("history", []):
        st.chat_message("user").write(entry["user"])
        st.chat_message("assistant").write(entry["response"])
if "history" not in st.session_state:
    st.session_state.history = []

user_query = st.text_input("Enter your query:")
with container:
        st.chat_message("user").write(user_query)
with container:
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                response = crew_operations(user_query)
                st.write(response)
st.session_state.history.append({"user": user_query, "response": response})
st.rerun()

if st.button("Clear"):
    st.session_state.history = []
    st.write("Chat history cleared.")
    st.rerun()

