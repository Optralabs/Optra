import streamlit as st
import openai
from openai import OpenAI
client = OpenAI()
import os
import requests
import datetime
import re
from fpdf import FPDF
from io import BytesIO
import pdfplumber
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from feedback import get_past_good_answers, show_feedback_ui
from globals import *

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from globals import *

def generate_pdf(content: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Times", size=11)

    cleaned_content = clean_text(content)  # clean first

    for line in cleaned_content.split("\n"):
        pdf.multi_cell(0, 10, line)

    pdf_string = pdf.output(dest='S').encode('latin1')
    return pdf_string

def clean_text(text):
    return text.encode('latin1', 'replace').decode('latin1')

# ----------------------------
# Load and embed OPTRA logo
# ----------------------------
import streamlit as st
from PIL import Image
from io import BytesIO
import base64

# Favicon and layout config (MUST come first)
st.set_page_config(
    page_title="Smart Grant Advisor",
    page_icon=Image.open("optra_logo_transparent.png"),
    layout="wide"
)

# Your existing OPTRA logo banner (no changes needed)
def get_logo_base64(path, width=80):
    img = Image.open(path)
    img = img.resize((width, width), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

logo_base64 = get_logo_base64("optra_logo_transparent.png")

st.markdown(
    f"""
    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
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

import streamlit as st
import base64
from PIL import Image
from io import BytesIO
import os

def get_logo_base64(path, size=32):
    img = Image.open(path)
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

import streamlit as st
import base64
from PIL import Image
from io import BytesIO

def get_logo_base64(path="optra_logo_transparent.png", size=32):
    try:
        img = Image.open(path)
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        return None

def set_favicon():
    logo_base64 = get_logo_base64()
    if logo_base64:
        st.markdown(
            f"""
            <link rel="icon" type="image/png" href="data:image/png;base64,{logo_base64}">
            """,
            unsafe_allow_html=True
        )

# Call the function to apply the favicon
set_favicon()

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
-  Upload and analyse documents instantly with the **Grant Application Reviewer**
-  Plan your application journey and track milestones with the **Grant Application Toolkit**
-  Craft professional, grant‑ready emails using the **Grant Email Composer**
-  Stay informed with the latest updates from the **Singapore Grant Newsfeed**

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

st.markdown("---")

import streamlit as st
import re

# Helper function to validate numeric inputs
def validate_numeric_input(value, field_name):
    if value.strip() == "":
        return None
    try:
        num = float(value.replace(',', ''))
        if num < 0:
            st.warning(f"{field_name} cannot be negative.")
            return None
        return num
    except ValueError:
        st.warning(f"Please enter a valid number for {field_name}.")
        return None

# Industry options (expand as needed)
industry_options = [
    "Retail",
    "Food & Beverage",
    "Technology",
    "Manufacturing",
    "Education",
    "Healthcare",
    "Professional Services",
    "Logistics",
    "Construction",
    "Others"
]

business_stage_options = [
    "Startup (Less than 1 year)",
    "Early Stage (1-3 years)",
    "Established (3-10 years)",
    "Scaling / Expansion (>10 years)"
]

digital_adoption_options = [
    "None",
    "Basic digital tools (email, spreadsheets)",
    "Moderate digital tools (ERP, CRM)",
    "Advanced automation or AI"
]

grant_goals = [
    "Business Expansion",
    "Technology Adoption / Digitalisation",
    "Workforce Training & Skills Development",
    "Sustainability / Green Initiatives",
    "Market Expansion / Export",
    "Product or Service Innovation",
    "Cost Reduction / Productivity",
    "Others"
]

# --- About Your Business ---
st.markdown("### About Your Business")

# Assume auto_data extracted from uploaded doc (you can integrate your extraction logic)
auto_data = {}

industry = st.selectbox(
    "Industry / Sector",
    options=industry_options,
    index=industry_options.index(auto_data.get("industry")) if auto_data.get("industry") in industry_options else 0,
    help="Select the primary industry or sector your business operates in."
)

revenue_input = st.text_input(
    "Annual Revenue (SGD)",
    value=str(auto_data.get("revenue", "")),
    help="Enter your annual revenue in Singapore Dollars (e.g., 1500000)."
)
revenue = validate_numeric_input(revenue_input, "Annual Revenue")

employees_input = st.text_input(
    "Number of Employees",
    value=str(auto_data.get("employees", "")),
    help="Total number of full-time employees."
)
employees = validate_numeric_input(employees_input, "Number of Employees")

years_input = st.text_input(
    "Years in Operation",
    value=str(auto_data.get("years", "")),
    help="How many years has your business been operating?"
)
years = validate_numeric_input(years_input, "Years in Operation")

business_stage = st.selectbox(
    "Business Stage / Lifecycle",
    options=business_stage_options,
    help="Select the stage your business is currently at."
)

ownership = st.selectbox(
    "Is Local Ownership ≥30%?",
    options=["Yes", "No"],
    index=0,
    help="Local ownership percentage affects eligibility for some grants."
)

digital_adoption = st.selectbox(
    "Level of Digital Adoption",
    options=digital_adoption_options,
    help="How advanced is your business in using digital or automation tools?"
)

goal = st.selectbox(
    "Primary Grant Objective / Goal",
    options=grant_goals,
    index=0,
    help="Choose the main goal you want to achieve with a grant."
)

additional_goal = st.text_area(
    "Additional Details About Your Grant Goals (optional)",
    help="Add any specific details to clarify your grant objectives."
)

# --- SFEC Specific Details (show only if ownership >=30%) ---
if ownership == "Yes":
    st.markdown("### SFEC Specific Details")

    skills_levy_input = st.text_input(
        "Skills Development Levy Paid Last Year (SGD)",
        help="Amount of Skills Development Levy paid last year (for SFEC eligibility)."
    )
    skills_levy_paid = validate_numeric_input(skills_levy_input, "Skills Development Levy Paid")

    local_employees_input = st.text_input(
        "Number of Local Employees",
        help="Number of employees who are Singapore citizens or PRs."
    )
    local_employees = validate_numeric_input(local_employees_input, "Number of Local Employees")

    violations = st.checkbox(
        "Any outstanding MOM or IRAS violations?",
        value=False,
        help="Outstanding violations can affect grant eligibility."
    )
else:
    skills_levy_paid = None
    local_employees = None
    violations = False

# === Check Eligibility ===
if st.button("Check Eligibility"):
    # === ✅ Ensure session_state stores required feedback context ===
    st.session_state["page_name"] = "Home"
    st.session_state["grant_type"] = goal  # Primary Grant Objective
    st.session_state["industry"] = industry

    with st.spinner("Analyzing eligibility..."):
        try:
            # ✅ Retrieve past good answers for similar queries
            past_answers = get_past_good_answers(f"{industry} | {goal} | {digital_adoption}")
            if past_answers:
                past_context_block = "Here are past highly-rated answers to similar cases:\n" + "\n\n".join(past_answers)
            else:
                past_context_block = ""

            # ✅ Retrieve relevant context from Pinecone
            pinecone_context = get_pinecone_context(
                user_id="test_user",  # TODO: Replace with Supabase-authenticated user ID
                query=f"{industry} {goal} {digital_adoption}",
                top_k=5
            )

            # ✅ Build eligibility prompt (safe, no backslash issues)
            eligibility_prompt_with_context = (
                "You are Smart Grant Advisor, an expert consultant on Singapore government grants specifically for SMEs.\n\n"
                "Here is relevant information from the user's past uploaded documents and stored data:\n"
                f"{pinecone_context}\n\n"
                f"{past_context_block}\n\n"
                "Given the detailed business information below, provide a comprehensive eligibility assessment for applicable government grants. "
                "Consider the SME's industry, business size, years of operation, local ownership, digital adoption level, business stage, and grant goals.\n\n"
                "Analyze suitability for these key Singapore government grants and schemes, but also mention any other relevant grants that may fit the profile:\n\n"
                "- Productivity Solutions Grant (PSG)\n"
                "- Enterprise Development Grant (EDG)\n"
                "- SkillsFuture Enterprise Credit (SFEC)\n"
                "- Career Trial Grant (CTG)\n"
                "- Workforce Singapore P-Max (WSG P-Max)\n"
                "- Startup SG Tech\n"
                "- Enterprise Financing Scheme (EFS)\n"
                "- Agri-Food Cluster Transformation (ACT)\n"
                "- Marine Shipyard Grant\n"
                "- Energy Efficiency Fund (E2F)\n"
                "- Green Incentive Programme (GIP)\n"
                "- Other sector-specific, innovation, or transformation-focused grants\n\n"
                f"### Business Information:\n"
                f"- Industry / Sector: {industry}\n"
                f"- Annual Revenue (SGD): {revenue if revenue is not None else 'Not Provided'}\n"
                f"- Number of Employees: {employees if employees is not None else 'Not Provided'}\n"
                f"- Years in Operation: {years if years is not None else 'Not Provided'}\n"
                f"- Business Stage: {business_stage}\n"
                f"- Local Ownership ≥30%: {ownership}\n"
                f"- Level of Digital Adoption: {digital_adoption}\n"
                f"- Primary Grant Objective / Goal: {goal}\n"
                f"- Additional Goal Details: {additional_goal if additional_goal.strip() != '' else 'None'}\n\n"
                f"### SFEC Specific Details:\n"
                f"- Skills Development Levy Paid Last Year (SGD): {skills_levy_paid if skills_levy_paid is not None else 'Not Provided'}\n"
                f"- Number of Local Employees: {local_employees if local_employees is not None else 'Not Provided'}\n"
                f"- Outstanding MOM or IRAS Violations: {'Yes' if violations else 'No'}\n\n"
                "Please provide your response in clear, professional markdown format with the following sections:\n\n"
                "1. **Eligible Grants**\n   List all grants the SME is likely eligible for based on the provided data. For each, explain *why* the SME qualifies, highlighting specific criteria met.\n\n"
                "2. **Potential Disqualifiers or Missing Information**\n   Identify any factors or missing data that may disqualify or limit eligibility. Offer advice on how to address or improve these areas.\n\n"
                "3. **Required Documents and Evidence**\n   Suggest the essential documents or evidence the SME should prepare for each relevant grant application.\n\n"
                "4. **Additional Recommendations**\n   Offer strategic advice or best practices to improve grant application success, such as timing, combining grants, or building capabilities.\n\n"
                "5. **Other Relevant Grants or Incentives**\n   Suggest any lesser-known or niche grants that may suit the SME’s profile, particularly for their industry or business goals.\n\n"
                "Maintain a balance of professionalism and simplicity to ensure SMEs without deep grant expertise can easily understand and act on your advice.\n"
                "Please return your response in markdown format, structured with headings and bullet points for easy readability by SME owners."
            )

            # ✅ Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful, accurate, and business-friendly grant advisor for Singapore SMEs."},
                    {"role": "user", "content": eligibility_prompt_with_context}
                ]
            )

            # ✅ Save API output
            st.session_state.response_text = response.choices[0].message.content

            # ✅ Save for feedback loop tracking (using SUPABASE_SERVICE_ROLE_KEY in feedback.py)
            st.session_state["last_query"] = eligibility_prompt_with_context
            st.session_state["last_ai_output"] = st.session_state.response_text

            st.success("Eligibility analysis complete.")

        except Exception as e:
            st.error(f"OpenAI API error: {e}")

# === Display & Export Results ===
if st.session_state.get("response_text"):
    st.markdown("### Eligibility Result")
    st.markdown(st.session_state.response_text)

    pdf_bytes = generate_pdf(st.session_state.response_text)
    if pdf_bytes:
        st.download_button("Download Eligibility Report (PDF)", data=pdf_bytes, file_name="grant_eligibility_report.pdf")

    st.download_button("Download Eligibility Report (Text)", data=st.session_state.response_text, file_name="grant_eligibility_report.txt")
    st.text_area("Preview of Report", value=st.session_state.response_text, height=300)
else:
    st.info("Fill in your business details and click 'Check Eligibility' to get a tailored grant report.")

# === Upload Supporting Business Document ===
st.markdown("---")
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

        # === Store in Pinecone immediately ===
        try:
            user_id = "test_user"  # TODO: Replace with actual logged-in user ID from Supabase
            add_document(
                text=all_text,
                doc_id_prefix=f"userdoc_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                metadata={"type": "grant_doc", "source": "upload"},
                user_id=user_id
            )
            st.info("📌 Document saved to Pinecone for future context and search.")
        except Exception as e:
            st.warning(f"Could not store document in Pinecone: {e}")

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
                    st.markdown("### Document Analysis")
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
    st.info("Type your question above and click 'Submit' to get a response.")

st.markdown("---")

# === Unified Feedback Loop ===
if "last_ai_output" in st.session_state and st.session_state["last_ai_output"]:
    show_feedback_ui(
        st.session_state.get("last_query", ""),
        st.session_state.get("last_ai_output", "")
    )

# === Footer ===
st.markdown("---")
st.caption("""
This assistant helps Singapore SMEs explore grant eligibility and guidance.
Not affiliated with GoBusiness or EnterpriseSG. Always confirm details at:
https://www.gobusiness.gov.sg or https://www.enterprisesg.gov.sg
""")

# =========================
# 📌 Save all key interactions to Pinecone
# =========================

# 1. Save Eligibility Results
if st.session_state.get("last_ai_output"):
    save_user_interaction(
        interaction_type="eligibility_result",
        content=st.session_state["last_ai_output"],
        metadata={
            "page": "eligibility_checker",
            "industry": st.session_state.get("industry"),
            "grant_type": st.session_state.get("grant_type")
        }
    )

# 2. Save FAQ Q&A
if "faq" in locals() and faq.strip() and st.session_state.get("last_ai_output"):
    save_user_interaction(
        interaction_type="faq_answer",
        content=f"Q: {faq}\nA: {st.session_state['last_ai_output']}",
        metadata={"page": "faq"}
    )

# 3. Save Uploaded Document Info
if "uploaded_file" in locals() and uploaded_file:
    save_user_interaction(
        interaction_type="uploaded_doc",
        content=f"Uploaded: {uploaded_file.name}",
        metadata={"page": "grant_application_reviewer"}
    )

