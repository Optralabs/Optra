import os
import datetime
import streamlit as st
import pinecone
from uuid import uuid4

# ================================
# 📌 Pinecone & Supabase Settings
# ================================
PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY", None)
PINECONE_INDEX_NAME = st.secrets.get("PINECONE_INDEX_NAME", None)

# Initialise Pinecone connection
if PINECONE_API_KEY and PINECONE_INDEX_NAME:
    try:
        pinecone.init(api_key=PINECONE_API_KEY)
        index = pinecone.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        st.warning(f"⚠️ Could not connect to Pinecone: {e}")
        index = None
else:
    index = None


# =====================================
# 📌 Get the current logged-in user ID
# =====================================
def get_current_user_id():
    """
    Get the logged-in user's ID from Supabase session_state.
    Falls back to 'test_user' if not logged in.
    """
    return st.session_state.get("user_id", "test_user")


# =====================================
# 📌 Add document to Pinecone
# =====================================
def add_document(text, doc_id_prefix, metadata=None, user_id=None):
    """
    Store a document in Pinecone with optional metadata.
    """
    if not index:
        st.warning("Pinecone is not configured. Document not saved.")
        return

    try:
        # Create a unique document ID
        doc_id = f"{doc_id_prefix}_{str(uuid4())}"

        # Store text + metadata in Pinecone
        index.upsert(vectors=[
            (
                doc_id,
                [0.0] * 1536,  # Placeholder vector (replace with actual embeddings if needed)
                {
                    "user_id": user_id or "unknown",
                    "text": text,
                    **(metadata or {})
                }
            )
        ])
    except Exception as e:
        st.warning(f"⚠️ Could not store document in Pinecone: {e}")


# =====================================
# 📌 Retrieve personalised context
# =====================================
def get_pinecone_context(user_id, query, top_k=5):
    """
    Retrieve top matching documents for a specific user from Pinecone.
    Returns concatenated text chunks.
    """
    if not index:
        return "No context available (Pinecone not configured)."

    try:
        # Perform a metadata filter search for the given user
        results = index.query(
            vector=[0.0] * 1536,  # Placeholder vector
            top_k=top_k,
            include_metadata=True,
            filter={"user_id": user_id}
        )

        # Combine the retrieved texts
        context_chunks = []
        for match in results.matches:
            if match.metadata and "text" in match.metadata:
                context_chunks.append(match.metadata["text"])

        return "\n".join(context_chunks) if context_chunks else "No relevant context found."
    except Exception as e:
        return f"Error retrieving context: {e}"


# =====================================
# 📌 Auto-save AI output for the page
# =====================================
def save_page_ai_output():
    """
    Saves the AI-generated output for the current page into Pinecone,
    along with metadata for personalised future recommendations.
    Should be called at the end of each .py page.
    """
    try:
        if not st.session_state.get("last_ai_output"):
            return  # Nothing to save

        user_id = get_current_user_id()
        page_name = st.session_state.get("page_name", "unknown_page")

        add_document(
            text=st.session_state["last_ai_output"],
            doc_id_prefix=f"page_{page_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            metadata={
                "type": "ai_output",
                "page": page_name,
                "grant_type": st.session_state.get("grant_type"),
                "industry": st.session_state.get("industry"),
                "extra_context": st.session_state.get("feedback_context", {})
            },
            user_id=user_id
        )
    except Exception as e:
        st.warning(f"Could not save AI output to Pinecone: {e}")


