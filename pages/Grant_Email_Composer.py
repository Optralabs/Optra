import streamlit as st
from datetime import datetime, timedelta
from streamlit_extras.stylable_container import stylable_container
from openai import OpenAI 
from PIL import Image
import base64
from io import BytesIO
import plotly.figure_factory as ff
import pandas as pd
import os

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_logo_base64(path, width=80):
    img = Image.open(path)
    img = img.resize((width, width), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

logo_base64 = get_logo_base64("optra_logo_transparent.png")

st.markdown(
    f"""
    <div style='display: flex; align-items: center; margin-bottom: 2rem;'>
        <img src='data:image/png;base64,{logo_base64}' width='80' style='margin-right: 15px;' />
        <div>
            <h1 style='margin: 0; font-size: 1.8rem;'>OPTRA</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------- Sidebar UI & Theme ----------------------------
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        section[data-testid="stSidebar"] .css-1v0mbdj, 
        section[data-testid="stSidebar"] .css-1wvsk6o {
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(to bottom, #0a0a0a 0%, #0a0a0a 10%, #0d0f1c 30%, #0f111f 60%, #00011d 100%) !important;
            color: #ffffff;
        }
        .block-container { background-color: rgba(0, 0, 0, 0) !important; }
        input, textarea, select {
            background-color: #111729 !important;
            color: #ffffff !important;
            border: 1px solid #2b3a5e !important;
        }
        ::placeholder { color: #888 !important; }
        button[kind="primary"] {
            background-color: #3e6ce2 !important;
            color: white !important;
            border-radius: 8px !important;
        }
        h1, h2, h3 {
            text-shadow: 0 0 4px rgba(0,0,0,0.4);
        }
    </style>
""", unsafe_allow_html=True)

# ========= App State Setup =========
st.title("🔒 Grant Email Composer")
st.markdown("Instantly enhance your emailing capabilities to the Grant-relevant organizations you contact.")

selected_grant = st.selectbox(
    "Select Grant of Interest",
    ["Productivity Solutions Grant (PSG)", "Enterprise Development Grant (EDG)", "Market Readiness Assistance (MRA)", "Startup SG Founder", "Other"]
)

email_purpose = st.selectbox(
    "Select Email Purpose",
    [
        "Request for quotation from vendor",
        "Clarify grant requirements with officer",
        "Follow-up on pending response",
        "Submit supporting documents",
        "Appeal for rejected application",
        "Request extension for submission",
        "Request site visit schedule",
        "Custom: Write your own"
    ]
)

# Allow user to input their own name and email
sender_name = st.text_input("Your Name (Sender)", placeholder="Your Name")
sender_email = st.text_input("Your Email", placeholder="e.g. yourname@example.com")

# Other optional info
company_name = st.text_input("Company Name", placeholder="e.g. Your Company Pte Ltd")

recipient_name = st.text_input("Recipient Name", placeholder="Write Contact's Name Here")
recipient_email = st.text_input("Recipient Email", placeholder="e.g. contact@vendor.com")

additional_context = st.text_area(
    "Add any extra context or specific requests (optional)", placeholder="e.g. Need the quote by next Tuesday..."
)

if st.button("Generate Email"):
    if not sender_name or not sender_email:
        st.warning("Please provide both your name and email.")
    elif not recipient_name or not recipient_email:
        st.warning("Please provide both recipient name and recipient email.")
    else:
        with st.spinner("Composing your email..."):
            try:
                prompt = f"""
Compose a clear, professional, and customized email.

Details:
- Purpose: {email_purpose}
- Sender Name: {sender_name}
- Sender Email: {sender_email}
- Company: {company_name}
- Grant of Interest: {selected_grant}
- Recipient: {recipient_name} ({recipient_email})
- Additional Info: {additional_context if additional_context else "None"}

Ensure the tone is polite, helpful, and adapted to an SME context. Include:
1. A clear subject line.
2. Proper salutation.
3. Introduction with the sender's role and company.
4. Purpose and action needed.
5. Optional context and request for follow-up.
6. Signature block with name, company, and contact info.
"""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a business writing assistant that drafts formal, SME-friendly emails for government grant processes."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=600
                )

                generated_email = response.choices[0].message.content.strip()
                st.text_area("Generated Email", value=generated_email, height=250, key="email_output")

                # Copy to clipboard button with hidden textarea workaround
                copy_button_code = f"""
                <button id="copy-btn" style="
                    background-color: #3e6ce2;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-top: 10px;
                ">
                    Copy Email to Clipboard
                </button>

                <textarea id="email-text" style="position: absolute; left: -9999px; top: 0;">{generated_email.replace('"', '&quot;')}</textarea>

                <script>
                const copyBtn = document.getElementById('copy-btn');
                const emailText = document.getElementById('email-text');
                copyBtn.addEventListener('click', () => {{
                    emailText.select();
                    navigator.clipboard.writeText(emailText.value).then(() => {{
                        alert('Email copied to clipboard!');
                    }}).catch(err => {{
                        alert('Failed to copy text: ' + err);
                    }});
                }});
                </script>
                """

                st.components.v1.html(copy_button_code, height=60)

            except Exception as e:
                st.error(f"Failed to generate email. Error: {e}")


