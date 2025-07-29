import streamlit as st
import requests
import datetime
from bs4 import BeautifulSoup

# Load and embed OPTRA logo
# ----------------------------
from PIL import Image
import base64
from io import BytesIO

def get_logo_base64(path, width=80):
    img = Image.open(path)
    img = img.resize((width, width), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Set your logo path
logo_base64 = get_logo_base64("optra_logo_transparent.png")

# Display logo and brand (only once)
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

st.title("Live Grant Insights")

# Inject global custom CSS for LanX-style gradient + form elements
st.markdown("""
    <style>
        /* Full-page gradient background */
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(to bottom, #0a0a0a 0%, #0a0a0a 10%, #0d0f1c 30%, #0f111f 60%, #00011d 100%) !important;
            color: #ffffff;
        }

        /* Remove extra white backgrounds in containers */
        .block-container {
            background-color: rgba(0, 0, 0, 0) !important;
        }

        /* Text input, selectbox, textarea styling */
        input, textarea, select {
            background-color: #111729 !important;
            color: #ffffff !important;
            border: 1px solid #2b3a5e !important;
        }

        /* Placeholder text color */
        ::placeholder {
            color: #888 !important;
        }

        /* Button style */
        button[kind="primary"] {
            background-color: #3e6ce2 !important;
            color: white !important;
            border-radius: 8px !important;
        }

        /* Optional: shadow box for main headings */
        h1, h2, h3 {
            text-shadow: 0 0 4px rgba(0,0,0,0.4);
        }
    </style>
""", unsafe_allow_html=True)

# 1. Fetch PSG Vendors (Simulated with fallback)
def fetch_psg_vendors() -> Tuple[List[Tuple[str, str]], str]:
    url = "https://data.gov.sg/api/action/datastore_search"
    params = {
        "resource_id": "cfba37cc-fb01-42e1-bbf6-0aadeec6f0bd",  # Placeholder resource ID
        "limit": 5
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        records = res.json()["result"]["records"]
        return [(rec["vendor_name"], rec.get("solution_name", "No description")) for rec in records], " PSG data fetched via API"
    except Exception as e:
        return [("Fallback Vendor", "Unable to fetch live data.")], f" Error fetching PSG data: {e}"

# 2. Mock other grant data (can later be linked to scrapers or APIs)
def get_mock_grant_data():
    return {
        "Enterprise Development Grant (EDG)": [
            ("EDG Business Strategy", "Support for upgrading business strategies, innovation, productivity."),
            ("EDG Market Access", "Helps expand overseas with expert consultancy and support.")
        ],
        "Startup SG Founder": [
            ("Start-up Capital Grant", "Provides mentorship and startup capital to first-time founders."),
        ],
        "SkillsFuture Enterprise Credit (SFEC)": [
            ("SFEC Training Subsidy", "Subsidies for employer-sponsored workforce upgrading."),
        ],
        "Market Readiness Assistance (MRA)": [
            ("MRA Overseas Expansion", "Support for international market expansion activities.")
        ]
    }

# 3. Optional Grant Dataset Discovery
@st.cache_data
def search_datasets(query="grant"):
    url = "https://data.gov.sg/api/action/package_search"
    try:
        params = {"q": query}
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()["result"]["results"]
        return [(d["title"], d["resources"][0]["url"]) for d in data[:5]]
    except:
        return []

# Streamlit App UI
st.set_page_config(page_title="Live Grant Insights", layout="wide")
st.title("Live Grant Insights for Singapore SMEs")
st.markdown("Gain real-time access to SME grants across productivity, innovation, hiring and expansion.")

# 1. PSG Vendors Section
st.subheader("Productivity Solutions Grant (PSG)")
psg_data, psg_status = fetch_psg_vendors()
st.caption(psg_status)
for vendor, desc in psg_data:
    st.markdown(f"- **{vendor}**: {desc}")

# 2. Other Grants Section
grants_data = get_mock_grant_data()
for grant_type, items in grants_data.items():
    st.subheader(f" {grant_type}")
    for name, desc in items:
        st.markdown(f"- **{name}**<br>{desc}", unsafe_allow_html=True)

# 3. Dataset Discovery Section
with st.expander(" Discover More Grant Datasets (via data.gov.sg)"):
    dataset_results = search_datasets()
    if dataset_results:
        for title, link in dataset_results:
            st.markdown(f"- [{title}]({link})")
    else:
        st.write("No datasets found or API error.")

# 4. Quick Links Section
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



