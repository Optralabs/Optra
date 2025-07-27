import streamlit as st
import openai
import os
import requests
import datetime
import re
from fpdf import FPDF
import pdfplumber
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ----------------------------
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

st.set_page_config(page_title="Smart Grant Advisor", layout="wide")
# Set page config

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


st.set_page_config(page_title="Smart Grant Advisor", layout="wide")

st.title("Smart Grant Advisor")
st.markdown("""
Welcome to **Smart Grant Advisor** — your AI-powered tool to help Singapore SMEs navigate complex government grants.

Use the sidebar to:
-  Access the **Grant Eligibility Checker**
-  Upload and review documents with the **Document Checker**

---
""")

st.info("Start by selecting a tool from the sidebar on the left.")


auto_data = {}

# === Load API Key from Streamlit secrets ===
import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

# === Helper: Extract text from PDF ===
def extract_text_from_pdf(file) -> str:
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# === Helper: Extract UEN and Industry ===
def extract_data_from_text(text):
    data = {}
    uen_match = re.search(r'\b\d{8}[A-Z]\b', text)
    if uen_match:
        data['uen'] = uen_match.group(0)
    text_lower = text.lower()
    if 'retail' in text_lower:
        data['industry'] = 'Retail'
    elif 'education' in text_lower:
        data['industry'] = 'Education'
    elif 'food and beverage' in text_lower or 'f&b' in text_lower:
        data['industry'] = 'F&B'
    return data

# === Eligibility Checks ===
def check_psg_eligibility(industry, revenue, employees, years, ownership, goal):
    reasons_ineligible = []
    eligible = True
    if ownership.lower() != "yes":
        eligible = False
        reasons_ineligible.append("Requires at least 30% local ownership.")
    try:
        revenue_val = float(str(revenue).replace(',', '').strip())
    except:
        revenue_val = 0
    try:
        employees_val = int(str(employees))
    except:
        employees_val = 0
    if revenue_val >= 100_000_000 and employees_val > 200:
        eligible = False
        reasons_ineligible.append("Annual revenue must be less than S$100 million OR have 200 or fewer employees.")
    psg_keywords = ['digital', 'equipment', 'automation', 'productivity', 'software', 'technology', 'digitalise', 'digitize']
    if not any(k in goal.lower() for k in psg_keywords):
        eligible = False
        reasons_ineligible.append("Grant focuses on digitalisation or equipment solutions.")
    try:
        years_val = float(years)
        if years_val <= 0:
            eligible = False
            reasons_ineligible.append("Business should be operational (years > 0).")
    except:
        eligible = False
        reasons_ineligible.append("Invalid input for years in operation.")
    return eligible, reasons_ineligible

def check_edg_eligibility(industry, revenue, employees, years, ownership, goal):
    reasons_ineligible = []
    eligible = True
    if ownership.lower() != "yes":
        eligible = False
        reasons_ineligible.append("Requires at least 30% local ownership.")
    try:
        years_val = float(years)
        if years_val < 2:
            eligible = False
            reasons_ineligible.append("Requires at least 2 years in operation.")
    except:
        eligible = False
        reasons_ineligible.append("Invalid input for years in operation.")
    try:
        revenue_val = float(str(revenue).replace(',', '').strip())
        if revenue_val <= 0:
            eligible = False
            reasons_ineligible.append("Business should be financially viable with revenue > 0.")
    except:
        eligible = False
        reasons_ineligible.append("Invalid input for annual revenue.")
    edg_keywords = ['growth', 'expand', 'expansion', 'overseas', 'innovation', 'innovate', 'develop', 'research', 'upgrade']
    if not any(k in goal.lower() for k in edg_keywords):
        eligible = False
        reasons_ineligible.append("Grant targets growth, overseas expansion, or innovation goals.")
    return eligible, reasons_ineligible

def check_sfec_eligibility(skills_levy_paid, local_employees, violations):
    reasons_ineligible = []
    eligible = True
    try:
        skills_levy_val = float(skills_levy_paid)
        if skills_levy_val < 750:
            eligible = False
            reasons_ineligible.append("Skills Development Levy paid must be at least S$750 in the past year.")
    except:
        eligible = False
        reasons_ineligible.append("Invalid input for Skills Development Levy paid.")
    try:
        local_employees_val = int(local_employees)
        if local_employees_val < 3:
            eligible = False
            reasons_ineligible.append("Must have employed at least 3 local employees in the past year.")
    except:
        eligible = False
        reasons_ineligible.append("Invalid input for number of local employees.")
    if violations:
        eligible = False
        reasons_ineligible.append("Must have no outstanding MOM or IRAS violations.")
    return eligible, reasons_ineligible

