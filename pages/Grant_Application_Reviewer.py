# === Imports & Setup ===
import streamlit as st
import pdfplumber
import re
import tempfile
from io import BytesIO
from fpdf import FPDF
from PIL import Image
import pytesseract
import fitz
import base64

from access_control import page_lock

page_lock ("Grant Application Reviewer")

# === App Config ===
st.set_page_config(
    page_title="Grant Document Checker",
    page_icon="optra_logo_transparent.png",
    layout="wide"
)

# === Dark Theme Styling ===
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {background-color: #000 !important;}
        section[data-testid="stSidebar"] * {color: #fff !important;}
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(to bottom, #0a0a0a, #0d0f1c, #0f111f, #00011d) !important;
            color: #fff;
        }
        h1, h2, h3 {text-shadow: 0 0 4px rgba(0,0,0,0.4);}
    </style>
""", unsafe_allow_html=True)

# === Logo Display ===
def get_logo_banner(path="optra_logo_transparent.png", width=80):
    img = Image.open(path)
    img = img.resize((width, width), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

logo_banner = get_logo_banner()
st.markdown(f"""
    <div style='display:flex;align-items:center;margin-bottom:0.5rem;'>
        <img src='data:image/png;base64,{logo_banner}' width='80' style='margin-right:15px;'/>
        <div><h1 style='margin:0;font-size:1.8rem;'>OPTRA</h1></div>
    </div>
""", unsafe_allow_html=True)

# === Page Title & Short Description ===
st.title("Grant Application Reviewer")
st.markdown("""
**Analyse your grant application with consultant‑level insights:**
- Detect missing or weak sections instantly.
- Check eligibility for PSG, EDG, SFEC grants.
- Receive tailored recommendations for approval success.
- Download a professional, board‑ready PDF report.
""")

# === Text Cleaning Utilities ===
def clean_text(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def safe_pdf_text(text):
    return clean_text(text).encode("latin-1", "replace").decode("latin-1")

def format_list_item(item):
    cleaned_item = re.sub(r"^[•\-\–\—○]+\s*", "", item.strip())
    if re.match(r"^\d+\.", cleaned_item):
        return clean_text(cleaned_item)
    else:
        return clean_text(f"- {cleaned_item}")

# === PDF Extraction ===
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            if text.strip():
                return re.sub(r'Page\s*\d+', '', text)
    except:
        pass
    text = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    pdf_doc = fitz.open(tmp_path)
    for page in pdf_doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img)
    return re.sub(r'Page\s*\d+', '', text)

# === Universal Field Extraction ===
def extract_fields(text):
    fields = {}
    heading_patterns = {
        "Project Description": ["project description", "overview", "project overview"],
        "Objectives": ["objectives", "goals", "aims"],
        "Budget": ["budget", "budget breakdown", "cost breakdown", "project budget", "costing", "financial breakdown"],
        "Vendor Name": ["vendor", "vendor name", "supplier", "service provider", "vendor details"],
        "Timeline": ["timeline", "schedule", "project schedule", "milestones"],
        "Product Outcomes": ["product outcomes", "deliverables", "expected results", "output"]
    }
    for key, variants in heading_patterns.items():
        for variant in variants:
            pattern = rf"(?i){variant}[:\-\s]*([\s\S]*?)(?=\n(?:{'|'.join(sum(heading_patterns.values(), []))})[:\-\s]|\Z)"
            match = re.search(pattern, text)
            if match:
                val = clean_text(match.group(1)).strip()
                if key == "Vendor Name":
                    val = "\n".join([v.strip() for v in val.split("\n") if v.strip()])
                fields[key] = val
                break
    return fields

# === Grant Type Selection ===
st.markdown("---")
st.subheader("Select the Related Grant Type")
selected_grant_type = st.selectbox(
    "Grant Type:",
    [
        "Not Selected",
        "Productivity Solutions Grant (PSG)",
        "Enterprise Development Grant (EDG)",
        "SkillsFuture Enterprise Credit (SFEC)",
        "Market Readiness Assistance (MRA)",
        "Energy Efficiency Grant (EEG)",
        "Startup SG Founder",
        "Other / Unsure"
    ],
    index=0
)
st.session_state["selected_grant_type"] = selected_grant_type
st.markdown("---")

# === File Upload ===
uploaded_file = st.file_uploader("Upload your grant application PDF", type=["pdf"])

# === Consultant-Level Eligibility Check ===
def check_eligibility(text, grant):
    text_lower = text.lower()

    rules = {
        "PSG": [
            ["pre-approved vendor", "approved vendor", "vendor registered", "it solution", "digital solution"],
            ["quotation", "vendor quote", "proposal document", "cost proposal"]
        ],
        "EDG": [
            ["capability building", "process improvement", "innovation capability", "business transformation"],
            ["market expansion", "international growth", "overseas expansion", "regional expansion"]
        ],
        "SFEC": [
            ["cpf contributions", "central provident fund", "cpf compliance"],
            ["local employees", "singaporean staff", "permanent residents"]
        ]
    }

    missing = []
    for req_group in rules.get(grant, []):
        if not any(keyword in text_lower for keyword in req_group):
            missing.append(req_group[0])

    status = "Eligible" if not missing else ("Possible" if len(missing) < len(rules.get(grant, [])) else "No")

    reasoning = ""
    try:
        if st.session_state.get("use_dummy_mode", True):
            if grant == "EDG":
                reasoning = "The proposal includes elements of overseas market expansion and capability development but lacks explicit detail on capability-building initiatives."
            elif grant == "PSG":
                reasoning = "The project describes a digital solution but does not confirm use of a pre-approved vendor."
            elif grant == "SFEC":
                reasoning = "Eligibility for SFEC depends on CPF contributions and local employee requirements, which are not clearly documented."
            else:
                reasoning = "No strong indicators for this grant type were identified."
        else:
            import openai
            prompt = f"""
You are a Singapore SME grant consultant. Review the following content and assess eligibility for {grant}.

---
{text[:3000]}
---

Return a concise, formal consultant-style reasoning.
"""
            ai_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0
            )
            reasoning = ai_resp.choices[0].message["content"].strip()
    except Exception as e:
        reasoning = f"(Reasoning unavailable: {e})"

    return status, missing, reasoning

# === If file is uploaded ===
if uploaded_file:
    extracted = extract_text_from_pdf(uploaded_file)
    st.session_state["uploaded_doc_text"] = extracted
    fields = extract_fields(extracted)

    summary = {
        "Project Overview": fields.get("Project Description", "No project overview provided."),
        "Objectives": fields.get("Objectives", "No objectives provided."),
        "Budget Breakdown": fields.get("Budget", "No budget provided."),
        "Vendors": fields.get("Vendor Name", "No vendor information found."),
        "Timeline": fields.get("Timeline", "No timeline provided."),
        "Sample Grant Application": ["No sample grant application found."],
        "Product Outcomes": fields.get("Product Outcomes", "No product outcomes provided.")
    }

    matrix = {}
    for g in ["PSG", "EDG", "SFEC"]:
        status, missing, reasoning = check_eligibility(extracted, g)
        matrix[g] = (status, missing, reasoning)

    # === Display Project Summary ===
    st.subheader("Project Summary")
    for section, content in summary.items():
        st.markdown(f"**{section}:**")

        # Timeline special formatting for UI
        if section == "Timeline" and isinstance(content, str):
            date_patterns = re.findall(
                r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
                r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b.*?(?=\n|,|;|$)",
                content,
                flags=re.IGNORECASE
            )
            if len(date_patterns) > 1:
                with st.expander("View Timeline Details"):
                    for item in date_patterns:
                        st.markdown(f"- {item.strip()}")
            else:
                st.markdown(format_list_item(content))
        else:
            if isinstance(content, list):
                for item in content:
                    st.markdown(format_list_item(item))
            else:
                st.markdown(format_list_item(content))
        st.markdown("")

    # === Display Eligibility Matrix ===
    st.markdown("---")
    st.subheader("Eligibility Matrix")
    for g, data in matrix.items():
        status, missing, reasoning = data
        with st.expander(f"{g} – Status: {status}"):
            st.write(f"**Missing Requirements:** {', '.join(missing) if missing else 'None'}")
            with st.expander("View Consultant's Reasoning"):
                st.write(reasoning)

    # === Recommendations Generator ===
    def generate_recommendations(summary, matrix):
        recs = []
        pos = []
        next_steps = []

        if not summary["Objectives"] or "No objectives" in str(summary["Objectives"]):
            recs.append(("Critical", "Provide clear, measurable objectives with at least 2–3 KPIs linked to grant outcomes."))
            next_steps.append("Define measurable KPIs aligned with grant objectives.")
        elif len(str(summary["Objectives"]).split()) < 10:
            recs.append(("Important", "Expand objectives with clear timelines and performance indicators."))
            next_steps.append("Expand objectives with measurable results over a defined timeline.")
        else:
            pos.append("Objectives are detailed and measurable.")

        if summary["Budget Breakdown"].startswith("No budget"):
            recs.append(("Critical", "Include a detailed budget breakdown with justifications."))
            next_steps.append("Prepare a detailed cost table with justifications.")
        elif len(summary["Budget Breakdown"].split()) < 10:
            recs.append(("Important", "Expand budget with itemised costs and vendor quotes."))
            next_steps.append("Add more detail to budget items and vendor quotations.")
        else:
            pos.append("Budget is well-structured and justified.")

        if str(summary["Vendors"]).startswith("No vendor"):
            recs.append(("Important", "Add vendor details and justify their selection."))
            next_steps.append("Identify and document vendor qualifications.")
        else:
            pos.append("Vendor details are clear and relevant.")

        if summary["Timeline"].startswith("No timeline"):
            recs.append(("Important", "Provide a clear project timeline with milestones."))
            next_steps.append("Create a timeline with milestones and dates.")
        else:
            pos.append("Timeline is clear and logical.")

        for g, data in matrix.items():
            status, _, _ = data
            if status != "Eligible":
                recs.append(("Critical" if status == "No" else "Important", f"Address gaps to meet {g} eligibility criteria."))
                next_steps.append(f"Review and meet {g} missing requirements.")

        return recs, pos, next_steps

    recs, pos, next_steps = generate_recommendations(summary, matrix)

    # === Display Recommendations ===
    st.markdown("---")
    st.subheader("AI‑Powered Consultant Recommendations")
    severity_colors = {"Critical": "#FF4B4B", "Important": "#FFA500", "Optional": "#00C851"}
    for severity, rec in recs:
        st.markdown(f"<span style='color:{severity_colors.get(severity, '#FFFFFF')}; font-weight:bold;'>[{severity}]</span> {rec}", unsafe_allow_html=True)

    if pos:
        st.subheader("Strengths")
        for p in pos:
            st.markdown(f"- {p}")

    if next_steps:
        st.subheader("Key Next Steps")
        for step in next_steps:
            st.markdown(f"- {step}")

# === PDF Export with Timeline Bullets & Key Next Steps ===
class BrandedPDF(FPDF):
    def safe_write(self, method, *args, **kwargs):
        safe_args = [safe_pdf_text(a) if isinstance(a, str) else a for a in args]
        return getattr(super(), method)(*safe_args, **kwargs)

    def header(self):
        if self.page_no() == 1:
            try:
                self.image("optra_logo_transparent.png", 10, 8, 15)
            except:
                pass
            self.safe_write("set_font", "Helvetica", "B", 16)
            self.safe_write("cell", 0, 10, "Grant Document Review", ln=True, align="C")
            self.safe_write("set_font", "Helvetica", "I", 10)
            self.safe_write("cell", 0, 8, "Confidential – For Internal and Review Use Only", ln=True, align="C")
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        try:
            self.image("optra_logo_transparent.png", 10, self.get_y()-2, 6)
        except:
            pass
        self.set_x(20)
        self.safe_write("set_font", "Helvetica", "I", 8)
        self.safe_write("cell", 0, 5, "Generated by OPTRA – Smart Grant Advisor", align="L")
        self.safe_write("cell", 0, 5, f"Page {self.page_no()}/{{nb}}", align="R")

def generate_pdf(summary, matrix, recs, pos, next_steps):
    pdf = BrandedPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Project Summary
    for title, content in summary.items():
        pdf.safe_write("set_font", "Helvetica", "B", 12)
        pdf.safe_write("multi_cell", 0, 6, f"{title}:")
        pdf.ln(1)
        pdf.safe_write("set_font", "Helvetica", "", 11)

        # Special handling for Timeline in PDF
        if title == "Timeline" and isinstance(content, str):
            date_patterns = re.findall(
                r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
                r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b.*?(?=\n|,|;|$)",
                content,
                flags=re.IGNORECASE
            )
            if len(date_patterns) > 1:
                for item in date_patterns:
                    pdf.safe_write("multi_cell", 0, 6, f"- {item.strip()}")
            else:
                pdf.safe_write("multi_cell", 0, 6, format_list_item(content))
        elif isinstance(content, list):
            for item in content:
                pdf.safe_write("multi_cell", 0, 6, format_list_item(item))
        else:
            pdf.safe_write("multi_cell", 0, 6, format_list_item(content))

        pdf.ln(3)

    # Eligibility Matrix
    pdf.safe_write("set_font", "Helvetica", "B", 12)
    pdf.safe_write("cell", 0, 8, "Eligibility Matrix", ln=True)
    pdf.safe_write("set_font", "Helvetica", "", 10)
    pdf.safe_write("cell", 50, 8, "Grant Type", border=1)
    pdf.safe_write("cell", 30, 8, "Status", border=1)
    pdf.safe_write("cell", 110, 8, "Missing Requirements", border=1, ln=True)
    for g, data in matrix.items():
        pdf.safe_write("cell", 50, 8, g, border=1)
        pdf.safe_write("cell", 30, 8, data[0], border=1)
        pdf.safe_write("multi_cell", 110, 8, ", ".join(data[1]) if data[1] else "-", border=1)
    pdf.ln(5)

    # Recommendations
    pdf.safe_write("set_font", "Helvetica", "B", 12)
    pdf.safe_write("cell", 0, 8, "AI‑Powered Consultant Recommendations", ln=True)
    pdf.safe_write("set_font", "Helvetica", "", 11)
    for severity, rec in recs:
        pdf.safe_write("multi_cell", 0, 6, f"[{severity}] {rec}")

    # Strengths
    if pos:
        pdf.ln(3)
        pdf.safe_write("set_font", "Helvetica", "B", 12)
        pdf.safe_write("cell", 0, 8, "Strengths", ln=True)
        pdf.safe_write("set_font", "Helvetica", "", 11)
        for p in pos:
            pdf.safe_write("multi_cell", 0, 6, f"- {p}")

    # Key Next Steps
    if next_steps:
        pdf.ln(3)
        pdf.safe_write("set_font", "Helvetica", "B", 12)
        pdf.safe_write("cell", 0, 8, "Key Next Steps", ln=True)
        pdf.safe_write("set_font", "Helvetica", "", 11)
        for step in next_steps:
            pdf.safe_write("multi_cell", 0, 6, f"- {step}")

    # Disclaimer
    pdf.ln(10)
    pdf.safe_write("set_font", "Helvetica", "I", 9)
    disclaimer = (
        "Disclaimer: This grant review is generated automatically based on the uploaded document and is intended "
        "for informational purposes only. It does not constitute financial or legal advice. While OPTRA takes care "
        "to ensure accuracy, final decisions on grant eligibility and approval rest with the respective funding agencies."
    )
    pdf.safe_write("multi_cell", 0, 5, disclaimer)

    buffer = BytesIO()
    buffer.write(pdf.output(dest='S').encode("latin-1", "replace"))
    buffer.seek(0)
    return buffer

# === Download Button ===
if uploaded_file:
    st.download_button(
        "Download Professional PDF Report",
        generate_pdf(summary, matrix, recs, pos, next_steps),
        "grant_review.pdf",
        mime="application/pdf"
    )



