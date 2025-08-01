import streamlit as st
from datetime import datetime, timedelta
from streamlit_extras.stylable_container import stylable_container
from openai import OpenAI 
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

def generate_gantt_timeline(grant_name, submission_date, include_buffer=True):
    tasks = roadmap.get(grant_name, [])
    total_tasks = len(tasks)
    if total_tasks == 0:
        return None

    duration_per_task = 2
    buffer_days = 1 if include_buffer else 0
    step = duration_per_task + buffer_days

    df = []
    for i, task in enumerate(reversed(tasks)):
        finish = submission_date - timedelta(days=i * step)
        start = finish - timedelta(days=duration_per_task)
        df.append(dict(Task=task, Start=start, Finish=finish))

    df = df[::-1]

    fig = ff.create_gantt(
        df,
        index_col=None,
        show_colorbar=False,
        group_tasks=True,
        title=f"{grant_name} Timeline",
        bar_width=0.5,
        showgrid_x=True,
        showgrid_y=True,
        height=350,
        colors=["#3e6ce2"],
        show_hover_fill=True
    )

    fig.update_layout(
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        margin=dict(l=120, r=40, t=60, b=40),
        yaxis=dict(
            autorange='reversed',
            tickfont=dict(size=13),
            title=dict(text='Tasks', font=dict(size=14)),
            gridcolor='rgba(255,255,255,0.1)',
        ),
        xaxis=dict(
            title=dict(text='Date'),
            tickformat='%b %d',
            gridcolor='rgba(255,255,255,0.1)',
            zeroline=False,
        )
    )
    return fig

def render_checklist(title, items, key_prefix):
    if title: 
        st.markdown(f"### {title}")
    for i, item in enumerate(items):
        checkbox_key = f"{key_prefix}_{i}"
        st.checkbox(str(item), key=checkbox_key)

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

    # Move "Customize Timeline" and chart here, below the checklists
    st.subheader("Customize Timeline")

    submission_date = st.date_input(
        "Target Submission Date", 
        value=datetime.today() + timedelta(days=30),
        min_value=datetime.today()
    )

    include_buffer = st.checkbox("Include 1 day buffer between tasks", value=True)

    st.markdown("\n")
    st.markdown("\n")

    st.markdown("### Visual Grant Timeline")
    fig = generate_gantt_timeline(
        st.session_state.selected_grant,
        submission_date,
        include_buffer
    )

    st.plotly_chart(fig, use_container_width=True)

    # Call OpenAI with dynamic analysis prompt for the selected grant
    with st.expander("AI Grant Analysis"):
        if st.button("Generate Insights for Application Success"):
            with st.spinner("Analyzing grant insights..."):
                try:
                    dynamic_prompt = f"""
You are a grant advisor. Analyze the key steps and document readiness for a company preparing to apply for the {st.session_state.selected_grant}. 
Company: {st.session_state.company_name}. Contact: {st.session_state.contact_person} ({st.session_state.email}).
Submission Target: {submission_date.strftime('%Y-%m-%d')}.
Give:
1. Common mistakes SMEs make in this grant.
2. Personalized preparation tips.
3. Key do's and don'ts to improve chances.
"""
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert in Singapore government grant processes for SMEs."},
                            {"role": "user", "content": dynamic_prompt}
                        ],
                        temperature=0.5,
                        max_tokens=700
                    )

                    insight = response.choices[0].message.content.strip()
                    st.text_area("Insights from AI Reviewer", value=insight, height=300)
                except Exception as e:
                    st.error(f"Error: {e}")

else:
    st.info("Select a grant and click 'Generate Application Guide' to see your timeline and next steps.")

st.markdown("---")

# ========= Reset Button =========
def perform_reset():
    for key in list(st.session_state.keys()):
        if key.startswith("checklist_") or key.startswith("doccheck_") or key in ["plan_generated", "selected_grant", "company_name", "contact_person", "email"]:
            del st.session_state[key]

if st.session_state.get("plan_generated"):
    st.button("Reset Planner", on_click=perform_reset)
