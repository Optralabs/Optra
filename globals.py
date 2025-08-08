# globals.py
import streamlit as st
from supabase import create_client, Client
from datetime import datetime as dt, timezone, timedelta
from PIL import Image
from io import BytesIO
import base64
import json
import re
from typing import Optional


# NEW: for token hashing / JWT
import hashlib
import jwt


# ==========================================================
# ✅ Supabase Client Setup (Service Role Key)
# ==========================================================
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE"]["SERVICE_ROLE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# Debug toggle
DEBUG_ENABLED = st.secrets.get("DEBUG", {}).get("ENABLE", False)


def _dbg_ui(msg: str):
   if DEBUG_ENABLED:
       try:
           st.info(msg)
       except Exception:
           pass


def _dbg_console(*args):
   if DEBUG_ENABLED:
       print(*args)


# ==========================================================
# ✅ Secrets-driven schema overrides
# ==========================================================
SUBS_SECRETS = st.secrets.get("SUPABASE_SUBSCRIPTIONS", {})
EMAIL_FIELD_OVERRIDE: Optional[str] = SUBS_SECRETS.get("EMAIL_FIELD")
PLAN_FIELD_OVERRIDE: Optional[str]  = SUBS_SECRETS.get("PLAN_FIELD")
STATUS_FIELD_OVERRIDE: Optional[str]= SUBS_SECRETS.get("STATUS_FIELD")


# ==========================================================
# ✅ Current user helper
# ==========================================================
def get_current_user_id():
   return st.session_state.get("user_id", "anonymous")


# ==========================================================
# ✅ Add AI Document to Supabase
# ==========================================================
def add_document(text, doc_id_prefix, metadata, user_id):
   try:
       supabase.table("documents").insert({
           "doc_id": f"{doc_id_prefix}",
           "user_id": user_id,
           "content": text,
           "metadata": json.dumps(metadata),
           "created_at": dt.now(timezone.utc).isoformat()
       }).execute()
   except Exception as e:
       _dbg_ui(f"Error saving document: {e}")


# ==========================================================
# ✅ Save User Interaction to Supabase
# ==========================================================
def save_user_interaction(interaction_type, content=None, metadata=None):
   try:
       supabase.table("interactions").insert({
           "user_id": get_current_user_id(),
           "interaction_type": interaction_type,
           "content": content,
           "metadata": json.dumps(metadata) if metadata else None,
           "created_at": dt.now(timezone.utc).isoformat()
       }).execute()
   except Exception as e:
       _dbg_ui(f"Error saving user interaction: {e}")


# ==========================================================
# ✅ Time Helpers
# ==========================================================
def get_current_utc():
   return dt.now(timezone.utc).isoformat()


def get_current_local():
   return dt.now().isoformat()


# ==========================================================
# ✅ Plan Normalization / Mapping
# ==========================================================
EMAIL_COLUMNS_DEFAULT   = ["email", "customer_email", "user_email", "billing_email"]
PLAN_COLUMNS_DEFAULT    = ["plan", "subscription_plan", "plan_name", "product_name", "price_nickname"]
STATUS_COLUMNS_DEFAULT  = ["status", "subscription_status", "state"]
ACTIVE_STATUSES         = {"active", "trialing", "paid", "current"}


PRICE_TO_PLAN = {
   # "price_monthly_xyz": "Starter Plan",
   # "price_yearly_abc":  "Pro Plan",
}


def _norm_email(email: Optional[str]) -> str:
   return re.sub(r"\s+", "", (email or "")).lower()


def _normalize_plan(raw_plan: Optional[str]) -> Optional[str]:
   if not raw_plan:
       return None
   p = raw_plan.strip().lower()
   if p in {"pro", "pro plan", "premium"}:
       return "Pro Plan"
   if p in {"starter", "starter plan", "basic"}:
       return "Starter Plan"
   if raw_plan in {"Pro Plan", "Starter Plan"}:
       return raw_plan
   return None


def _row_status_ok(row: dict, status_columns: list[str]) -> bool:
   if not status_columns:
       return True
   vals = { (row.get(c) or "").strip().lower() for c in status_columns if row.get(c) is not None }
   if not vals:
       return True
   return any(v in ACTIVE_STATUSES for v in vals)


