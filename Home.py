import streamlit as st
import openai
from openai import OpenAI
client = OpenAI()
import os
import requests
import datetime
import re
from fpdf import FPDF
import pdfplumber
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ----------------------------
# Load and embed OPTRA logo
# ----------------------------
from PIL import Image
import base64
from io import BytesIO
import streamlit as st

def get_logo_base64(path, width=80):
    img = Image.open(path)
    img = img.resize((width, width), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Set your logo path
logo_base64 = get_logo_base64("optra_logo_transparent.png")

# Display logo and brand (only once)
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

st.set_page_config(page_title="Smart Grant Advisor", layout="wide")
# Set page config

# ----------------------------
# 🧩 OPTRA Sidebar Setup
# ----------------------------
st.markdown("""
    <style>
        /* Force sidebar background to black */
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        /* Sidebar text color */
        section[data-testid="stSidebar"] .css-1v0mbdj, 
        section[data-testid="stSidebar"] .css-1wvsk6o {
            color: #ffffff !important;
        }
        /* Optional spacing and styling tweaks */
        .sidebar-content {
            padding: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Smart Grant Advisor", layout="wide")

st.title("Smart Grant Advisor")
st.markdown("""
Welcome to **Smart Grant Advisor** — your AI-powered tool to help Singapore SMEs navigate complex government grants.

Use the sidebar to:
-  Upload and review documents with the **Document Checker**
-  Access Live Grant Insights **

---
""")

st.info("Start by selecting a tool from the sidebar on the left.")


auto_data = {}

# === Load API Key from Streamlit secrets ===
import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

# === Helper: Extract text from PDF ===
def extract_text_from_pdf(file) -> str:
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# === Helper: Extract UEN and Industry ===
def extract_data_from_text(text):
    data = {}
    uen_match = re.search(r'\b\d{8}[A-Z]\b', text)
    if uen_match:
        data['uen'] = uen_match.group(0)
    text_lower = text.lower()
    if 'retail' in text_lower:
        data['industry'] = 'Retail'
    elif 'education' in text_lower:
        data['industry'] = 'Education'
    elif 'food and beverage' in text_lower or 'f&b' in text_lower:
        data['industry'] = 'F&B'
    return data

# === About Your Business ===
st.markdown("### About Your Business")
industry = st.text_input("Industry / Sector", value=auto_data.get("industry") or "")
revenue = st.text_input("Annual Revenue (SGD)")
employees = st.text_input("No. of Employees")
years = st.text_input("Years in Operation")
ownership = st.selectbox("Is Local Ownership ≥30%?", ["Yes", "No"], index=0)
goal = st.text_input("What do you want to achieve with a grant?")

if st.button("Check Eligibility Based on Business Info"):
    with st.spinner("Analyzing eligibility with OpenAI..."):
        try:
            eligibility_prompt = f"""
You are a smart grant advisor for Singaporean SMEs.
Based on the following inputs, assess which grants the business is likely eligible for (e.g. PSG, EDG) and explain why.

### Business Info:
- Industry: {industry}
- Revenue: {revenue}
- Employees: {employees}
- Years in Operation: {years}
- Local Ownership ≥30%: {ownership}
- Business Goal: {goal}
"""
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful and precise grant advisor for Singaporean SMEs."},
                    {"role": "user", "content": eligibility_prompt}
                ]
            )
            st.session_state.eligibility_response = res.choices[0].message.content
            st.success("Eligibility results ready!")
        except Exception as e:
            st.error(f"OpenAI API error: {e}")

if st.session_state.get("eligibility_response"):
    st.markdown("### Eligibility Result")
    st.markdown(st.session_state.eligibility_response)

    pdf_bytes = generate_pdf(st.session_state.eligibility_response)
    if pdf_bytes:
        st.download_button("Download Eligibility as PDF", data=pdf_bytes, file_name="eligibility_report.pdf")

# === SFEC Inputs ===
st.markdown("### SFEC Specific Details")
skills_levy_paid = st.text_input("Skills Development Levy Paid Last Year (S$)")
local_employees = st.text_input("Number of Local Employees")
violations = st.checkbox("Any outstanding MOM or IRAS violations?", value=False)

# === Eligibility Check Button ===
if st.button("Check Eligibility"):
    with st.spinner("Analyzing eligibility with OpenAI..."):
        try:
            prompt = f"""
You are a smart grant advisor for Singaporean SMEs.
Based on the following inputs, assess which grants the business is likely eligible for (PSG, EDG, SFEC), and explain why in clear terms.

### Business Info:
- Industry: {industry}
- Revenue: {revenue}
- Employees: {employees}
- Years in Operation: {years}
- Local Ownership ≥30%: {ownership}
- Business Goal: {goal}

### SFEC:
- SDL Paid Last Year: {skills_levy_paid}
- Local Employees: {local_employees}
- Violations: {"Yes" if violations else "No"}

{f"### Extracted Document:\n{doc_summary}" if doc_summary else ""}

Return a markdown report with:
- ✅ Eligible Grants
- 📋 Justification
- 📂 Missing Documents
- ❗ Ineligible Grants (if any)
"""
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful and precise grant advisor for Singaporean SMEs."},
                    {"role": "user", "content": prompt}
                ]
            )
            st.session_state.response_text = response.choices[0].message.content
            st.success("✅ Eligibility analysis complete.")
        except Exception as e:
            st.error(f"OpenAI API error: {e}")

# === PDF Export Section ===
if st.session_state.get("response_text"):
    st.markdown("### 📋 Results")
    st.markdown(st.session_state.response_text)

    # Download Buttons
    st.markdown("#### 📁 Export Results")
    st.text_area("Output Preview", value=st.session_state.response_text, height=300)

    pdf_bytes = generate_pdf(st.session_state.response_text)
    if pdf_bytes:
        st.download_button("📄 Download as PDF", data=pdf_bytes, file_name="grant_eligibility.pdf")
    st.download_button("📄 Download as Text", st.session_state.response_text, file_name="grant_recommendation.txt")
else:
    st.info("Fill in your business details and click 'Check Eligibility' to get results.")

st.markdown("---")

# === Optional Document Upload ===
st.markdown("### Upload Supporting Business Document (Optional)")
st.markdown("_We’ll analyze your uploaded document to tailor grant recommendations._")
uploaded_file = st.file_uploader("Upload a PDF document (e.g. ACRA BizFile)", type=["pdf"])

doc_summary = ""
auto_data = {}

if uploaded_file:
    try:
        all_text = extract_text_from_pdf(uploaded_file)
        doc_summary = all_text[:2000]
        auto_data = extract_data_from_text(all_text)
        st.success("Document uploaded and analyzed.")
        st.text_area("Extracted Content (preview)", doc_summary, height=180)

        if st.button("Run Document Analysis"):
            with st.spinner("Analyzing document with OpenAI..."):
                try:
                    prompt_doc = f"""
You are an expert on Singapore government grants. A user uploaded the following document (likely an ACRA BizFile or proposal).

Please:
1. Summarize the document in plain English.
2. Explain how this information is relevant to applying for PSG, EDG, or SFEC.
3. Flag any key information that seems missing or unclear.

### Uploaded Document Text:
{all_text[:3000]}
"""
                    doc_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that explains grant-related documents for Singapore SMEs."},
                            {"role": "user", "content": prompt_doc}
                        ]
                    )
                    st.markdown("### 🧾 Document Analysis")
                    st.markdown(doc_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"OpenAI API error during document analysis: {e}")
    except Exception as e:
        st.warning(f"Could not read PDF: {e}")

st.markdown("---")


# === Main App UI ===
st.set_page_config(page_title="Smart Grant Advisor", layout="wide")

# Inject global custom CSS for LanX-style gradient + form elements
st.markdown("""
    <style>
        /* Full-page gradient background */
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(to bottom, #0a0a0a 0%, #0a0a0a 10%, #0d0f1c 30%, #0f111f 60%, #00011d 100%) !important;
            color: #ffffff;
        }

        /* Remove extra white backgrounds in containers */
        .block-container {
            background-color: rgba(0, 0, 0, 0) !important;
        }

        /* Text input, selectbox, textarea styling */
        input, textarea, select {
            background-color: #111729 !important;
            color: #ffffff !important;
            border: 1px solid #2b3a5e !important;
        }

        /* Placeholder text color */
        ::placeholder {
            color: #888 !important;
        }

        /* Button style */
        button[kind="primary"] {
            background-color: #3e6ce2 !important;
            color: white !important;
            border-radius: 8px !important;
        }

        /* Optional: shadow box for main headings */
        h1, h2, h3 {
            text-shadow: 0 0 4px rgba(0,0,0,0.4);
        }
    </style>
""", unsafe_allow_html=True)

# === Tips & Recommendations Section ===
st.header("Tips & Recommendations for Grant Success")
st.markdown("""
Here are some practical tips to improve your chances of securing government grants in Singapore:
""")

tips = [
    "- Use **pre-approved PSG vendors** to speed up your application process.",
    "- Make sure your **ACRA BizFile** is updated within the last 3 months.",
    "- Include a **clear project justification** showing how the solution improves productivity or supports expansion.",
    "- For EDG, demonstrate **capability-building** or **market expansion** plans.",
    "- To qualify for SFEC, ensure you’ve **met CPF and local hiring criteria**, and have no MOM/IRAS violations.",
    "- Prepare **financial statements**, employee records, and vendor quotes in advance.",
    "- Explore **co-funding opportunities** by combining eligible grants (e.g., PSG + SFEC)."
]

for tip in tips:
    st.markdown(f"- {tip}")

st.markdown("---")


# === FAQ Section ===
st.subheader("Ask a Question")

faq = st.text_area("Enter a question about Singapore SME grants, criteria, or your uploaded documents:")

if st.button("Submit"):
    if not faq.strip():
        st.warning("Please enter a question before submitting.")
    else:
        with st.spinner("Thinking..."):
            try:
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful and precise grant advisor for Singaporean SMEs."
                        },
                        {
                            "role": "user",
                            "content": faq
                        }
                    ]
                )
                st.markdown("### 💬 Answer")
                st.markdown(res.choices[0].message.content)
            except Exception as e:
                st.error(f"API error: {e}")
else:
    st.info("Type your question above and click 'Submit FAQ' to get a response.")

st.markdown("---")


# === Feedback Section ===
st.subheader("Feedback")
with st.form("feedback_form"):
    feedback = st.text_area("Your feedback")
    if st.form_submit_button("Submit"):
        st.success("Thank you for your feedback!")

# === Footer ===
st.markdown("---")
st.caption("""
This assistant helps Singapore SMEs explore grant eligibility and guidance.
Not affiliated with GoBusiness or EnterpriseSG. Always confirm details at:
https://www.gobusiness.gov.sg or https://www.enterprisesg.gov.sg
""")



