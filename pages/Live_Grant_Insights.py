import streamlit as st
import requests
import datetime
from bs4 import BeautifulSoup

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


