import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from typing import List, Tuple, Dict
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
from utils.grant_scoring import score_grant_match
from utils.grant_data import fetch_sample_grants

# ======= Securely get OpenAI key from Streamlit secrets =======
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ======= Logo embed setup (unchanged) =======
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

# ======= Sidebar and page styling (unchanged) =======
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        section[data-testid="stSidebar"] .css-1v0mbdj, 
        section[data-testid="stSidebar"] .css-1wvsk6o {
            color: #ffffff !important;
        }
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

st.set_page_config(page_title="Live Grant Insights", layout="wide")

st.title("Live Grant Insights")
st.markdown("Stay ahead with actionable recommendations tailored to your business.")

# Simulated user inputs (replace these with session state or inputs later)
sector = st.session_state.get("sector", "Retail")
revenue = st.session_state.get("revenue", 500000)
staff_count = st.session_state.get("staff_count", 10)
goal = st.session_state.get("goal", "Expand operations")

# === GPT: Application Readiness Checklist ===
def get_readiness_checklist(grant_name, grant_type, sector):
    prompt = f"""
    You are a government grants consultant in Singapore. The SME is considering applying for a grant called '{grant_name}' which is a '{grant_type}' type of grant. 
    The business is in the '{sector}' sector. 

    Provide a checklist (3-6 items max) of documents or preparation steps this SME must complete before applying. 
    Each item should be short and specific.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful SME grant consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )
        checklist_text = response['choices'][0]['message']['content']
        return checklist_text
    except Exception as e:
        return f"Could not generate checklist: {e}"

# === Custom Progress Bar ===
def custom_progress_bar(score: float):
    score = max(0, min(score, 100))
    percent = int(score)
    bar_color = "#2F49F4"
    bg_color = "#0B0E28"

    bar_html = f"""
    <div style="width: 100%; background-color: {bg_color}; border-radius: 10px; padding: 3px;">
        <div style="
            width: {percent}%;
            background-color: {bar_color};
            height: 20px;
            border-radius: 7px;
            transition: width 0.4s ease-in-out;">
        </div>
    </div>
    <p style="color: #F5F5F5; font-size: 16px; margin-top: 6px;">Eligibility Score: {percent}%</p>
    """
    components.html(bar_html, height=60)

# === Grant Matching Results ===
grants = fetch_sample_grants()
for grant in grants:
    score, summary = score_grant_match(grant, sector, revenue, staff_count, goal)

    with stylable_container(key=f"grant_{grant['name']}", css_styles="""
        border: 1px solid #DDD;
        padding: 1em;
        border-radius: 12px;
        margin-bottom: 1.5em;
        background-color: #ffffff0a;
    """):
        st.markdown(f"### **{grant['name']}**")
        st.markdown(f"*Type:* {grant['type']} | [View Grant Info]({grant['link']})")
        st.markdown(f"**Why it matches:** {summary}")
        custom_progress_bar(score)

        with st.expander("Application Readiness Checklist"):
            checklist = get_readiness_checklist(grant['name'], grant['type'], sector)
            st.markdown(checklist)

# ========== Quick Links Always Visible ==========
st.markdown("---")
st.subheader("Quick Links & Grant Resources")
quick_links = {
    "Productivity Solutions Grant (PSG)": "https://www.gobusiness.gov.sg/grants/psg",
    "Enterprise Development Grant (EDG)": "https://www.gobusiness.gov.sg/grants/edg",
    "Market Readiness Assistance (MRA)": "https://www.gobusiness.gov.sg/grants/mra",
    "Startup SG": "https://www.startupsg.gov.sg/",
    "SkillsFuture Enterprise Credit (SFEC)": "https://www.gobusiness.gov.sg/grants/sfec",
    "GoBusiness Gov Assist Portal": "https://www.gobusiness.gov.sg/grant-assist"
}

cols = st.columns(3)
for i, (title, link) in enumerate(quick_links.items()):
    with cols[i % 3]:
        st.markdown(f"[{title}]({link})")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Data will refresh hourly.")
