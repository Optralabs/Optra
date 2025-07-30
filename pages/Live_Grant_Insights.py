import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from typing import List, Tuple, Dict
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from utils.grant_database import get_all_grants

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

# ========== Grant Scoring ==========
def score_grant_match(grant, sector, revenue, staff_count, goal):
    score = 0
    reasons = []

    # Sector check
    if grant['sectors']:
        if sector and sector.lower() in [s.lower() for s in grant['sectors']]:
            score += 25
            reasons.append("✔️ Sector is eligible.")
        else:
            reasons.append("❌ Sector mismatch.")
    else:
        # No sector restriction = partial credit
        score += 10
        reasons.append("ℹ️ No sector restriction.")

    # Revenue check
    max_revenue = grant.get('max_revenue')
    if max_revenue is not None:
        if revenue <= max_revenue:
            score += 25
            reasons.append(f"✔️ Revenue ≤ ${max_revenue:,}.")
        else:
            reasons.append(f"❌ Revenue > ${max_revenue:,}.")
    else:
        score += 10
        reasons.append("ℹ️ No revenue cap.")

    # Staff check
    max_staff = grant.get('max_staff')
    if max_staff is not None:
        if staff_count <= max_staff:
            score += 25
            reasons.append(f"✔️ Staff count ≤ {max_staff}.")
        else:
            reasons.append(f"❌ Staff count > {max_staff}.")
    else:
        score += 10
        reasons.append("ℹ️ No staff cap.")

    # Business goal check
    if goal:
        if goal.lower() in [g.lower() for g in grant['supported_goals']]:
            score += 25
            reasons.append("✔️ Business goal aligns.")
        else:
            reasons.append("❌ Business goal does not align.")
    else:
        reasons.append("ℹ️ No business goal specified.")

    return min(score, 100), reasons

# ========== PDF Report Generator ==========
def generate_pdf(sector, revenue, staff_count, goal, matches):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    pdf.setTitle("Grant Match Report")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Grant Match Report")
    y -= 40

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Business Sector: {sector}")
    y -= 20
    pdf.drawString(50, y, f"Annual Revenue: SGD {revenue:,.2f}")
    y -= 20
    pdf.drawString(50, y, f"Staff Count: {staff_count}")
    y -= 20
    pdf.drawString(50, y, f"Business Goal: {goal}")
    y -= 30

    for match in matches:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"{match['Grant']} — {match['Score']}% Match")
        y -= 25

        pdf.setFont("Helvetica", 11)
        for reason in match['Reasons'].split("\n"):
            pdf.drawString(60, y, f"- {reason.strip()}")
            y -= 15

            if y < 60:
                pdf.showPage()
                y = height - 50

        y -= 20

    pdf.save()
    buffer.seek(0)
    return buffer

# ========== Streamlit UI ==========
st.title("📊 Live Grant Insights")
st.markdown("Get real-time insights into which grants best match your business profile.")

with st.form("sme_form"):
    st.subheader("Your SME Details")
    sector = st.text_input("Sector (e.g., retail, f&b, logistics)").strip()
    revenue = st.number_input("Annual Revenue (SGD)", min_value=0, step=10000)
    staff_count = st.number_input("Full-Time Staff Count", min_value=0, step=1)
    goal = st.text_input("Business Goal (e.g., automation, expansion)").strip()
    submitted = st.form_submit_button("Analyze Grants")

if submitted:
    st.markdown("---")
    st.subheader("🎯 Matching Grants")
    grants = get_all_grants()
    matches = []

    for grant in grants:
        score, reasons = score_grant_match(grant, sector, revenue, staff_count, goal)
        clamped_score = max(0, min(100, int(score)))

        with stylable_container(key=grant['name'], css_styles="border:1px solid #ccc; padding:1em; border-radius:10px; margin-bottom:1em;"):
            st.markdown(f"### [{grant['name']}]({grant['link']})")
            st.markdown(f"*Type:* {grant['type']}")
            components.html(f"""
                <div style='background:#0B0E28; border-radius:10px; padding:5px;'>
                    <div style='width:{clamped_score}%; background:#2F49F4; height:20px; border-radius:7px;'></div>
                </div>
                <p style='color:#F5F5F5; font-size:16px; margin-top:6px;'>Eligibility Score: {clamped_score}%</p>
            """, height=60)
            st.markdown("**Rationale:**")
            for reason in reasons:
                st.markdown(f"- {reason}")
            matches.append({
                "Grant": grant["name"],
                "Score": clamped_score,
                "Reasons": "\n".join(reasons),
                "Link": grant["link"]
            })

    # PDF Download
    if matches:
        st.markdown("#### 📄 Downloadable PDF Report")
        if st.button("Generate PDF Report"):
            pdf_file = generate_pdf(sector, revenue, staff_count, goal, matches)
            st.download_button("📥 Download Report", data=pdf_file, file_name="Grant_Report.pdf", mime="application/pdf")

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
