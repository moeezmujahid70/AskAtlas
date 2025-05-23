import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from auth import auth_page, logout
from database import (
    get_user_chats, get_chat_messages,
    create_chat, save_message, delete_chat, get_db_connection
)
from chroma_store import retrieve_similar_context

# Set page layout
st.set_page_config(layout="wide")

# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

# Authenticate user
if not auth_page():
    st.stop()

# Sidebar - User Info
st.sidebar.title(f"Welcome, {st.session_state.username}")
st.sidebar.subheader("Chats")

# Fetch all user chats
chats = get_user_chats(st.session_state.user_id)

# Create New Chat Button
if st.sidebar.button("\u2795 New Chat", key="new_chat"):
    new_chat_id = create_chat(st.session_state.user_id)
    st.session_state.current_chat_id = new_chat_id
    st.rerun()

# List chats with delete buttons
for chat in chats:
    col1, col2 = st.sidebar.columns([5, 1])
    with col1:
        if st.button(chat["title"], key=f"chat_button_{chat['id']}"):
            st.session_state.current_chat_id = chat["id"]
            st.rerun()
    with col2:
        if st.button("\u274C", key=f"delete_chat_{chat['id']}"):
            delete_chat(chat["id"])
            if st.session_state.current_chat_id == chat["id"]:
                st.session_state.current_chat_id = None
            st.rerun()

# Add space before sticky logout
st.sidebar.markdown("<br><br><br><br>", unsafe_allow_html=True)

# Sticky logout button
st.sidebar.markdown(
    """
    <div style="position: fixed; bottom: 20px; width: 18%;">
        <form action="?">
            <button style="width: 100%; padding: 0.5em;" type="submit" onclick="streamlit.setComponentValue('logout', true)">Logout</button>
        </form>
    </div>
    """,
    unsafe_allow_html=True
)

if st.query_params.get("logout") == "true":
    logout()

# No chat selected
if not st.session_state.current_chat_id:
    st.info("Please select or create a chat to start messaging.")
    st.stop()

# Fixed header with title + input + scroll
st.markdown('<div class="fixed-header">', unsafe_allow_html=True)

# Input row
st.markdown('<div class="input-row">', unsafe_allow_html=True)
user_input = st.chat_input("Ask something...")
if st.button("Scroll to Bottom"):
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat messages in scrollable container
st.markdown('<div class="chat-body">', unsafe_allow_html=True)
messages = get_chat_messages(st.session_state.current_chat_id)
for msg in messages:
    if msg["is_user"]:
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Gemini:** {msg['content']}")

# Context toggle appears after all messages
toggle = st.toggle("Include previous knowledge", key="use_context")
st.caption("Enable this to include previous knowledge in your response.")
st.markdown('</div>', unsafe_allow_html=True)

# Handle user input and generate response
if user_input and user_input.strip():
    save_message(
        chat_id=st.session_state.current_chat_id,
        user_id=st.session_state.user_id,
        content=user_input,
        is_user=True
    )

    # Only update chat title if it's the first user message
    messages = get_chat_messages(st.session_state.current_chat_id)
    if len(messages) == 1 and messages[0]["is_user"]:
        def extract_tags(text, num_tags=3):
            vectorizer = TfidfVectorizer(stop_words='english')
            X = vectorizer.fit_transform([text])
            scores = np.asarray(X.sum(axis=0)).flatten()
            words = np.array(vectorizer.get_feature_names_out())
            sorted_indices = scores.argsort()[::-1]
            return " ".join(words[sorted_indices[:num_tags]])

        tag = extract_tags(user_input)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE chats SET title = ? WHERE id = ?",
                       (tag, st.session_state.current_chat_id))
        conn.commit()
        conn.close()

    prompt = user_input
    if st.session_state.use_context:
        rag_context = retrieve_similar_context(
            user_input, st.session_state.user_id)
        prompt = f"{rag_context}\nYou: {user_input}"

    try:
        gemini_reply = model.generate_content(prompt).text
    except Exception as e:
        gemini_reply = f"Error: {str(e)}"

    save_message(
        chat_id=st.session_state.current_chat_id,
        user_id=st.session_state.user_id,
        content=gemini_reply,
        is_user=False
    )

    st.rerun()

# CSS for layout
st.markdown("""
<style>
.fixed-header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: white;
    z-index: 1000;
    padding-bottom: 0.5em;
    border-bottom: 1px solid #eee;
}
.input-row {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.chat-body {
    margin-top: 140px;
    padding-bottom: 2em;
}
</style>
""", unsafe_allow_html=True)
