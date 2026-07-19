import streamlit as st
from crew_operations import crew_operations
import threading
import sys
from io import StringIO

log_stream = StringIO()

class StreamToLogger:
    
    def write(self, message):
        log_stream.write(message)
        log_stream.flush()

    def flush(self):
        log_stream.flush()

sys.stdout = StreamToLogger()
sys.stderr = StreamToLogger()

st.set_page_config(page_title="Academic Agent - Unified Personal AI Workspace", page_icon=":robot_face:", layout="centered")
if "user" not in st.session_state:
    st.session_state.history = []
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
st.title("Academic Agent - Unified Personal AI Workspace")
for entry in st.session_state.get("history", []):
    st.chat_message("user").write(entry["user"])
    st.chat_message("assistant").write(entry["response"])
    
if user_query := st.chat_input("Ask me anything about your academic work!"):
    st.chat_message("user").write(user_query)
    log_box= st.empty()
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
