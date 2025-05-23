import os
import streamlit as st
from datetime import datetime
import time

# Import custom modules
from auth import auth_page, init_session_state, logout
from database import create_chat, get_user_chats, get_chat_messages
from chat_handler import process_message, get_formatted_chat_history

# Load custom CSS


def load_css():
    css_file = os.path.join(os.path.dirname(
        __file__), "templates", "style.css")
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found: {css_file}")


def format_time(timestamp_str):
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%H:%M")
    except:
        return ""


def display_chat_interface():
    """Display the main chat interface."""
    st.title("AI Powered ChatBot")

    # Create columns for layout
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Your Chats")

        if st.button("New Chat", use_container_width=True):
            chat_id = create_chat(st.session_state.user_id)
            st.session_state.current_chat_id = chat_id
            st.rerun()

        chats = get_user_chats(st.session_state.user_id)

        st.markdown("<div class='chat-list'>", unsafe_allow_html=True)
        for chat in chats:
            chat_class = "chat-item active-chat" if st.session_state.current_chat_id == chat[
                "id"] else "chat-item"
            if st.markdown(f"<div class='{chat_class}'>{chat['title']} ({chat['message_count']} messages)</div>", unsafe_allow_html=True):
                st.session_state.current_chat_id = chat["id"]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.button("Logout", on_click=logout, use_container_width=True)

    with col2:
        if not st.session_state.current_chat_id and chats:
            st.session_state.current_chat_id = chats[0]["id"]
            st.rerun()

        if not st.session_state.current_chat_id:
            chat_id = create_chat(st.session_state.user_id)
            st.session_state.current_chat_id = chat_id
            st.rerun()

        st.checkbox("Use context from previous chats", key="use_context")

        messages = get_formatted_chat_history(st.session_state.current_chat_id)

        for msg in messages:
            if msg["role"] == "user":
                st.markdown(
                    f"**You** ({format_time(msg['timestamp'])}): {msg['content']}")
            else:
                st.markdown(
                    f"**Gemini** ({format_time(msg['timestamp'])}): {msg['content']}")

        user_input = st.text_input("Type your message...", key="user_input")
        if st.button("Send", use_container_width=True):
            if user_input.strip():
                response = process_message(
                    user_id=st.session_state.user_id,
                    chat_id=st.session_state.current_chat_id,
                    user_message=user_input,
                    use_context=st.session_state.use_context
                )
                st.session_state.user_input = ""
                st.rerun()

# Main App Entry


def main():
    st.set_page_config(page_title="Gemini Chat", layout="wide")
    load_css()
    init_session_state()

    if auth_page():
        display_chat_interface()


if __name__ == "__main__":
    main()
