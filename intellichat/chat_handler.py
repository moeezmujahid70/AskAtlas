import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from database import save_message, get_chat_messages, update_message_vector_id
from vector_store import add_message_to_vector_store, get_chat_context

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# @st.cache_resource
# def load_model():
#     return genai.GenerativeModel("gemini-1.5-flash")

# model = load_model()


def initialize_chat():
    """Initialize a new chat session with Gemini."""
    return genai.GenerativeModel('gemini-2.0-flash').start_chat(history=[])


def format_chat_history(messages):
    """Format messages from the database into a format for the chat interface."""
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "id": msg["id"],
            "role": "user" if msg["is_user"] else "assistant",
            "content": msg["content"],
            "timestamp": msg["timestamp"]
        })
    return formatted_messages


def get_formatted_chat_history(chat_id):
    """Get formatted chat history for display."""
    messages = get_chat_messages(chat_id)
    return format_chat_history(messages)


def process_message(user_id, chat_id, user_message, use_context=False):
    """
    Process a user message, save it to the database, and get AI response.

    Args:
        user_id: The ID of the current user
        chat_id: The ID of the current chat
        user_message: The message from the user
        use_context: Whether to include context from previous chats

    Returns:
        The AI response text
    """
    # Save user message to database
    message_id = save_message(chat_id, user_id, user_message, is_user=True)

    # Add message to vector store
    vector_id = add_message_to_vector_store(
        user_message,
        user_id,
        message_id,
        chat_id,
        is_user=True
    )

    # Update message with vector ID
    update_message_vector_id(message_id, vector_id)

    # Get chat history for this chat
    messages = get_chat_messages(chat_id)
    history = []

    # Format messages for Gemini API
    for msg in messages:
        role = "user" if msg["is_user"] else "model"
        history.append({"role": role, "parts": [msg["content"]]})

    # Initialize chat with history
    # Exclude the latest message
    chat = genai.GenerativeModel(
        'gemini-2.0-flash').start_chat(history=history[:-1])

    # Prepare prompt with context if needed
    prompt = user_message
    context = ""

    if use_context:
        context = get_chat_context(user_id, user_message)
        if context and context != "No relevant context found in past conversations.":
            prompt = f"""
            I need you to answer the following question using the context from my previous conversations where relevant:
            
            Question: {user_message}
            
            {context}
            
            Only use the context if it's relevant to the question. If the context doesn't help, just answer normally.
            Always respond directly to the question without mentioning that you're using context or previous conversations.
            """

    # Get AI response
    response = chat.send_message(prompt if use_context else user_message)
    response_text = response.text

    # Save AI response to database
    ai_message_id = save_message(
        chat_id, user_id, response_text, is_user=False)

    # Add AI response to vector store
    ai_vector_id = add_message_to_vector_store(
        response_text,
        user_id,
        ai_message_id,
        chat_id,
        is_user=False
    )

    # Update message with vector ID
    update_message_vector_id(ai_message_id, ai_vector_id)

    return response_text
