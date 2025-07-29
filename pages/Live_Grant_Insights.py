import streamlit as st
import requests
import datetime
from bs4 import BeautifulSoup
from typing import List, Dict
import openai

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
st.title("Live Grant Insights for Singapore SMEs")
st.markdown("Real-time SME grant intelligence, customized for your business.")

# ======= Sidebar filters for user input =======
with st.sidebar:
    st.header("🔍 Smart Grant Filter")
    sector = st.selectbox("Industry Sector", ["Retail", "Manufacturing", "F&B", "Tech", "Others"])
    revenue = st.selectbox("Annual Revenue", ["< $500k", "$500k–$1M", "$1M–$5M", "> $5M"])
    headcount = st.selectbox("Employee Count", ["< 10", "10–50", "51–100", "> 100"])
    intent = st.multiselect("Business Goal", ["Go Digital", "Expand Overseas", "Upskill Staff", "Automate Ops"])

# ======= Fetch grants dynamically from a public source (example: gov.sg datasets) =======
@st.cache_data(ttl=3600)
def fetch_live_grants() -> List[Dict]:
    # Example: Fetch list of grants from data.gov.sg or mock public API
    # For demo, static mock data simulates live fetch.
    # Replace this with your actual API/scraper fetching logic.
    grants = [
        {
            "name": "Productivity Solutions Grant (PSG)",
            "desc": "Supports adoption of IT solutions and equipment to enhance business processes.",
            "type": "Digitalisation",
            "url": "https://www.gobusiness.gov.sg/psg",
            "tags": ["Go Digital", "Automate Ops"],
            "sector": ["Retail", "Manufacturing", "F&B", "Tech", "Others"],
            "min_revenue": "< $5M",
            "max_revenue": "> $0",
            "min_headcount": "< 100",
        },
        {
            "name": "Enterprise Development Grant (EDG)",
            "desc": "Supports projects that help upgrade business capabilities, innovate, and expand overseas.",
            "type": "Growth/Innovation",
            "url": "https://www.enterprisesg.gov.sg/financial-assistance/grants/enterprise-development-grant",
            "tags": ["Expand Overseas", "Go Digital"],
            "sector": ["Retail", "Manufacturing", "F&B", "Tech", "Others"],
            "min_revenue": "$500k–$1M",
            "max_revenue": "> $0",
            "min_headcount": "10–50",
        },
        {
            "name": "Market Readiness Assistance (MRA)",
            "desc": "Supports overseas market expansion including market set-up and identification.",
            "type": "International Expansion",
            "url": "https://www.enterprisesg.gov.sg/mra",
            "tags": ["Expand Overseas"],
            "sector": ["Retail", "Manufacturing", "F&B", "Tech", "Others"],
            "min_revenue": "$1M–$5M",
            "max_revenue": "> $0",
            "min_headcount": "10–50",
        },
        {
            "name": "SkillsFuture Enterprise Credit (SFEC)",
            "desc": "Encourages employers to invest in workforce skills and transformation.",
            "type": "Workforce",
            "url": "https://www.skillsfuture.gov.sg/sfec",
            "tags": ["Upskill Staff"],
            "sector": ["Retail", "Manufacturing", "F&B", "Tech", "Others"],
            "min_revenue": "< $5M",
            "max_revenue": "> $0",
            "min_headcount": "< 100",
        }
    ]
    return grants

# ======= Eligibility scoring prompt for GPT =======
def generate_eligibility_prompt(grant: Dict, user_data: Dict) -> str:
    prompt = f"""
You are an expert SME grants consultant. Given the following grant information and user business profile, evaluate the eligibility and match score (0-100) and provide a short justification.

Grant:
Name: {grant['name']}
Description: {grant['desc']}
Type: {grant['type']}
Applicable sectors: {', '.join(grant.get('sector', []))}
Business size constraints: Revenue {grant.get('min_revenue')} to {grant.get('max_revenue')}, Headcount min {grant.get('min_headcount')}

User Business Profile:
Sector: {user_data['sector']}
Revenue: {user_data['revenue']}
Headcount: {user_data['headcount']}
Business Goals: {', '.join(user_data['intent'])}

Answer in JSON format with keys: "match_score" (0-100), "justification" (string).
"""
    return prompt.strip()