def _resolve_plan_from_row(row: dict, plan_columns: list[str]) -> Optional[str]:
   for c in plan_columns:
       plan = _normalize_plan(row.get(c))
       if plan:
           return plan
   price_id = row.get("price_id")
   if price_id and price_id in PRICE_TO_PLAN:
       return PRICE_TO_PLAN[price_id]
   return None


def _pick_latest(rows: list[dict]) -> Optional[dict]:
   if not rows:
       return None
   def _key(r):
       return (
           r.get("updated_at") or "",
           r.get("created_at") or "",
           r.get("id") or 0,
       )
   return sorted(rows, key=_key, reverse=True)[0]


# ==========================================================
# ✅ Session Logger  (compatible with your sessions schema)
# ==========================================================
def _sha256(s: str) -> str:
   return hashlib.sha256(s.encode("utf-8")).hexdigest()


def log_session(
   email: str,
   plan_or_token: Optional[str] = None,
   *,
   token: Optional[str] = None,
   expires_at_iso: Optional[str] = None,
   ip_address: Optional[str] = None,
   device_fingerprint: Optional[str] = None,
):
   """
   Inserts into Supabase 'sessions' with columns:
     email, token_hash, ip_address, device_fingerprint, expires_at, created_at(default now()).


   Backwards compatible:
     - Old usage: log_session(email, plan)  -> stores just email (created_at via DB).
     - New usage: log_session(email, token=token, expires_at_iso=...)  -> stores token_hash & expires_at.
   """
   try:
       # Prefer explicit token kwarg; else treat 2nd arg as token if it looks like a JWT
       tok = token or (plan_or_token if (plan_or_token and "." in plan_or_token) else None)
       token_hash = _sha256(tok) if tok else None


       if not expires_at_iso:
           expires_at_iso = st.session_state.get("unlock_expiry")  # set by set_auth_cookie


       payload = {
           "email": (email or "").strip().lower(),
           "token_hash": token_hash,
           "ip_address": ip_address,
           "device_fingerprint": device_fingerprint,
           "expires_at": expires_at_iso,
       }
       # remove nulls
       payload = {k: v for k, v in payload.items() if v is not None}


       res = supabase.table("sessions").insert(payload).execute()
       # Always print once while wiring this up
       print("sessions insert result:", getattr(res, "data", None), getattr(res, "error", None))
   except Exception as e:
       print("Session log insert error:", e)


# ==========================================================
# ✅ Main plan lookup (unchanged behaviour; keeps auto-log for compatibility)
# ==========================================================
def get_user_plan(email: str) -> Optional[str]:
   try:
       if not email:
           _dbg_ui("(debug) get_user_plan: empty email.")
           return None


       e = _norm_email(email)


       email_columns  = [EMAIL_FIELD_OVERRIDE] if EMAIL_FIELD_OVERRIDE else []
       email_columns += [c for c in EMAIL_COLUMNS_DEFAULT if c not in email_columns]


       plan_columns   = [PLAN_FIELD_OVERRIDE] if PLAN_FIELD_OVERRIDE else []
       plan_columns  += [c for c in PLAN_COLUMNS_DEFAULT if c not in plan_columns]


       status_columns = [STATUS_FIELD_OVERRIDE] if STATUS_FIELD_OVERRIDE else []
       status_columns+= [c for c in STATUS_COLUMNS_DEFAULT if c not in status_columns]


       sub_row = None


       # 1) Direct lookup in subscriptions by email
       for col in email_columns:
           try:
               res = (
                   supabase.table("subscriptions")
                   .select("*")
                   .ilike(col, f"%{e}%")
                   .limit(5)
                   .execute()
               )
               rows = getattr(res, "data", None) or []
               cand = _pick_latest(rows)
               if cand:
                   sub_row = cand
                   _dbg_ui(f"(debug) subscriptions hit via {col} → id={cand.get('id')}")
                   break
           except Exception as qerr:
               _dbg_ui(f"(debug) subscriptions lookup failed on '{col}': {qerr}")


       # 2) Fallback: profiles(email) -> user_id -> subscriptions
       if not sub_row:
           try:
               prof = (
                   supabase.table("profiles")
                   .select("id, user_id, email")
                   .ilike("email", f"%{e}%")
                   .limit(1)
                   .execute()
               )
               prof_rows = getattr(prof, "data", None) or []
               if prof_rows:
                   user_id = prof_rows[0].get("user_id") or prof_rows[0].get("id")
                   if user_id:
                       sub = (
                           supabase.table("subscriptions")
                           .select("*")
                           .eq("user_id", user_id)
                           .limit(5)
                           .execute()
                       )
                       rows = getattr(sub, "data", None) or []
                       cand = _pick_latest(rows)
                       if cand:
                           sub_row = cand
                           _dbg_ui(f"(debug) subscriptions hit via user_id={user_id} → id={cand.get('id')}")
           except Exception as qerr:
               _dbg_ui(f"(debug) profiles/user_id lookup failed: {qerr}")


       if not sub_row:
           _dbg_ui(f"(debug) No subscriptions row found for '{e}'. "
                   f"Tried email columns {email_columns} and profiles fallback.")
           return None


       if any(k in sub_row for k in status_columns):
           if not _row_status_ok(sub_row, status_columns):
               _dbg_ui("(debug) Row found but not 'active'. "
                       "Status fields: " + ", ".join(f"{c}={sub_row.get(c)}" for c in status_columns if c in sub_row))
               return None


       plan = _resolve_plan_from_row(sub_row, plan_columns)


       # Keep old behaviour: log a minimal session row when a valid plan is seen
       if plan in ("Starter Plan", "Pro Plan"):
           # (Backward compatible: this will just insert email/created_at)
           log_session(e, plan)


       return plan


   except Exception as ex:
       _dbg_ui(f"(debug) get_user_plan exception: {ex}")
       return None


