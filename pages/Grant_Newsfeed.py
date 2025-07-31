import streamlit as st
import feedparser
import re
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime
import urllib.parse

# Set page config once at the very top
st.set_page_config(
    page_title="Smart Grant Advisor",
    page_icon="favicon.ico",  # You can keep your favicon file name here
    layout="wide"
)

# ----------------------------
# Load and embed OPTRA logo with fix
# ----------------------------
def get_logo_base64(path, width=80):
    img = Image.open(path)
    # Preserve aspect ratio on resize
    w_percent = (width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((width, h_size), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

logo_base64 = get_logo_base64("optra_logo_transparent.png")

st.markdown(
    f"""
    <div class='logo-container' style='display: flex; align-items: flex-start; margin-bottom: 2rem; margin-top: 4.5rem;'>
        <img src='data:image/png;base64,{logo_base64}' width='80' style='margin-right: 15px; max-height: 80px; display: block;' />
        <div>
            <h1 style='margin: 0; font-size: 1.8rem;'>OPTRA</h1>
        </div>
    </div>
    <style>
      .logo-container {{
        overflow: visible !important;
      }}
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Styling
# ----------------------------
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(to bottom, #0a0a0a, #0f111f 60%, #00011d);
            color: #ffffff;
        }
        .block-container {
            padding-top: 0 !important;
        }
        h1, h2, h3 {
            text-shadow: 0 0 4px rgba(0,0,0,0.4);
        }
        a {
            color: #4da6ff;
        }
        img {
            display: block;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# Title & Description
# ----------------------------
st.title("Grant Newsfeed")
st.markdown("Catch the latest news, insights, and essential information about government grants for Singapore SMEs.")
st.markdown("---")

# ----------------------------
# News Scraper
# ----------------------------
def fetch_news_headlines(grant_name, max_articles=3):
    query = urllib.parse.quote(grant_name + " Singapore")
    rss_url = f"https://www.bing.com/news/search?q={query}&format=RSS"
    feed = feedparser.parse(rss_url)

    headlines = []
    for entry in feed.entries:
        link = entry.link
        domain_match = re.search(r"https?://(?:www\.)?([^/]+)", link)
        domain = domain_match.group(1).lower() if domain_match else "source unknown"

        published = entry.get("published_parsed")
        if published:
            date_str = datetime(*published[:6]).strftime("%d %b %Y")
        else:
            date_str = "Date unknown"

        headlines.append(f"- [{entry.title}]({link})  \n<small>Source: {domain} | Date: {date_str}</small>")
        if len(headlines) >= max_articles:
            break

    return headlines if headlines else ["- No recent news articles available from public sources."]

# ----------------------------
# Grant Definitions
# ----------------------------
grants = [
    {
        "name": "Productivity Solutions Grant (PSG)",
        "summary": [
            "- Supports SMEs adopting IT solutions and automation to improve productivity.",
            "- Covers pre-scoped equipment and vendor services with up to 50% funding."
        ],
        "eligibility": [
            "- Business registered and operating in Singapore.",
            "- Must have at least 30% local shareholding.",
            "- Purchase/subscription must be used locally."
        ],
        "links": [
            "- [PSG Overview](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/productivity-solutions-grant)",
            "- [Apply via Business Grants Portal](https://www.businessgrants.gov.sg)"
        ]
    },
    {
        "name": "Enterprise Development Grant (EDG)",
        "summary": [
            "- Helps SMEs grow and transform via capability building, innovation, and market access projects.",
            "- Provides up to 50% funding support for consultancy, training, software, and equipment."
        ],
        "eligibility": [
            "- Registered and operating in Singapore.",
            "- Minimum 30% local shareholding.",
            "- Ready to start and complete the project."
        ],
        "links": [
            "- [EDG Overview](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant)",
            "- [Apply via Business Grants Portal](https://www.businessgrants.gov.sg)"
        ]
    },
    {
        "name": "SkillsFuture Enterprise Credit (SFEC)",
        "summary": [
            "- Offers an additional S$10,000 credit to support workforce upgrading and enterprise transformation.",
            "- Credit automatically applies to eligible schemes like PSG and SFW."
        ],
        "eligibility": [
            "- Must have contributed at least $750 to SDL in a year.",
            "- Minimum 3 Singapore Citizens/PRs employed for 12 months."
        ],
        "links": [
            "- [SFEC Overview](https://www.enterprisejobskills.gov.sg/content/upgrade-skills/sfec.html)"
        ]
    },
    {
        "name": "Market Readiness Assistance (MRA)",
        "summary": [
            "- Supports international expansion activities such as market promotion, set-up, and business development.",
            "- Up to 50% support capped at S$100,000 per new market."
        ],
        "eligibility": [
            "- Business must be Singapore-registered and operating locally.",
            "- New to the market (no previous setup)."
        ],
        "links": [
            "- [MRA Overview](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/market-readiness-assistance-grant)"
        ]
    },
    {
        "name": "Startup SG Founder",
        "summary": [
            "- Supports first-time entrepreneurs with mentorship and startup capital.",
            "- Co-matching grant of up to S$50,000 available through accredited mentor partners."
        ],
        "eligibility": [
            "- First-time founder with minimum 30% equity.",
            "- Singapore Citizen or Permanent Resident."
        ],
        "links": [
            "- [Startup SG Founder Details](https://www.startupsg.gov.sg/programmes/4892/startup-sg-founder)"
        ]
    },
    {
        "name": "Energy Efficiency Grant (EEG)",
        "summary": [
            "- Helps SMEs in specific sectors improve energy efficiency via equipment upgrades.",
            "- Up to 70% support for qualifying equipment purchases."
        ],
        "eligibility": [
            "- SME in Food Services, Manufacturing, or Retail sector.",
            "- Registered and operating in Singapore."
        ],
        "links": [
            "- [EEG Overview](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/energy-efficiency-grant)"
        ]
    }
]

# ----------------------------
# Display Each Grant Section
# ----------------------------
for grant in grants:
    st.header(grant["name"])

    st.subheader("Latest News")
    for headline in fetch_news_headlines(grant["name"]):
        st.markdown(headline, unsafe_allow_html=True)

    st.subheader("What’s This Grant About?")
    for point in grant["summary"]:
        st.markdown(point)

    st.subheader("Who’s Eligible?")
    for item in grant["eligibility"]:
        st.markdown(item)

    st.subheader("Application Links")
    for link in grant["links"]:
        st.markdown(link)

    st.markdown("---")
