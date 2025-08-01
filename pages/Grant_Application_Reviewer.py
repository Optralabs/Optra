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

# === App Config ===
st.set_page_config(
    page_title="Grant Application Reviewer",
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

st.markdown("---")

# === Unicode-safe text cleaner ===
def clean_text(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

# === Ensure safe PDF text ===
def safe_pdf_text(text):
    return clean_text(text).encode("latin-1", "replace").decode("latin-1")

# === Bullet/Number Handling ===
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

# === Detect if it's a grant application ===
def is_grant_application(text):
    keywords = ["grant", "funding", "application", "proposal", "budget", "timeline", "objectives", "vendor", "KPI"]
    count = sum(1 for k in keywords if k.lower() in text.lower())
    return count >= 3

# === Vendor cleaning ===
def clean_vendor_name(vendor):
    vendor = re.sub(r"^[sS]:\s*", "", vendor)
    vendor = re.sub(r"^[•\-\–\—○]+\s*", "", vendor)
    return vendor.strip()

# === Extract key sections ===
def extract_fields(text):
    fields = {}
    patterns = {
        "Project Description": r'(?:Project\s+Description|Overview)[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)',
        "Objectives": r'(?:Objectives?)[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)',
        "Budget": r'(?:Budget|Cost\s+Breakdown)[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)',
        "Vendor Name": r'(?:Vendors?)[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)',
        "Timeline": r'(?:Timeline|Schedule)[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)',
        "Product Outcomes": r'(?:Outcomes?|Deliverables?)[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)'
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            val = clean_text(match.group(1).strip())
            if key == "Vendor Name":
                val = "\n".join([clean_vendor_name(v) for v in val.split("\n") if v.strip()])
            fields[key] = val
    return fields

# === Build project summary ===
def build_project_summary(fields):
    vendors = fields.get("Vendor Name", "")
    if isinstance(vendors, str):
        vendors_list = [clean_vendor_name(v) for v in re.split(r';|,|\n', vendors) if clean_vendor_name(v)]
    else:
        vendors_list = [clean_vendor_name(v) for v in vendors if clean_vendor_name(v)]
    return {
        "Project Overview": fields.get("Project Description", "No project overview provided."),
        "Objectives": fields.get("Objectives", ["No objectives provided."]),
        "Budget Breakdown": fields.get("Budget", "No budget provided."),
        "Vendors": vendors_list if vendors_list else ["No vendor information found."],
        "Timeline": fields.get("Timeline", "No timeline provided."),
        "Sample Grant Application": ["No sample grant application found. This may be because the project is not eligible for PSG, EDG, or SFEC grants."],
        "Product Outcomes": fields.get("Product Outcomes", ["No product outcomes provided. This may be because the project is not eligible for PSG, EDG, or SFEC grants."])
    }

# === Eligibility Checking ===
def check_eligibility(text, grant):
    rules = {
        "PSG": ["pre-approved vendor", "quotation"],
        "EDG": ["capability building", "market expansion"],
        "SFEC": ["cpf contributions", "local employees"]
    }
    missing = [req for req in rules.get(grant, []) if req not in text.lower()]
    if not missing:
        return "Eligible", []
    elif len(missing) < len(rules.get(grant, [])):
        return "Possible", missing
    else:
        return "No", missing

# === Consultant-Level Recommendations ===
def generate_recommendations(summary, matrix):
    recs = []
    pos = []
    if not summary["Objectives"] or "No objectives" in summary["Objectives"][0]:
        recs.append(("Critical", "Provide clear, measurable objectives with at least 2–3 KPIs."))
    elif len(summary["Objectives"]) < 3:
        recs.append(("Important", "Expand objectives to cover more specific goals and timelines."))
    else:
        pos.append("Your objectives are detailed and measurable — this is a strong section.")
    if summary["Budget Breakdown"].startswith("No budget"):
        recs.append(("Critical", "Include a detailed budget breakdown with justifications for each item."))
    elif len(summary["Budget Breakdown"].split()) < 10:
        recs.append(("Important", "Expand the budget with cost justifications for each component."))
    else:
        pos.append("Your budget section is detailed and well‑justified.")
    if summary["Vendors"][0].startswith("No vendor"):
        recs.append(("Important", "Add vendor details and selection rationale, especially for PSG."))
    else:
        pos.append("Vendor details are present.")
    if summary["Timeline"].startswith("No timeline"):
        recs.append(("Important", "Specify a clear timeline with defined milestones and delivery dates."))
    else:
        pos.append("Your timeline is clearly stated.")
    if matrix["SFEC"][0] != "Eligible":
        recs.append(("Critical", "Provide proof of CPF contributions and local employee count for SFEC eligibility."))
    if matrix["PSG"][0] != "Eligible":
        recs.append(("Important", "For PSG, confirm pre‑approved vendor status and include a formal quotation."))
    return recs, pos

# === PDF Generator ===
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

def generate_pdf(summary, matrix, recs, pos):
    pdf = BrandedPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    for title, content in summary.items():
        pdf.safe_write("set_font", "Helvetica", "B", 12)
        pdf.safe_write("multi_cell", 0, 6, f"{title}:")
        pdf.ln(1)
        pdf.safe_write("set_font", "Helvetica", "", 11)
        if isinstance(content, list):
            for item in content:
                pdf.safe_write("multi_cell", 0, 6, format_list_item(item))
        else:
            pdf.safe_write("multi_cell", 0, 6, format_list_item(content))
        pdf.ln(3)
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
    pdf.safe_write("set_font", "Helvetica", "B", 12)
    pdf.safe_write("cell", 0, 8, "AI‑Powered Consultant Recommendations", ln=True)
    pdf.safe_write("set_font", "Helvetica", "", 11)
    for severity, rec in recs:
        pdf.safe_write("multi_cell", 0, 6, f"[{severity}] {rec}")
    if pos:
        pdf.ln(3)
        pdf.safe_write("set_font", "Helvetica", "B", 12)
        pdf.safe_write("cell", 0, 8, "Strengths", ln=True)
        pdf.safe_write("set_font", "Helvetica", "", 11)
        for p in pos:
            pdf.safe_write("multi_cell", 0, 6, f"- {p}")
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

# === Main UI ===
uploaded_file = st.file_uploader("Upload your grant application PDF", type=["pdf"])
if uploaded_file:
    extracted = extract_text_from_pdf(uploaded_file)
    if not is_grant_application(extracted):
        st.error("❌ This document does not appear to be a grant application.")
    else:
        fields = extract_fields(extracted)
        summary = build_project_summary(fields)
        matrix = {g: check_eligibility(extracted, g) for g in ["PSG", "EDG", "SFEC"]}
        recs, pos = generate_recommendations(summary, matrix)

        # Project Summary
        st.subheader("Project Summary")
        for section, content in summary.items():
            st.markdown(f"**{section}:**")
            if isinstance(content, list):
                for item in content:
                    st.markdown(format_list_item(item))
            else:
                st.markdown(format_list_item(content))
            st.markdown("")

        # Separator before Eligibility Matrix
        st.markdown("---")

        # Eligibility Matrix
        st.subheader("Eligibility Matrix")
        for g, data in matrix.items():
            with st.expander(f"{g} – Status: {data[0]}"):
                st.write(f"**Missing Requirements:** {', '.join(data[1]) if data[1] else 'None'}")

        # Separator before AI-Powered Consultant Recommendations
        st.markdown("---")

        # AI‑Powered Recommendations with colors
        st.subheader("AI‑Powered Consultant Recommendations")
        severity_colors = {"Critical": "#FF4B4B", "Important": "#FFA500", "Optional": "#00C851"}
        for severity, rec in recs:
            st.markdown(f"<span style='color:{severity_colors.get(severity, '#FFFFFF')}; font-weight:bold;'>[{severity}]</span> {rec}", unsafe_allow_html=True)

        # Strengths
        if pos:
            st.subheader("Strengths")
            for p in pos:
                st.markdown(f"- {p}")

        # Extra spacing before download button
        st.markdown("<br>", unsafe_allow_html=True)

        # Download
        st.download_button(
            "Download Professional PDF Report",
            generate_pdf(summary, matrix, recs, pos),
            "grant_review.pdf",
            mime="application/pdf"
        )
else:
    st.info("Please upload a grant application PDF to begin.")