# ==========================================================
# ✅ Locked Page UI
# ==========================================================
def get_logo_base64(path="optra_logo_transparent.png", width=80):
   try:
       img = Image.open(path)
       img = img.resize((width, width), Image.Resampling.LANCZOS)
       buffer = BytesIO()
       img.save(buffer, format="PNG")
       return base64.b64encode(buffer.getvalue()).decode()
   except Exception:
       return None


def show_locked_page(message="🔒 This page is locked. Please log in from the Home page."):
   st.set_page_config(page_title="Locked", layout="wide", page_icon="optra_logo_transparent.png")
   st.markdown("""
       <style>
       html, body, [data-testid="stAppViewContainer"] {
           background: linear-gradient(to bottom, #0a0a0a 0%, #0a0a0a 10%, #0d0f1c 30%, #0f111f 60%, #00011d 100%) !important;
           color: #ffffff !important;
       }
       section[data-testid="stSidebar"] {
           background-color: #000 !important;
       }
       section[data-testid="stSidebar"] * {
           color: #fff !important;
       }
       </style>
   """, unsafe_allow_html=True)


   logo_b64 = get_logo_base64()
   if logo_b64:
       st.markdown(
           f"""
           <div style='display: flex; align-items: center; margin-bottom: 2rem;'>
               <img src='data:image/png;base64,{logo_b64}' width='80' style='margin-right: 15px;' />
               <div>
                   <h1 style='margin: 0; font-size: 1.8rem; color: white;'>OPTRA</h1>
               </div>
           </div>
           """,
           unsafe_allow_html=True
       )


   st.warning(message)
   st.stop()


# ==========================================================
# ✅ Auth Cookie / Persistent Session (returns token)
# ==========================================================
JWT_SECRET = st.secrets.get("JWT_SECRET", "dev_secret_change_me")
JWT_ALGO = "HS256"
AUTH_COOKIE_NAME = "optra_auth"


def set_auth_cookie(email: str, plan: str, hours_valid: int = 24):
   """
   Creates a signed JWT cookie and mirrors state in session_state.
   Returns the raw token so callers can store a hash in Supabase.
   """
   if not email or not plan:
       return None


   expiry = dt.now(timezone.utc) + timedelta(hours=hours_valid)
   payload = {"email": _norm_email(email), "plan": plan, "exp": int(expiry.timestamp())}
   token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


   # Cookie
   try:
       st.experimental_set_cookie(
           AUTH_COOKIE_NAME,
           token,
           expires_at=expiry,
           secure=True,
           httponly=True,
           samesite="Lax",
       )
   except Exception:
       pass


   # Mirror in session_state
   st.session_state["user_email"] = payload["email"]
   st.session_state["user_plan"] = plan
   st.session_state["unlocked"] = True
   st.session_state["unlock_expiry"] = expiry.isoformat()


   # Optional: also mirror into query params (helps with multi-tab)
   try:
       st.query_params["user_email"] = payload["email"]
       st.query_params["user_plan"] = plan
   except Exception:
       pass


   return token  # <-- important for log_session(token=...)


