import streamlit as st
import requests
import datetime
from bs4 import BeautifulSoup
from PIL import Image
import base64
from io import BytesIO
from typing import List, Dict

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="Live Grant Insights", layout="wide")

# -----------------------
# Load and embed OPTRA logo
# -----------------------
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

# -----------------------
# Global CSS
# -----------------------
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        section[data-testid="stSidebar"] .css-1v0mbdj,
        section[data-testid="stSidebar"] .css-1wvsk6o {
            color: #ffffff !important;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(to bottom, #0a0a0a 0%, #0a0a0a 10%, #0d0f1c 30%, #0f111f 60%, #00011d 100%) !important;
            color: #ffffff;
        }
        .block-container {
            background-color: rgba(0, 0, 0, 0) !important;
        }
        input, textarea, select {
            background-color: #111729 !important;
            color: #ffffff !important;
            border: 1px solid #2b3a5e !important;
        }
        ::placeholder {
            color: #888 !important;
        }
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

# -----------------------
# Header
# -----------------------
st.title("Live Grant Insights for Singapore SMEs")
st.markdown("Real-time SME grant intelligence, customized for your business.")

# -----------------------
# SMART FILTERS
# -----------------------
with st.sidebar:
    st.header("🔍 Smart Grant Filter")
    sector = st.selectbox("Industry Sector", ["Retail", "Manufacturing", "F&B", "Tech", "Others"])
    revenue = st.selectbox("Annual Revenue", ["< $500k", "$500k–$1M", "$1M–$5M", "> $5M"])
    headcount = st.selectbox("Employee Count", ["< 10", "10–50", "51–100", "> 100"])
    intent = st.multiselect("Business Goal", ["Go Digital", "Expand Overseas", "Upskill Staff", "Automate Ops"])

# -----------------------
# GRANT FEED (SIMULATED API)
# -----------------------
@st.cache_data(ttl=1800)
def fetch_grant_feed() -> List[Dict]:
    return [
        {
            "name": "Productivity Solutions Grant (PSG)",
            "desc": "Support for adoption of pre-approved digital solutions.",
            "type": "Digitalisation",
            "match_score": 92,
            "link": "https://www.gobusiness.gov.sg/psg"
        },
        {
            "name": "Enterprise Development Grant (EDG)",
            "desc": "Helps companies upgrade capabilities, innovate or expand overseas.",
            "type": "Growth/Innovation",
            "match_score": 84,
            "link": "https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant/overview"
        },
        {
            "name": "Market Readiness Assistance (MRA)",
            "desc": "Supports overseas expansion through market entry, marketing, etc.",
            "type": "International Expansion",
            "match_score": 78,
            "link": "https://www.enterprisesg.gov.sg/mra"
        },
        {
            "name": "SkillsFuture Enterprise Credit (SFEC)",
            "desc": "Additional funding for workforce transformation and job redesign.",
            "type": "Workforce",
            "match_score": 65,
            "link": "https://www.skillsfuture.gov.sg/sfec"
        }
    ]

# -----------------------
# DISPLAY GRANTS BASED ON FILTERS
# -----------------------
def display_filtered_grants(grants: List[Dict]):
    st.subheader("🔎 Matching Grants For You")
    for grant in grants:
        if grant["match_score"] > 70:
            st.markdown(f"""
                <div style='border:1px solid #2b3a5e; padding:1rem; border-radius:10px; margin-bottom:1rem;'>
                    <h4 style='margin-bottom:0.2rem;'>{grant['name']}</h4>
                    <p style='margin:0.3rem 0;'>{grant['desc']}</p>
                    <p><b>Focus:</b> {grant['type']} | <b>Success Likelihood:</b> {grant['match_score']}%</p>
                    <a href="{grant['link']}" target="_blank">🔗 View Details</a>
                </div>
            """, unsafe_allow_html=True)

# -----------------------
# PSG VENDOR LOOKUP
# -----------------------
@st.cache_data(ttl=3600)
def fetch_psg_vendors() -> Dict[str, List[str]]:
    return {
        "Retail": ["Vend POS", "StoreHub", "Qashier"],
        "F&B": ["FoodZaps", "Oddle", "TabSquare"],
        "Tech": ["Microsoft 365", "Xero", "Freshworks"],
        "Others": ["Generic Vendor A", "Generic Vendor B"]
    }

st.divider()
st.subheader("⚙️ PSG Vendor Recommendations")
psg_vendors = fetch_psg_vendors()
if sector in psg_vendors:
    for vendor in psg_vendors[sector]:
        st.markdown(f"- ✅ {vendor}")
else:
    st.markdown("No sector-specific vendors found.")

# -----------------------
# BONUS: DATASET DISCOVERY
# -----------------------
@st.cache_data(ttl=86400)
def discover_datasets(query="grant"):
    url = "https://data.gov.sg/api/action/package_search"
    try:
        res = requests.get(url, params={"q": query}, timeout=10)
        res.raise_for_status()
        data = res.json()["result"]["results"]
        return [(d["title"], d["resources"][0]["url"]) for d in data if d.get("resources")]
    except:
        return []

with st.expander("📚 Discover Government Grant Datasets"):
    datasets = discover_datasets()
    if datasets:
        for title, link in datasets:
            st.markdown(f"- [{title}]({link})")
    else:
        st.write("No datasets available or API error.")

# -----------------------
# Render Final Grant Feed
# -----------------------
display_filtered_grants(fetch_grant_feed())

# -----------------------
# 4. Quick Links Section
# -----------------------
st.divider()
st.subheader(" Quick Grant Resources")
st.markdown("""
- [GoBusiness Grant Navigator](https://www.gobusiness.gov.sg/gov-assist/grants/)
- [EnterpriseSG Financial Assistance Directory](https://www.enterprisesg.gov.sg/financial-assistance)
- [PSG Pre-approved Solutions](https://www.gobusiness.gov.sg/productivity-solutions-grant/solutions/)
- [Startup SG](https://www.startupsg.gov.sg/)
- [SkillsFuture Enterprise Credit (SFEC)](https://www.skillsfuture.gov.sg/sfec)
- [Market Readiness Assistance (MRA)](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/market-readiness-assistance/overview)
""")
