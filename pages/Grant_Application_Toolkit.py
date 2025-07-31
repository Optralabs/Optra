import streamlit as st
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
import openai

# Setup OpenAI Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ======= Brand Identity Logo Embed (keep your current one) =======
from PIL import Image
import base64
from io import BytesIO

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

# ========== App Title ==========
st.title("Application Readiness Hub")
st.markdown("This tool guides you through preparing for your selected grant application.")

# ========== SME Details ==========
st.subheader("Your SME Profile")
with st.form("sme_form"):
    grant = st.selectbox("Select a Grant", [
        "Enterprise Development Grant (EDG)",
        "Productivity Solutions Grant (PSG)",
        "Market Readiness Assistance (MRA)"
    ])
    company_name = st.text_input("Company Name")
    contact_person = st.text_input("Contact Person")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Generate Application Guide")

# ========== Generate Plan ==========
if submitted and company_name:
    st.markdown("---")
    st.subheader(f"Next Steps for {grant}")

    roadmap = {
        "Enterprise Development Grant (EDG)": [
            "Check your business is registered and operational in Singapore",
            "Prepare latest 2 years of audited financial statements",
            "Define project scope and desired outcomes",
            "Engage a pre-approved consultant (if applicable)",
            "Submit application via Business Grants Portal (BGP)"
        ],
        "Productivity Solutions Grant (PSG)": [
            "Choose a pre-approved vendor",
            "Request vendor quotation",
            "Prepare company ACRA Bizfile",
            "Login to Business Grants Portal and submit"
        ],
        "Market Readiness Assistance (MRA)": [
            "Ensure at least 30% local shareholding",
            "Confirm overseas business expansion intent",
            "Gather vendor quotations",
            "Draft export marketing plan",
            "Submit through Business Grants Portal"
        ]
    }

    st.markdown("### Your Action Checklist")
    for item in roadmap.get(grant, []):
        st.checkbox(item, value=False)

    # ========== Grant-Specific Document Checklist ==========
    st.markdown("### Grant-Specific Document Checklist")
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
    for doc in doc_checklist.get(grant, []):
        st.checkbox(doc, value=False)

    # ========== Email Templates ==========
    st.markdown("### Email Templates")
    st.markdown("**To Vendor (Quotation Request):**")
    vendor_email = f"""
Dear [Vendor Name],

I am reaching out on behalf of {company_name} regarding a quotation for a project we are planning to apply under the {grant}. 

Could you please share a formal quote including project scope and pricing?

Thank you,
{contact_person}
    """
    st.code(vendor_email.strip(), language="text")

    st.markdown("**To Grant Officer (Clarification):**")
    officer_email = f"""
Dear Grant Officer,

I am currently preparing an application for the {grant} on behalf of {company_name}. 

Could I clarify the required documents and eligibility details before submission?

Looking forward to your response.

Best regards,
{contact_person} ({email})
    """
    st.code(officer_email.strip(), language="text")

    st.markdown("---")
    st.success("✅ Application Planner Ready. Begin your preparation today.")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
