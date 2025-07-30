import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from typing import List, Tuple, Dict
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container

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

# ========== Page Config ==========
st.set_page_config(page_title="Live Grant Insights", layout="wide")
st.title("Live Grant Insights")

# ========== Sidebar or Top Filter Section ==========
st.markdown("### Tell us about your business")

with st.form("business_profile_form"):
    col1, col2 = st.columns(2)

    with col1:
        biz_name = st.text_input("Business Name")
        sector = st.selectbox("Sector", ["Retail", "F&B", "Manufacturing", "Professional Services", "Logistics", "Healthcare", "Other"])
        revenue = st.selectbox("Annual Revenue", ["< S$100k", "S$100k - S$500k", "S$500k - S$1M", "> S$1M"])

    with col2:
        staff_count = st.selectbox("Number of Employees", ["1-5", "6-20", "21-50", "> 50"])
        goal = st.selectbox("Main Business Goal", [
            "Digitalisation", "Overseas Expansion", "Product Development",
            "Automation", "Sustainability", "Training & Capability Building"
        ])
        submitted = st.form_submit_button("Show Grant Insights")

# ========== Cache Grant Fetching Functions ========== 
@st.cache_data(ttl=3600)
def fetch_sample_grants() -> List[Dict]:
    """ Placeholder for live scraping or API fetch. Replace this with real data.gov.sg or ESG API."""
    return [
        {"name": "Productivity Solutions Grant (PSG)", "summary": "Support for digital tools and equipment.", "type": "Digitalisation", "link": "https://www.gobusiness.gov.sg/grants/psg"},
        {"name": "Enterprise Development Grant (EDG)", "summary": "Help companies grow and transform.", "type": "Capability Building", "link": "https://www.gobusiness.gov.sg/grants/edg"},
        {"name": "Market Readiness Assistance (MRA)", "summary": "Support for international expansion.", "type": "Overseas Expansion", "link": "https://www.gobusiness.gov.sg/grants/mra"},
    ]

# ========== GPT-Powered Grant Matching ========== 
@st.cache_data(show_spinner=False)
def score_grant_match(grant: Dict, sector: str, revenue: str, staff_count: str, goal: str) -> Tuple[int, str]:
    from openai import OpenAI
    import os
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    prompt = f"""
    You are a Singapore grant consultant. A business in the {sector} sector with {staff_count} employees and {revenue} annual revenue wants to pursue {goal}. Evaluate if they qualify for the following grant:

    Grant Name: {grant['name']}
    Summary: {grant['summary']}

    Score the match out of 100. Also provide a 1-paragraph justification.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw = response.choices[0].message.content
    score_line = next((line for line in raw.split("\n") if any(char.isdigit() for char in line)), "")
    score = int(''.join(filter(str.isdigit, score_line))) if score_line else 50
    return score, raw.strip()

# ========== Grant Results ========== 
if submitted:
    st.markdown("---")
    st.subheader("Matched Grants for You")

    grants = fetch_sample_grants()

    for grant in grants:
        score, summary = score_grant_match(grant, sector, revenue, staff_count, goal)
        with stylable_container(key=f"grant_{grant['name']}", css_styles="border:1px solid #DDD; padding:1em; border-radius:12px; margin-bottom: 1em"):
            st.markdown(f"**{grant['name']}** — *{grant['type']}*")
            st.markdown(f" [View Grant Info]({grant['link']})")
            clamped_score = max(0, min(100, float(score)))
            import streamlit as st
            import streamlit.components.v1 as components

            def custom_progress_bar(score: float):
                # Clamp value between 0 and 100
                score = max(0, min(score, 100))
                percent = int(score)

                bar_color = "#2F49F4"  # Glow Blue
                bg_color = "#0B0E28"   # Grid Background

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

# Example usage
custom_progress_bar(score=74.3)

            st.markdown(f"**Score:** {score}/100")
            st.markdown(f"**Analysis:** {summary}")

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
