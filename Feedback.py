import streamlit as st
from supabase import create_client, Client
from datetime import datetime as dt, timezone
from globals import *

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]  # ✅ Use service role key for R/W access
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "feedback"

# ==========================================================
# ✅ Retrieve Past Good Answers for Context
# ==========================================================
def get_past_good_answers(context_tag: str, limit: int = 3):
    """
    Retrieves previously 'good' rated AI answers for a given context tag.
    """
    try:
        result = (
            supabase.table(TABLE_NAME)
            .select("output, rating, context_tag")
            .eq("context_tag", context_tag)
            .eq("rating", "good")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        if hasattr(result, "data") and result.data:
            return [row["output"] for row in result.data if row.get("output")]
        else:
            return []
    except Exception as e:
        st.warning(f"Error retrieving past good answers: {e}")
        return []

# ==========================================================
# 💾 Save Feedback
# ==========================================================
def save_feedback(page_name: str, context_tag: str, query: str, ai_output: str, rating: str):
    try:
        supabase.table(TABLE_NAME).insert({
            "page_name": page_name,
            "context_tag": context_tag,
            "query": query,
            "output": ai_output,
            "rating": rating,
            # ✅ Use safe alias and timezone-aware UTC timestamp
            "created_at": dt.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"Error saving feedback: {e}")

# ==========================================================
# 👍👎 Feedback UI
# ==========================================================
def show_feedback_ui(query: str, ai_output: str):
    if not query or not ai_output:
        return

    st.markdown("#### Rate this AI Response")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("👍 Good"):
            save_feedback(
                page_name=st.session_state.get("page_name", "unknown"),
                context_tag=st.session_state.get("grant_type", "general"),
                query=query,
                ai_output=ai_output,
                rating="good"
            )
            st.success("Thanks! Your positive feedback was recorded.")

    with col2:
        if st.button("👎 Needs Improvement"):
            save_feedback(
                page_name=st.session_state.get("page_name", "unknown"),
                context_tag=st.session_state.get("grant_type", "general"),
                query=query,
                ai_output=ai_output,
                rating="bad"
            )
            st.info("Thanks! We’ll work on improving future answers.")


