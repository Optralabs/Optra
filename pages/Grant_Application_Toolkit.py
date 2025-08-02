import streamlit as st
from datetime import datetime, timedelta
from streamlit_extras.stylable_container import stylable_container
from openai import OpenAI 
from PIL import Image
import base64
from io import BytesIO
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
    ],
    "Startup SG Founder": [
        "Attend mandatory workshop",
        "Prepare business proposal",
        "Submit through Accredited Mentor Partner"
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
    ],
    "Startup SG Founder": [
        "Pitch Deck",
        "Mentor Endorsement",
        "Workshop Certificate"
    ]
}

st.title("Application Readiness Hub")
st.markdown("This tool guides you through preparing for your selected grant application.")

if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False
if "selected_grant" not in st.session_state:
    st.session_state.selected_grant = None

with st.form("sme_form"):
    selected_grant = st.selectbox("Select a Grant", list(roadmap.keys()))
    company_name = st.text_input("Company Name")
    contact_person = st.text_input("Your Name")
    email = st.text_input("Your Email")
    submitted = st.form_submit_button("Generate Application Guide")

    if submitted and company_name.strip():
        st.session_state.plan_generated = True
        st.session_state.selected_grant = selected_grant
        st.session_state.company_name = company_name.strip()
        st.session_state.contact_person = contact_person.strip()
        st.session_state.email = email.strip()

def render_checklist(title, items, key_prefix):
    st.subheader(title)
    for idx, item in enumerate(items):
        item_key = f"{key_prefix}_item_{idx}"
        explain_key = f"{key_prefix}_explain_{idx}"
        toggle_key = f"{key_prefix}_toggle_{idx}"

        st.checkbox(item, key=item_key)

        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Explain", key=explain_key):
                st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)

        if st.session_state.get(toggle_key):
            with st.spinner("Generating explanation..."):
                if f"{toggle_key}_text" not in st.session_state:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert grant consultant helping simplify tasks."},
                            {"role": "user", "content": f"Explain and simplify this grant application task: '{item}'"}
                        ],
                        temperature=0.5,
                        max_tokens=300
                    )
                    st.session_state[f"{toggle_key}_text"] = response.choices[0].message.content

            st.markdown(
                f"""
                <div style="background-color:#111729; color: #ffffff; padding:1rem; border-radius:8px; margin-top:0.5rem; margin-bottom:1rem; max-width:90%;">
                    <strong style="color: #8ab4f8;">Explanation:</strong><br>{st.session_state[f"{toggle_key}_text"]}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Close explanation", key=f"{toggle_key}_close"):
                st.session_state[toggle_key] = False

if st.session_state.plan_generated and st.session_state.selected_grant in roadmap:
    st.markdown("---")
    st.subheader(f"Next Steps for {st.session_state.selected_grant}")

    checklist_items = roadmap.get(st.session_state.selected_grant, [])
    docs = doc_checklist.get(st.session_state.selected_grant, [])

    cols = st.columns(2)
    with cols[0]:
        with st.expander("Your Action Checklist", expanded=True):
            render_checklist("", checklist_items, f"checklist_{st.session_state.selected_grant}")
    with cols[1]:
        with st.expander("Grant-Specific Document Checklist", expanded=True):
            render_checklist("", docs, f"doccheck_{st.session_state.selected_grant}")

    st.markdown("---")
    st.subheader("AI-Powered Dynamic Timeline")

    submission_date = st.date_input(
        "Target Submission Date", 
        value=datetime.today() + timedelta(days=30),
        min_value=datetime.today()
    )

    if st.button("Generate Timeline Guide"):
        with st.spinner("Generating detailed timeline..."):
            prompt = f"""
You are an expert grant consultant. Create a detailed, step-by-step action timeline for an SME applying for the {st.session_state.selected_grant}.
Submission Date: {submission_date.strftime('%Y-%m-%d')}
List the steps in a bullet format with short actionable instructions, organized by week or phase.
Only return the formatted plan.
"""
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You help SMEs plan grant applications efficiently."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=800
                )
                timeline_text = response.choices[0].message.content.strip()
                st.markdown("### Timeline Plan")
                st.markdown(timeline_text)
            except Exception as e:
                st.error(f"Error generating timeline: {e}")

else:
    st.info("Select a grant and click 'Generate Application Guide' to see your timeline and next steps.")

def perform_reset():
    for key in list(st.session_state.keys()):
        if key.startswith("checklist_") or key.startswith("doccheck_") or key in ["plan_generated", "selected_grant", "company_name", "contact_person", "email"]:
            del st.session_state[key]

if st.session_state.get("plan_generated"):
    st.button("Reset Planner", on_click=perform_reset)

# ========= Reset Button =========
def perform_reset():
    for key in list(st.session_state.keys()):
        if key.startswith("checklist_") or key.startswith("doccheck_") or key in ["plan_generated", "selected_grant", "company_name", "contact_person", "email"]:
            del st.session_state[key]

if st.session_state.get("plan_generated"):
    st.button("Reset Planner", on_click=perform_reset)
