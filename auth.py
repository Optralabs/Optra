# auth.py
import streamlit as st
from supabase import create_client, Client
from jose import jwt
from datetime import datetime, timedelta

# ==========================================================
# ✅ Supabase client (Service Role key)
# ==========================================================
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE"]["SERVICE_ROLE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ==========================================================
# ✅ JWT config (from nested secrets)
# ==========================================================
JWT_SECRET = st.secrets["SUPABASE"]["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_LIFETIME_HOURS = 12  # adjust if you want longer/shorter sessions

# ==========================================================
# ✅ Token helpers
# ==========================================================
def create_token(email: str) -> str:
    """Create a signed JWT for the given email with an expiry."""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_LIFETIME_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token():
    """
    Read the 'token' from the URL query params via st.query_params
    and return the decoded payload, or None if invalid/expired/missing.
    """
    params = st.query_params
    token = params.get("token")

    # Normalize in case something set a list
    if isinstance(token, list):
        token = token[0]

    if not token:
        return None

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        st.error("Your session has expired. Please log in again.")
        return None
    except jwt.JWTError:
        # Invalid token
        return None

# ==========================================================
# ✅ Subscription helpers (Supabase)
# ==========================================================
def get_user_plan(email: str):
    """
    Return the plan string ('Starter Plan' / 'Pro Plan') for the given email.
    Case-insensitive match; trims whitespace. Returns None if not found.
    """
    try:
        if not email:
            return None
        email_norm = email.strip().lower()

        resp = (
            supabase.table("subscriptions")
            .select("email, plan")
            .ilike("email", email_norm)  # case-insensitive match
            .limit(1)
            .execute()
        )

        if resp.data:
            return resp.data[0].get("plan")
        return None
    except Exception as e:
        # Optional: st.warning(f"Error fetching user plan: {e}")
        return None

def is_registered_email(email: str) -> bool:
    """
    Return True if the email exists in subscriptions (case-insensitive).
    """
    try:
        if not email:
            return False
        email_norm = email.strip().lower()
        resp = (
            supabase.table("subscriptions")
            .select("email")
            .ilike("email", email_norm)
            .limit(1)
            .execute()
        )
        return bool(resp.data)
    except Exception:
        return False