# === PDF Export Function ===
from fpdf import FPDF
from io import BytesIO

def generate_pdf(text):
    class PDF(FPDF):
        def header(self):
            self.set_draw_color(180, 180, 180)
            self.rect(10, 10, 190, 277)  # border
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "Grant Eligibility Report", ln=True, align="C")
            self.ln(10)

        def section_title(self, title):
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(0)
            self.cell(0, 10, title, ln=True)
            self.set_text_color(0)

        def section_body(self, body, size=11):
            self.set_font("Helvetica", "", size)
            self.multi_cell(0, 7, body)
            self.ln()

        def checklist(self, items):
            self.set_font("Helvetica", "", 11)
            for item in items:
                self.cell(5)
                self.cell(0, 7, f"- {item}", ln=True)
            self.ln()

    # Sanitize input: replace problematic punctuation with safe equivalents
    text = text.replace("—", "-").replace("–", "-").replace("•", "-")
    text = text.replace("✓", "").replace("✔", "").replace("✅", "")
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')

    # Remove remaining non-latin characters
    clean_text = text.encode("ascii", "ignore").decode("ascii")

    # Identify and extract sections
    sections = {
        "Eligible Grants": "",
        "Justification": "",
        "Documents to Prepare": "",
        "Not Eligible For": "",
        "Other Grants You Can Explore": ""
    }

    current = None
    for line in clean_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "Eligible Grants" in line:
            current = "Eligible Grants"
            continue
        elif "Justification" in line:
            current = "Justification"
            continue
        elif "Documents to Prepare" in line:
            current = "Documents to Prepare"
            continue
        elif "Not Eligible For" in line:
            current = "Not Eligible For"
            continue
        elif "Other Grants You Can Explore" in line:
            current = "Other Grants You Can Explore"
            continue
        if current:
            sections[current] += line + "\n"

    # Initialize PDF
    pdf = PDF()
    pdf.add_page()

    if sections["Eligible Grants"]:
        pdf.section_title("Eligible Grants")
        pdf.section_body(sections["Eligible Grants"])

    if sections["Justification"]:
        pdf.section_title("Justification")
        pdf.section_body(sections["Justification"], size=11)

    if sections["Documents to Prepare"]:
        checklist_items = [item.strip("- ") for item in sections["Documents to Prepare"].splitlines() if item.strip()]
        pdf.section_title("Checklist of Documents")
        pdf.checklist(checklist_items)

    if sections["Not Eligible For"]:
        pdf.section_title("Grants Not Eligible For")
        pdf.section_body(sections["Not Eligible For"], size=11)

    if sections["Other Grants You Can Explore"]:
        pdf.section_title("Other Grants You Can Explore")
        pdf.section_body(sections["Other Grants You Can Explore"], size=11)

    # Add Tips section manually
    pdf.section_title("Recommendations & Tips")
    pdf.section_body("""- Consider working with pre-approved vendors to expedite PSG applications.
- Ensure your ACRA BizFile is updated and reflects your operational activities.
- For EDG eligibility in future, invest in capability-building or product innovation.
- To qualify for SFEC, ensure timely CPF contributions and meet local hiring thresholds.
- Keep records of past training, digitalisation, and transformation projects - they can support future claims.""", size=10)

    # Final output to buffer
    buffer = BytesIO()
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer

# === Scrape PSG Solutions ===
@st.cache_data(ttl=3600)
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

# === Scrape EDG Headlines ===
@st.cache_data(ttl=3600)
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

# === Form Fields ===
st.markdown("### About Your Business")
industry = st.text_input("Industry / Sector", value=auto_data.get("industry") or "")
revenue = st.text_input("Annual Revenue (SGD)")
employees = st.text_input("No. of Employees")
years = st.text_input("Years in Operation")
ownership = st.selectbox("Is Local Ownership ≥30%?", ["Yes", "No"], index=0)
goal = st.text_input("What do you want to achieve with a grant?")

# === Optional Document Upload ===
st.markdown("### Upload Supporting Business Document (Optional)")
st.markdown("_We’ll analyze your uploaded document to tailor grant recommendations._")
uploaded_file = st.file_uploader("Upload a PDF document (e.g. ACRA BizFile)", type=["pdf"])