# ======= Call OpenAI GPT to evaluate eligibility and generate advice =======
@st.cache_data(ttl=900)
def gpt_evaluate_grant(grant: Dict, user_data: Dict) -> Dict:
    prompt = generate_eligibility_prompt(grant, user_data)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        # Expecting JSON response
        import json
        result = json.loads(content)
        # Ensure keys exist and correct types
        match_score = int(result.get("match_score", 0))
        justification = result.get("justification", "")
        return {"match_score": match_score, "justification": justification}
    except Exception as e:
        # Fail gracefully with zero score and error justification
        return {"match_score": 0, "justification": f"Error evaluating eligibility: {e}"}

# ======= Filter grants by user input & get GPT-based scoring =======
def filter_and_score_grants(grants: List[Dict], user_data: Dict) -> List[Dict]:
    filtered = []
    for grant in grants:
        # Quick filter by sector
        if user_data['sector'] not in grant['sector']:
            continue
        # Revenue and headcount are strings like "< $500k", "10-50", so naive filtering below:
        # (Could be improved to numeric ranges if you want)
        # For demo, just allow all; GPT scoring will refine the fit
        score_data = gpt_evaluate_grant(grant, user_data)
        if score_data["match_score"] > 40:  # Threshold for display
            combined = grant.copy()
            combined.update(score_data)
            filtered.append(combined)
    # Sort descending by match score
    return sorted(filtered, key=lambda x: x["match_score"], reverse=True)

# ======= PSG Vendor Recommendations (simple static) =======
@st.cache_data(ttl=3600)
def fetch_psg_vendors():
    return {
        "Retail": ["Vend POS", "StoreHub", "Qashier"],
        "F&B": ["FoodZaps", "Oddle", "TabSquare"],
        "Tech": ["Microsoft 365", "Xero", "Freshworks"],
        "Others": ["Generic Vendor A", "Generic Vendor B"]
    }

# ======= Main app rendering =======
st.divider()
st.subheader("PSG Vendor Recommendations")
psg_vendors = fetch_psg_vendors()
if sector in psg_vendors:
    for vendor in psg_vendors[sector]:
        st.markdown(f"- {vendor}")
else:
    st.markdown("No sector-specific vendors found.")

st.divider()
st.subheader("Matching Grants For You")

user_profile = {
    "sector": sector,
    "revenue": revenue,
    "headcount": headcount,
    "intent": intent,
}

live_grants = fetch_live_grants()
scored_grants = filter_and_score_grants(live_grants, user_profile)

if not scored_grants:
    st.info("No matching grants found based on your profile and GPT eligibility scoring.")
else:
    for grant in scored_grants:
        st.markdown(f"""
            <div style='border:1px solid #2b3a5e; padding:1rem; border-radius:10px; margin-bottom:1rem;'>
                <h4 style='margin-bottom:0.2rem;'>{grant['name']} ({grant['match_score']}%)</h4>
                <p style='margin:0.3rem 0;'>{grant['desc']}</p>
                <p><b>Focus:</b> {grant['type']}</p>
                <p><b>GPT Eligibility Justification:</b> {grant['justification']}</p>
                <a href="{grant['url']}" target="_blank">🔗 View Details</a>
            </div>
        """, unsafe_allow_html=True)

# ======= Bonus: Discover govt datasets =======
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

with st.expander("Discover Government Grant Datasets"):
    datasets = discover_datasets()
    if datasets:
        for title, link in datasets:
            st.markdown(f"- [{title}]({link})")
    else:
        st.write("No datasets available or API error.")

# ======= Quick Links Section =======
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
