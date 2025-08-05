import streamlit as st
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import tiktoken
from datetime import datetime

# =========================
# 1. Load API Keys from secrets.toml
# =========================
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]

# =========================
# 2. Connect to OpenAI & Pinecone
# =========================
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

# =========================
# 3. Pinecone index settings
# =========================
INDEX_NAME = "optra-grant-index"
EMBEDDING_DIM = 1536  # matches OpenAI text-embedding-3 models

# Create index if it doesn't exist
if INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(INDEX_NAME)

# =========================
# 4. Helper functions
# =========================
def embed_text(text: str):
    """Convert text to embedding using OpenAI."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def chunk_text(text: str, max_tokens: int = 500):
    """Split text into smaller chunks for better retrieval."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

# =========================
# 5. Data Insertion
# =========================
def add_document(text: str, doc_id_prefix: str, metadata: dict, user_id: str):
    """Add a user-specific document (PDF, notes) into Pinecone."""
    namespace = f"user_{user_id}"
    chunks = chunk_text(text)
    vectors = []
    for idx, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        vectors.append((
            f"{doc_id_prefix}_chunk_{idx}",
            embedding,
            {**metadata, "chunk_index": idx}
        ))
    index.upsert(vectors=vectors, namespace=namespace)

def add_public_document(text: str, doc_id_prefix: str, metadata: dict):
    """Add a shared public document into Pinecone."""
    chunks = chunk_text(text)
    vectors = []
    for idx, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        vectors.append((
            f"{doc_id_prefix}_chunk_{idx}",
            embedding,
            {**metadata, "chunk_index": idx}
        ))
    index.upsert(vectors=vectors, namespace="public")

def add_ai_response(question: str, answer: str, rating: str, user_id: str):
    """Store a rated AI answer for future optimisation."""
    namespace = f"user_{user_id}"
    combined_text = f"Q: {question}\nA: {answer}"
    embedding = embed_text(combined_text)
    metadata = {
        "type": "ai_response",
        "rating": rating,
        "question": question,
        "timestamp": datetime.now().isoformat()
    }
    index.upsert(
        vectors=[(f"airesp_{datetime.now().timestamp()}", embedding, metadata)],
        namespace=namespace
    )

# =========================
# 6. Retrieval
# =========================
def search_grants(query: str, user_id: str, top_k: int = 5, include_public: bool = True):
    """Search Pinecone for relevant results from user + public data."""
    query_vector = embed_text(query)
    
    # Search user-specific namespace
    private_results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=f"user_{user_id}"
    ).matches

    public_results = []
    if include_public:
        public_results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            namespace="public"
        ).matches

    # Combine and sort by score
    combined_results = private_results + public_results
    combined_results.sort(key=lambda x: x.score, reverse=True)
    return combined_results[:top_k]

# =========================
# 7. Deletion (for bad answers or privacy)
# =========================
def delete_user_data(user_id: str):
    """Remove all vectors for a user."""
    index.delete(delete_all=True, namespace=f"user_{user_id}")

# =========================
# 8. Test Block
# =========================
if __name__ == "__main__":
    st.write("Available indexes:", pc.list_indexes())