doc_summary = ""
auto_data = {}

if uploaded_file:
    try:
        all_text = extract_text_from_pdf(uploaded_file)
        doc_summary = all_text[:2000]
        auto_data = extract_data_from_text(all_text)
        st.success("✅ Document uploaded and analyzed.")
        st.text_area("Extracted Content (preview)", doc_summary, height=180)
    except Exception as e:
        st.warning(f"Could not read PDF: {e}")

st.markdown("---")

# === SFEC Inputs ===
st.markdown("### SFEC Specific Details")
skills_levy_paid = st.text_input("Skills Development Levy Paid Last Year (S$)")
local_employees = st.text_input("Number of Local Employees")
violations = st.checkbox("Any outstanding MOM or IRAS violations?", value=False)

if st.button("Check Eligibility"):
    try:
        revenue_val = float(re.sub(r"[^\d.]", "", revenue))
        employees_val = int(employees)
        years_val = float(years)
        skills_levy_val = float(skills_levy_paid) if skills_levy_paid else 0
        local_employees_val = int(local_employees) if local_employees else 0
    except Exception:
        st.error("Please enter valid numbers for Revenue, Employees, Years, Skills Levy, and Local Employees.")
        st.stop()

    ownership_val = ownership.lower()
    violations_val = violations

    # Check eligibility
    psg_ok, psg_why = check_psg_eligibility(industry, revenue_val, employees_val, years_val, ownership_val, goal)
    edg_ok, edg_why = check_edg_eligibility(industry, revenue_val, employees_val, years_val, ownership_val, goal)
    sfec_ok, sfec_why = check_sfec_eligibility(skills_levy_val, local_employees_val, violations_val)

    eligible = []
    not_eligible = []
    if psg_ok: eligible.append("PSG")
    else: not_eligible.append("PSG: " + ", ".join(psg_why))
    if edg_ok: eligible.append("EDG")
    else: not_eligible.append("EDG: " + ", ".join(edg_why))
    if sfec_ok: eligible.append("SFEC")
    else: not_eligible.append("SFEC: " + ", ".join(sfec_why))

    prompt_parts = [
        "You are a Smart Grant Advisor for Singapore SMEs.",
        "",
        "Business Profile:",
        f"- Industry: {industry}",
        f"- Revenue: {revenue}",
        f"- Employees: {employees}",
        f"- Years in Operation: {years}",
        f"- Local Ownership ≥30%?: {ownership}",
        f"- Business Goal: {goal}"
    ]
    if auto_data.get("uen"):
        prompt_parts.append(f"- UEN: {auto_data['uen']}")
    if doc_summary:
        prompt_parts.append(f"Supporting Document Extract:\n{doc_summary}")
    prompt_parts.append("")
    prompt_parts.append("Your task:")
    prompt_parts.append("1. List eligible grants.")
    prompt_parts.append("2. Explain ineligibility where applicable.")
    prompt_parts.append("3. Suggest how to qualify in the future.")
    prompt_parts.append("4. Provide checklist of documents to prepare.")
    prompt = "\n".join(prompt_parts)
    
use_dummy = False  # make sure this is defined above

# Start response logic
if use_dummy:
    response_text = """
### ✅ Eligible Grants
- Productivity Solutions Grant (PSG)

### 💬 Justification
Your SME is aligned with digitalisation goals and has the necessary ownership and size to qualify for PSG.

### 📂 Documents to Prepare
- Latest ACRA BizFile
- Financial Statements
- Vendor quotation (for PSG)
- Proof of local employees

### ❗ Not Eligible For
- **EDG**: Requires ≥2 years in operation and growth/innovation goals.
- **SFEC**: Must meet S$750 levy + ≥3 local staff + no violations.
"""
else:
    with st.spinner("Analyzing via OpenAI..."):
        try:
            res = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Smart Grant Advisor for Singapore SMEs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6
            )
            response_text = res.choices[0].message.content
        except Exception as e:
            st.error(f"API error: {e}")
                st.stop()

    st.success("✅ Results Ready")
    st.markdown(response_text)
    st.markdown("### 📋 Copy or Export Results")
    st.text_area("Output Preview", value=response_text, height=300)
    st.download_button("📄 Download as Text", response_text, file_name="grant_recommendation.txt")
    st.download_button("📄 Download as PDF", generate_pdf(response_text), file_name="grant_recommendation.pdf")

