import chromadb
from sentence_transformers import SentenceTransformer

# Initialize local ChromaDB persistent storage
client = chromadb.PersistentClient(path="./jarvis_vector_db")

# Use a lightweight, fast local embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Create or get memory collection
collection = client.get_or_create_collection(name="jarvis_memories")


def store_memory(key: str, value: str) -> str:
    """Stores facts into the vector database using semantic embeddings."""
    text_content = f"{key}: {value}"
    embedding = embedding_model.encode(text_content).tolist()

    collection.upsert(
        documents=[text_content],
        embeddings=[embedding],
        metadatas=[{"key": key.strip().lower(), "value": value.strip()}],
        ids=[key.strip().lower()],
    )
    return f"Stored into vector memory: {key} = {value}"


def query_memory(query_text: str, top_k: int = 1) -> str:
    """Retrieves facts based on semantic similarity."""
    if collection.count() == 0:
        return "Memory bank is currently empty, sir."

    query_embedding = embedding_model.encode(query_text).tolist()
    results = collection.query(
        query_embeddings=[query_embedding], n_results=top_k
    )

    if results and results["documents"] and results["documents"][0]:
        retrieved_fact = results["documents"][0][0]
        return f"Semantic memory match: {retrieved_fact}"

    return "No relevant memories found."


def get_all_vector_memories() -> str:
    """Retrieves all stored facts from vector memory."""
    if collection.count() == 0:
        return "No memories recorded yet."
    docs = collection.get()["documents"]
    return "Stored memories: " + "; ".join(docs)