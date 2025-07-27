import streamlit as st
import requests
import datetime
from bs4 import BeautifulSoup

# Load and embed OPTRA logo
# ----------------------------
from PIL import Image
import base64
from io import BytesIO
import streamlit as st

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

st.title("Live Grant Scraper")

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


# Cache with TTL removed, because we want manual control now

def fetch_psg_solutions():
    fallback = [("eCommerce Solutions", "Tools for online selling."),
                ("Cybersecurity Tools", "Packages for small biz protection."),
                ("Accounting Systems", "Automate invoicing and expenses.")]
    try:
        url = "https://www.gobusiness.gov.sg/productivity-solutions-grant/solutions/"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if res.status_code != 200:
            return fallback, "Fallback (bad response)", datetime.datetime.now()
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".solution-card")
        data = [(c.select_one(".solution-name").text.strip(), c.select_one(".solution-description").text.strip()) for c in cards[:5]]
        return data or fallback, "Live scrape successful", datetime.datetime.now()
    except:
        return fallback, "Fallback (error)", datetime.datetime.now()

def fetch_edg_headlines():
    fallback = [("Strategic Brand & Marketing Development", ""), ("Overseas Expansion Planning", "")]
    try:
        url = "https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant/overview"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if res.status_code != 200:
            return fallback, "Fallback (bad response)", datetime.datetime.now()
        soup = BeautifulSoup(res.text, "html.parser")
        headers = soup.select("h2, h3")
        results = [(h.text.strip(), "") for h in headers if len(h.text.strip()) > 4]
        return results[:5], "Live scrape successful", datetime.datetime.now()
    except:
        return fallback, "Fallback (error)", datetime.datetime.now()

if "psg_data" not in st.session_state:
    st.session_state.psg_data = None
if "psg_status" not in st.session_state:
    st.session_state.psg_status = None
if "psg_time" not in st.session_state:
    st.session_state.psg_time = None

if "edg_data" not in st.session_state:
    st.session_state.edg_data = None
if "edg_status" not in st.session_state:
    st.session_state.edg_status = None
if "edg_time" not in st.session_state:
    st.session_state.edg_time = None

if st.button("Run Grant Scraper"):
    with st.spinner("Scraping PSG Solutions..."):
        psg_data, psg_status, psg_time = fetch_psg_solutions()
        st.session_state.psg_data = psg_data
        st.session_state.psg_status = psg_status
        st.session_state.psg_time = psg_time

    with st.spinner("Scraping EDG Headlines..."):
        edg_data, edg_status, edg_time = fetch_edg_headlines()
        st.session_state.edg_data = edg_data
        st.session_state.edg_status = edg_status
        st.session_state.edg_time = edg_time

if st.session_state.psg_data:
    st.header("Productivity Solutions Grant (PSG)")
    st.markdown(f"**Last updated:** {st.session_state.psg_time.strftime('%Y-%m-%d %H:%M')} — {st.session_state.psg_status}")
    for title, desc in st.session_state.psg_data:
        st.markdown(f"- **{title}**\n  {desc}")

if st.session_state.edg_data:
    st.header("Enterprise Development Grant (EDG)")
    st.markdown(f"**Last updated:** {st.session_state.edg_time.strftime('%Y-%m-%d %H:%M')} — {st.session_state.edg_status}")
    for title, desc in st.session_state.edg_data:
        st.markdown(f"- **{title}**\n  {desc}")

if not (st.session_state.psg_data or st.session_state.edg_data):
    st.info("Click the button above to start scraping live grant data.")


