import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import json

# Initialize the model for creating embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Ensure the database directory exists
if not os.path.exists('data/vector_db'):
    os.makedirs('data/vector_db')

# Initialize ChromaDB client
client = chromadb.PersistentClient(
    path="data/vector_db", settings=Settings(anonymized_telemetry=False))

# # Create or get the collection for chat messages
# try:
#     collection = client.get_collection("chat_messages")
# except ValueError:
#     collection = client.create_collection("chat_messages")

# Ensure collection exists or create it
if "chat_messages" not in [col.name for col in client.list_collections()]:
    collection = client.create_collection("chat_messages")
else:
    collection = client.get_collection("chat_messages")


def generate_embedding(text):
    """Generate an embedding vector for the given text."""
    return model.encode(text).tolist()


def add_message_to_vector_store(message_content, user_id, message_id, chat_id, is_user):
    """
    Add a message to the vector store.

    Args:
        message_content: The text content of the message
        user_id: ID of the user who owns this message
        message_id: ID of the message in the SQL database
        chat_id: ID of the chat this message belongs to
        is_user: Boolean indicating if this is a user message or AI response

    Returns:
        The ID of the document in the vector store
    """
    doc_id = str(uuid.uuid4())

    # Create metadata to be stored with the embedding
    metadata = {
        "user_id": user_id,
        "message_id": message_id,
        "chat_id": chat_id,
        "is_user": is_user,
        "content": message_content  # Store full content in metadata for retrieval
    }

    # Add document to the collection
    collection.add(
        ids=[doc_id],
        embeddings=[generate_embedding(message_content)],
        metadatas=[metadata]
    )

    return doc_id


def search_user_messages(query_text, user_id, n_results=5):
    """
    Search for relevant messages from a user's history.

    Args:
        query_text: The query text to search for
        user_id: The ID of the user whose messages to search
        n_results: Maximum number of results to return

    Returns:
        List of relevant message contents and their metadata
    """
    # Generate embedding for the query
    query_embedding = generate_embedding(query_text)

    # Search the collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"user_id": user_id}
    )

    # Format the results
    formatted_results = []
    if results and 'metadatas' in results and results['metadatas']:
        for metadata in results['metadatas'][0]:
            formatted_results.append({
                "content": metadata["content"],
                "is_user": metadata["is_user"],
                "chat_id": metadata["chat_id"],
                "message_id": metadata["message_id"]
            })

    return formatted_results


def get_chat_context(user_id, query_text):
    """
    Get relevant context from user's past conversations.

    Args:
        user_id: The ID of the user
        query_text: The current query text

    Returns:
        A formatted string containing relevant context
    """
    relevant_messages = search_user_messages(query_text, user_id, n_results=10)

    if not relevant_messages:
        return "No relevant context found in past conversations."

    # Format the context
    context = "Relevant information from previous conversations:\n\n"
    for i, msg in enumerate(relevant_messages):
        role = "User" if msg["is_user"] else "AI"
        context += f"{i+1}. [{role}]: {msg['content']}\n\n"

    return context
