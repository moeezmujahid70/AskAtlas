# chroma_store.py
import chromadb
from sentence_transformers import SentenceTransformer

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="user_knowledge")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed_and_store_message(message_id, content, user_id, tags=None):
    embedding = embedder.encode(content).tolist()
    metadata = {"user_id": user_id}
    if tags:
        metadata["tags"] = tags
    collection.add(
        documents=[content],
        embeddings=[embedding],
        ids=[str(message_id)],
        metadatas=[metadata]
    )


def retrieve_similar_context(user_query, user_id, top_k=5):
    query_embedding = embedder.encode(user_query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"user_id": user_id},
    )
    return "\n".join(results["documents"][0]) if results["documents"] else ""
