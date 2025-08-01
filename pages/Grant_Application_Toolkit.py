import streamlit as st
from datetime import datetime, timedelta
from streamlit_extras.stylable_container import stylable_container
from openai import OpenAI  # ✅ Updated import for new SDK
from PIL import Image
import base64
from io import BytesIO
import plotly.figure_factory as ff
import pandas as pd

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

# ========= Data Structures =========
roadmap = {
    "Productivity Solutions Grant (PSG)": [
        "Identify pre-approved vendor",
        "Get a quotation",
        "Submit application on Business Grants Portal"
    ],
    "Enterprise Development Grant (EDG)": [
        "Define project scope",
        "Prepare project proposal",
        "Submit application on BGP"
    ],
    "Market Readiness Assistance (MRA)": [
        "Identify overseas opportunity",
        "Engage consultant or service provider",
        "Submit application"
    ]
}

doc_checklist = {
    "Enterprise Development Grant (EDG)": [
        "Audited Financial Statements",
        "Project Proposal",
        "Quotations from vendors"
    ],
    "Productivity Solutions Grant (PSG)": [
        "Latest ACRA Bizfile",
        "Vendor Quotation",
        "Company Bank Statement"
    ],
    "Market Readiness Assistance (MRA)": [
        "Company Registration Info",
        "Overseas Marketing Plan",
        "Quotation from Consultant"
    ]
}

# ========= App State Setup =========
st.title("Application Readiness Hub")
st.markdown("This tool guides you through preparing for your selected grant application.")

if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False
if "selected_grant" not in st.session_state:
    st.session_state.selected_grant = None

# ========= Main Form =========
with st.form("sme_form"):
    selected_grant = st.selectbox("Select a Grant", list(roadmap.keys()))
    company_name = st.text_input("Company Name")
    contact_person = st.text_input("Contact Person")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Generate Application Guide")

    if submitted and company_name.strip():
        st.session_state.plan_generated = True
        st.session_state.selected_grant = selected_grant
        st.session_state.company_name = company_name.strip()
        st.session_state.contact_person = contact_person.strip()
        st.session_state.email = email.strip()

# ==== New Gantt timeline generator using Plotly Figure Factory ====
def generate_gantt_timeline(grant_name):
    tasks = roadmap.get(grant_name, [])
    base_date = datetime.today()
    df = []
    for i, task in enumerate(tasks):
        start = base_date + timedelta(days=i * 3)
        finish = start + timedelta(days=2)  # Each task 2 days duration approx
        df.append(dict(Task=task, Start=start, Finish=finish))

    fig = ff.create_gantt(
        df,
        index_col=None,
        show_colorbar=False,
        group_tasks=True,
        title=f"{grant_name} Timeline",
        bar_width=0.3,
        showgrid_x=True,
        showgrid_y=True
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# ==== Helper to render checklists in expanders ====
def render_checklist(title, items, key_prefix):
    with st.expander(title, expanded=True):
        for i, item in enumerate(items):
            st.checkbox(item, key=f"{key_prefix}_{i}")

# ========= Planner UI Output =========
if st.session_state.plan_generated and st.session_state.selected_grant in roadmap:
    st.markdown("---")
    st.subheader(f"Next Steps for {st.session_state.selected_grant}")

    checklist_items = roadmap.get(st.session_state.selected_grant, [])
    docs = doc_checklist.get(st.session_state.selected_grant, [])

    cols = st.columns(2)
    with cols[0]:
        render_checklist("Your Action Checklist", checklist_items, f"checklist_{st.session_state.selected_grant}")
    with cols[1]:
        render_checklist("Grant-Specific Document Checklist", docs, f"doccheck_{st.session_state.selected_grant}")

    st.markdown("### Visual Grant Timeline")
    fig = generate_gantt_timeline(st.session_state.selected_grant)
    st.plotly_chart(fig, use_container_width=True)

# ========= AI Email Generator =========
if st.session_state.plan_generated and st.session_state.selected_grant:
    st.markdown("### AI-Powered Email Generator")

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

    recipient_name = st.text_input("Recipient Name", placeholder="Write Contact's Name Here")
    recipient_email = st.text_input("Recipient Email", placeholder="e.g. contact@vendor.com")

    additional_context = st.text_area(
        "Add any extra context or specific requests (optional)", placeholder="e.g. Need the quote by next Tuesday..."
    )

    if st.button("Generate Email"):
        if not recipient_name or not recipient_email:
            st.warning("Please provide both recipient name and recipient email.")
        else:
            with st.spinner("Composing your email..."):
                try:
                    prompt = f"""
Compose a clear, professional, and customized email.

Details:
- Purpose: {email_purpose}
- Sender Name: {st.session_state.contact_person}
- Sender Email: {st.session_state.email}
- Company: {st.session_state.company_name}
- Grant of Interest: {st.session_state.selected_grant}
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
                    st.code(generated_email, language='markdown')

                    st.download_button("Copy to Clipboard", data=generated_email, file_name="generated_email.txt", mime="text/plain")

                except Exception as e:
                    st.error(f"Failed to generate email. Error: {e}")


# ========= Reset Button =========
def perform_reset():
    for key in list(st.session_state.keys()):
        if key.startswith("checklist_") or key.startswith("doccheck_") or key in ["plan_generated", "selected_grant", "company_name", "contact_person", "email"]:
            del st.session_state[key]

if st.session_state.get("plan_generated"):
    st.button("Reset Planner", on_click=perform_reset)
