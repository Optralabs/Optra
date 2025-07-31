import streamlit as st
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
import openai
from streamlit_timeline import timeline

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

# Sidebar and styling code omitted for brevity — keep yours as is

# Define roadmap and doc_checklist — keep as you have

# ========== App Title ==========
st.title("Application Readiness Hub")
st.markdown("This tool guides you through preparing for your selected grant application.")

# Initialize session state variables
if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False

if "selected_grant" not in st.session_state:
    st.session_state.selected_grant = None

# ========== SME Details Form ==========
with st.form("sme_form"):
    selected_grant = st.selectbox("Select a Grant", [
        "Enterprise Development Grant (EDG)",
        "Productivity Solutions Grant (PSG)",
        "Market Readiness Assistance (MRA)"
    ])
    company_name = st.text_input("Company Name")
    contact_person = st.text_input("Contact Person")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Generate Application Guide")

    if submitted and company_name:
        st.session_state.plan_generated = True
        st.session_state.selected_grant = selected_grant
        st.session_state.company_name = company_name
        st.session_state.contact_person = contact_person
        st.session_state.email = email

# ========== Show Checklist and Details if Plan Generated ==========
if st.session_state.plan_generated:
    st.markdown("---")
    st.subheader(f"Next Steps for {st.session_state.selected_grant}")

    checklist_items = roadmap.get(st.session_state.selected_grant, [])

    st.markdown("### Your Action Checklist")
    for i, item in enumerate(checklist_items):
        checkbox_key = f"checklist_{st.session_state.selected_grant}_{i}"
        st.checkbox(item, key=checkbox_key)

    st.markdown("### Grant-Specific Document Checklist")
    docs = doc_checklist.get(st.session_state.selected_grant, [])
    for i, doc in enumerate(docs):
        checkbox_key = f"doccheck_{st.session_state.selected_grant}_{i}"
        st.checkbox(doc, key=checkbox_key)

    # ===== Timeline visualization =====
    st.markdown("### Visual Grant Timeline")
    timeline_events = []
    for idx, item in enumerate(checklist_items):
        timeline_events.append({
            "content": item,
            "start": datetime.now().strftime("%Y-%m-%d"),
            "type": "box",
            "id": idx + 1
        })

    timeline_data = {
        "title": f"{st.session_state.selected_grant} Preparation Timeline",
        "items": timeline_events
    }

    timeline(timeline_data, height=300)

    # ========== Email Templates ==========
    st.markdown("### Email Templates")
    st.markdown("**To Vendor (Quotation Request):**")
    vendor_email = f"""
Dear [Vendor Name],

I am reaching out on behalf of {st.session_state.company_name} regarding a quotation for a project we are planning to apply under the {st.session_state.selected_grant}. 

Could you please share a formal quote including project scope and pricing?

Thank you,
{st.session_state.contact_person}
    """
    st.code(vendor_email.strip(), language="text")

    st.markdown("**To Grant Officer (Clarification):**")
    officer_email = f"""
Dear Grant Officer,

I am currently preparing an application for the {st.session_state.selected_grant} on behalf of {st.session_state.company_name}. 

Could I clarify the required documents and eligibility details before submission?

Looking forward to your response.

Best regards,
{st.session_state.contact_person} ({st.session_state.email})
    """
    st.code(officer_email.strip(), language="text")

    st.markdown("---")
    st.success("Application Planner Ready. Begin your preparation today.")

# ===== Reset Planner Handling =====
if "reset_triggered" not in st.session_state:
    st.session_state.reset_triggered = False

if st.session_state.plan_generated and not st.session_state.reset_triggered:
    if st.button("Reset Planner"):
        st.session_state.reset_triggered = True
        st.experimental_rerun()

if st.session_state.reset_triggered:
    keys_to_remove = [key for key in list(st.session_state.keys()) if key.startswith("checklist_") or key.startswith("doccheck_")]
    for key in keys_to_remove:
        del st.session_state[key]
    for key in ["plan_generated", "selected_grant", "company_name", "contact_person", "email", "reset_triggered"]:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()