st.markdown("---")

# === Main App UI ===
st.set_page_config(page_title="Smart Grant Advisor", layout="wide")

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

# === Tips & Recommendations Section ===
st.header("Tips & Recommendations for Grant Success")
st.markdown("""
Here are some practical tips to improve your chances of securing government grants in Singapore:
""")

tips = [
    "- Use **pre-approved PSG vendors** to speed up your application process.",
    "- Make sure your **ACRA BizFile** is updated within the last 3 months.",
    "- Include a **clear project justification** showing how the solution improves productivity or supports expansion.",
    "- For EDG, demonstrate **capability-building** or **market expansion** plans.",
    "- To qualify for SFEC, ensure you’ve **met CPF and local hiring criteria**, and have no MOM/IRAS violations.",
    "- Prepare **financial statements**, employee records, and vendor quotes in advance.",
    "- Explore **co-funding opportunities** by combining eligible grants (e.g., PSG + SFEC)."
]

for tip in tips:
    st.markdown(f"- {tip}")

st.markdown("---")

# === Grant Listings Section ===
st.header("Live PSG, EDG and SFEC Information")
st.markdown("---")

st.markdown("### Productivity Solutions Grant (PSG)")
psg_data, psg_status, psg_time = fetch_psg_solutions()
st.markdown("Supports adoption of pre-approved IT tools and equipment for productivity.")
st.markdown(f"**Last updated:** {psg_time.strftime('%Y-%m-%d %H:%M')} — {psg_status}")
for title, desc in psg_data:
    st.markdown(f"- **{title}**\n  {desc}")
st.markdown("*Useful Links:*")
st.markdown("""
- [PSG Overview](https://www.gobusiness.gov.sg/productivity-solutions-grant/)
- [Browse Solutions](https://www.gobusiness.gov.sg/productivity-solutions-grant/solutions/)
- [Eligibility](https://www.gobusiness.gov.sg/grants/psg/eligibility/)
- [How to Apply](https://www.gobusiness.gov.sg/productivity-solutions-grant/apply/)
""")

st.markdown("### Enterprise Development Grant (EDG)")
st.markdown("EDG supports larger-scale projects for innovation, capability building, and market expansion.")
edg_data, edg_status, edg_time = fetch_edg_headlines()
st.markdown(f"**Last updated:** {edg_time.strftime('%Y-%m-%d %H:%M')} — {edg_status}")
for header, _ in edg_data:
    st.markdown(f"- {header}")
st.markdown("*Useful Links:*")
st.markdown("""
- [EDG Overview](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant/overview)
- [Eligibility](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant/eligibility)
- [Project Types](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant/project-categories)
- [How to Apply](https://www.enterprisesg.gov.sg/financial-assistance/grants/for-local-companies/enterprise-development-grant/how-to-apply)
""")

st.markdown("### SkillsFuture Enterprise Credit (SFEC)")
st.markdown("SFEC provides $10,000 credits to eligible employers undertaking workforce or business transformation efforts.")
st.markdown("*Useful Links:*")
st.markdown("""
- [SFEC Info](https://www.skillsfuture.gov.sg/sfec)
- [Eligibility](https://www.skillsfuture.gov.sg/sfec/eligibility)
- [How to Use](https://www.skillsfuture.gov.sg/sfec/how-to-apply)
""")

st.markdown("---")

# === FAQ Section ===
st.subheader("Ask a Question")
faq = st.text_area("Enter a question about Singapore SME grants, criteria, or your uploaded documents.")
if faq:
    with st.expander("📖 Ask a grant question"):
        try:
            res = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful and precise grant advisor for Singaporean SMEs."
                    },
                    {
                        "role": "user",
                        "content": faq
                    }
                ]
            )
            st.markdown(res.choices[0].message.content)
        except openai.error.OpenAIError as e:
            st.error(f"API error: {e}")

st.markdown("---")

# === Feedback Section ===
st.subheader("Feedback")
with st.form("feedback_form"):
    feedback = st.text_area("Your feedback")
    if st.form_submit_button("Submit"):
        st.success("Thank you for your feedback!")

# === Footer ===
st.markdown("---")
st.caption("""
This assistant helps Singapore SMEs explore grant eligibility and guidance.
Not affiliated with GoBusiness or EnterpriseSG. Always confirm details at:
https://www.gobusiness.gov.sg or https://www.enterprisesg.gov.sg
""")


