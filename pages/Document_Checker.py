import streamlit as st
import pdfplumber
import openai
import os
import re
import tempfile
from dotenv import load_dotenv
from io import BytesIO
from fpdf import FPDF
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
use_dummy_mode = not bool(OPENAI_API_KEY)
if not use_dummy_mode:
    openai.api_key = OPENAI_API_KEY

# ----------------------------
# Extract text from PDF with OCR fallback
# ----------------------------
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            if text.strip():
                return re.sub(r'Page\s*\d+', '', text)
    except:
        pass

    # OCR fallback
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

# ----------------------------
# Extract key fields
# ----------------------------
def extract_fields(text):
    fields = {}
    fields["Project Title"] = re.search(r'Project Title[:\-]?\s*(.+)', text, re.IGNORECASE)
    fields["Company Name"] = re.search(r'Company Name[:\-]?\s*(.+)', text, re.IGNORECASE)
    fields["Budget"] = re.search(r'Budget[:\-]?\s*(.+?)(?=\n|Vendors|Timeline|$)', text, re.IGNORECASE | re.DOTALL)
    fields["Timeline"] = re.search(r'(Expected Timeline|Timeline)[:\-]?\s*(.+)', text, re.IGNORECASE)
    objectives = re.findall(r'(?:Objective[s]?:|Objectives\n)(.+?)(?=\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)

    clean = {}
    for key, match in fields.items():
        if match:
            clean[key] = match.group(1).strip()

    if objectives:
        lines = re.split(r'\n|[0-9]+\.', objectives[0])
        clean["Objectives"] = [line.strip('- ').strip() for line in lines if line.strip()]
    return clean

# ----------------------------
# Analyze content with GPT or dummy fallback
# ----------------------------
def analyze_text(text):
    if use_dummy_mode:
        return {
            "mistakes": ["No executive summary found.", "Missing vendor justification."],
            "recommendations": ["Add a summary of the project goals.", "Explain vendor selection rationale."]
        }

    prompt = (
        "You are a grant reviewer in Singapore. Review the following SME grant application text:\n\n"
        + text.strip() + "\n\n"
        "1. List any mistakes or missing parts.\n"
        "2. Explain why each is a problem.\n"
        "3. Recommend specific improvements for PSG/EDG grants.\n\n"
        "Format:\nMistakes:\n1. ...\n\nRecommendations:\n1. ..."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=800
    )

    content = response['choices'][0]['message']['content']
    sections = {"mistakes": [], "recommendations": []}
    current = None
    for line in content.splitlines():
        line = line.strip()
        if line.lower().startswith("mistakes"):
            current = "mistakes"
        elif line.lower().startswith("recommendations"):
            current = "recommendations"
        elif line and (line[0].isdigit() or line.startswith("-")) and current:
            cleaned = line.lstrip("1234567890.- ").strip()
            sections[current].append(cleaned)
    return sections

# ----------------------------
# PDF + TXT Export
# ----------------------------
class StyledPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Grant Application Review Report", ln=True, align="C")
        self.ln(5)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0)
        self.cell(0, 10, title, ln=True)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(50)

def generate_pdf(mistakes, recommendations):
    pdf = StyledPDF()
    pdf.add_page()
    pdf.section_title("Mistakes Identified")
    for m in mistakes:
        pdf.multi_cell(0, 10, f"- {m}")
    pdf.ln(3)
    pdf.section_title("Recommendations and Tips")
    for r in recommendations:
        pdf.multi_cell(0, 10, f"- {r}")
    pdf.ln(3)
    pdf.section_title("Checklist of Documents")
    for item in ["Latest ACRA BizFile", "Financial Statements", "Vendor quotation", "Proof of local employees"]:
        pdf.multi_cell(0, 10, f"- {item}")
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100)
    pdf.multi_cell(0, 10, "Note: Review is based on provided content. Refer to official guidelines for final decision.")
    buffer = BytesIO()
    buffer.write(pdf.output(dest='S').encode('latin-1'))
    buffer.seek(0)
    return buffer

def generate_txt(mistakes, recommendations):
    out = "Mistakes:\n" + "\n".join(f"- {m}" for m in mistakes)
    out += "\n\nRecommendations:\n" + "\n".join(f"- {r}" for r in recommendations)
    out += "\n\nChecklist:\n- Latest ACRA BizFile\n- Financial Statements\n- Vendor quotation\n- Proof of local employees"
    return out.encode("utf-8")

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Grant Application Checker", layout="centered")
st.title("Grant Application Checker")

st.markdown(
    "Upload a grant application PDF (text-based or scanned). This tool extracts content, detects mistakes, "
    "and offers improvement suggestions tailored to Singapore grants like PSG and EDG."
)

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    st.markdown("---")
    st.subheader("Extracted Grant Summary")

    with st.spinner("Processing your file..."):
        extracted = extract_text_from_pdf(uploaded_file)
        parsed = extract_fields(extracted)

    if not extracted.strip():
        st.warning("No readable text found in your PDF.")
    else:
        for field, value in parsed.items():
            if field == "Objectives" and isinstance(value, list):
                st.markdown("**Objectives:**")
                for o in value:
                    st.markdown(f"- {o}")
            else:
                st.markdown(f"**{field}:** {value}")

        st.markdown("**Full Extracted Text:**")
        formatted_text = re.sub(r'Page\s*\d+', '', extracted.strip()).replace("\n", "\n\n")
        st.markdown(
    f"<div style='background-color:#f8f9fa;padding:1rem;border-radius:6px;color:#000;'>"
    f"<pre style='white-space:pre-wrap; font-family:monospace; color:#000;'>{formatted_text}</pre>"
    f"</div>",
    unsafe_allow_html=True
        )

        with st.spinner("Analyzing with AI..."):
            results = analyze_text(extracted)

        st.success("Review complete.")
        st.subheader("Mistakes")
        for m in results["mistakes"]:
            st.markdown(f"- {m}")
        st.subheader("Recommendations")
        for r in results["recommendations"]:
            st.markdown(f"- {r}")

        st.subheader("Download Report")
        st.download_button("Download PDF", generate_pdf(results["mistakes"], results["recommendations"]), file_name="grant_review.pdf")
        st.download_button("Download TXT", generate_txt(results["mistakes"], results["recommendations"]), file_name="grant_review.txt")

else:
    st.info("Please upload a grant application PDF to begin.")
