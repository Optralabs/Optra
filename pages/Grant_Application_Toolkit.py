import streamlit as st
from datetime import datetime, timedelta
from streamlit_extras.stylable_container import stylable_container
import openai
from PIL import Image
import base64
from io import BytesIO
import plotly.graph_objects as go
import pandas as pd

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ======= Brand Identity Logo Embed =======
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
        "Identify IT solution or equipment vendor",
        "Obtain official quotation from pre-approved vendor",
        "Ensure your business is registered and operating in Singapore",
        "Confirm that your purchase is not made before the grant application",
        "Submit application via Business Grants Portal"
    ],
    "Enterprise Development Grant (EDG)": [
        "Define project scope and objectives",
        "Gather financial statements for past 3 years",
        "Prepare project proposal with clear deliverables",
        "Get official quotation from a third-party consultant/vendor",
        "Ensure business is at least 30% locally owned"
    ],
    "Market Readiness Assistance (MRA)": [
        "Confirm overseas market you intend to enter",
        "Gather quotations from third-party vendors (e.g., marketing, business matching)",
        "Ensure service providers are not related to your company",
        "Draft a marketing/expansion plan specific to overseas market",
        "Submit MRA application via Business Grants Portal before incurring expenses"
    ]
}

doc_checklist = {
    "Enterprise Development Grant (EDG)": [
        "ACRA Bizfile",
        "Audited Financial Statements (last 2 years)",
        "Project Proposal Document",
        "Vendor Quotation",
        "Company's Financial Projections"
    ],
    "Productivity Solutions Grant (PSG)": [
        "ACRA Bizfile",
        "Pre-approved Vendor Quotation",
        "Screenshots of Quoted IT Solution",
        "Purchase Order (if applicable)",
        "Product Brochure / Specs Sheet"
    ],
    "Market Readiness Assistance (MRA)": [
        "ACRA Bizfile",
        "Vendor Quotation",
        "Proposed Marketing Plan",
        "Proof of Overseas Market Interest",
        "Company Bank Statement"
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

# ========= Clean Horizontal Timeline =========
def generate_clean_timeline(grant_name):
    checklist = roadmap.get(grant_name, [])
    base_date = datetime.today()
    df = pd.DataFrame({
        "Task": checklist,
        "Date": [base_date + timedelta(days=i * 3) for i in range(len(checklist))]
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=[1] * len(df),
        mode="markers+text",
        marker=dict(size=14, color="#3e6ce2"),
        text=df["Task"],
        textposition="top center",
        hovertemplate="<b>%{text}</b><br>%{x|%b %d, %Y}<extra></extra>"
    ))

    fig.update_layout(
        title=f"{grant_name} Timeline",
        xaxis=dict(title="Date", showgrid=False),
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    return fig

# ========= Planner UI Output =========
if st.session_state.plan_generated and st.session_state.selected_grant in roadmap:
    st.markdown("---")
    st.subheader(f"Next Steps for {st.session_state.selected_grant}")

    checklist_items = roadmap.get(st.session_state.selected_grant, [])
    docs = doc_checklist.get(st.session_state.selected_grant, [])

    st.markdown("### Your Action Checklist")
    for i, item in enumerate(checklist_items):
        checkbox_key = f"checklist_{st.session_state.selected_grant}_{i}"
        st.checkbox(item, key=checkbox_key)

    st.markdown("### Grant-Specific Document Checklist")
    for i, doc in enumerate(docs):
        checkbox_key = f"doccheck_{st.session_state.selected_grant}_{i}"
        st.checkbox(doc, key=checkbox_key)

    st.markdown("### Visual Grant Timeline")
    fig = generate_clean_timeline(st.session_state.selected_grant)
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
            "Custom: Write your own"
        ]
    )

    additional_context = st.text_area(
        "Add any extra context or specific requests (optional)", placeholder="e.g. Need the quote by next Tuesday..."
    )

    if st.button("Generate Email"):
        with st.spinner("Composing your email..."):
            try:
                prompt = f"""Generate a concise, professional email for the following scenario:

- Purpose: {email_purpose}
- Company: {st.session_state.company_name}
- Contact Person: {st.session_state.contact_person}
- Grant: {st.session_state.selected_grant}
- Email: {st.session_state.email}
- Additional Context: {additional_context if additional_context else "None"}

Keep it formal, polite, and ready to send."""
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a business writing assistant that drafts grant-related emails."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=500
                )
                generated_email = response.choices[0].message.content.strip()
                st.text_area("Generated Email", value=generated_email, height=200)
            except Exception as e:
                st.error(f"Failed to generate email. Error: {e}")


    st.success("Application Planner Ready. Begin your preparation today.")

# ========= Reset Button =========
def perform_reset():
    for key in list(st.session_state.keys()):
        if key.startswith("checklist_") or key.startswith("doccheck_") or key in ["plan_generated", "selected_grant", "company_name", "contact_person", "email"]:
            del st.session_state[key]

if st.session_state.get("plan_generated"):
    st.button("Reset Planner", on_click=perform_reset)
