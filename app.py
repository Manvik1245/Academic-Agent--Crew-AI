import streamlit as st
import sys
from PIL import Image

st.set_page_config(page_title="Academic Agent - Unified Personal AI Workspace", page_icon="🤖", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("Academic Agent - Unified Personal AI Workspace")

if st.button("Test Notion connection"):
    from crew_operations import notion_connection
    result = notion_connection.run("")
    if "error" in result:
        st.error(result["error"])
    else:
        st.success("Notion connection succeeded.")
        st.code(result["results"])

for entry in st.session_state.get("history", []):
    st.chat_message("user").write(entry["user"])
    st.chat_message("assistant").write(entry["response"])
        
if user_query := st.chat_input("Ask me anything about your academic work!"):
    st.chat_message("user").write(user_query)
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            from crew_operations import run_crew as crew_operations
<<<<<<< HEAD
            response = crew_operations(user_query, chat_history= st.session_state.history)
            st.write(response)
    st.session_state.history.append({"user": user_query, "response": response})

=======
            response = crew_operations(user_query)
            st.write(response)
    st.session_state.history.append({"user": user_query, "response": response})


>>>>>>> origin/main
if st.button("Clear"):
    st.session_state.history = []
    st.rerun()
