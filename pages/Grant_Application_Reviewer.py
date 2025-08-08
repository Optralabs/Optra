import streamlit as st
from globals import get_user_plan, show_locked_page
from auth import verify_token


# 1) Page config early (avoid duplicate set_page_config later in the file)
st.set_page_config(page_title="OPTRA", layout="wide", page_icon="optra_logo_transparent.png")


# 2) Resolve the user’s email
# Prefer session (set by Home.py), then token
decoded = verify_token()  # should read st.query_params["token"] if present
email_from_token = (decoded or {}).get("email")
email = st.session_state.get("user_email") or email_from_token


# 3) Resolve plan
plan = get_user_plan(email) if email else None


# 4) Access rules
# Allow Starter + Pro:
if plan not in ("Starter Plan", "Pro Plan"):
   # Consistent locked styling + stop
   show_locked_page("🔒 This page is locked. Please unlock access on the Home page.")


# If you want this page to require Pro only, use this instead:
# if plan != "Pro Plan":
#     show_locked_page("🔒 Pro plan required. Upgrade to access this page.")


# 5) Keep session in sync
st.session_state["user_email"] = email
st.session_state["user_plan"]  = plan
st.session_state["unlocked"]   = True


# (Optional) Same gradient for unlocked pages too:
st.markdown("""
<style>
 html, body, [data-testid="stAppViewContainer"] {
     background: linear-gradient(to bottom, #0a0a0a 0%, #0a0a0a 10%, #0d0f1c 30%, #0f111f 60%, #00011d 100%) !important;
     color: #ffffff !important;
 }
 section[data-testid="stSidebar"] { background-color: #000 !important; }
 section[data-testid="stSidebar"] * { color: #fff !important; }
</style>
""", unsafe_allow_html=True)


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
from auth import verify_token
from globals import show_locked_page, get_logo_base64
from feedback import show_feedback_ui, get_past_good_answers


# === Page Config ===
st.set_page_config(
   page_title="Grant Application Reviewer",
   page_icon="optra_logo_transparent.png",
   layout="wide"
)


# === Logo Display ===
logo_base64 = get_logo_base64()
st.markdown(f"""
   <div style='display:flex;align-items:center;margin-bottom:0.5rem;'>
       <img src='data:image/png;base64,{logo_base64}' width='80' style='margin-right:15px;'/>
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
# Safeguard placeholders so we never hit NameError
summary = None
matrix = None


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


   # Static reasoning for now
   if grant == "EDG":
       reasoning = "The proposal includes elements of overseas market expansion and capability development but lacks explicit detail on capability-building initiatives."
   elif grant == "PSG":
       reasoning = "The project describes a digital solution but does not confirm use of a pre-approved vendor."
   elif grant == "SFEC":
       reasoning = "Eligibility for SFEC depends on CPF contributions and local employee requirements, which are not clearly documented."
   else:
       reasoning = "No strong indicators for this grant type were identified."


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


   # ✅ Store AI output for feedback UI
   st.session_state["ai_output_for_feedback"] = "\n".join([f"{k}: {v}" for k, v in summary.items()])


   # ✅ Store page context for feedback
   st.session_state["feedback_context"] = {
       "page_name": "Document Checker",
       "grant_type": selected_grant_type,
       "industry": None
   }


   # Continue with displaying project summary, eligibility matrix, etc.


# === Display Project Summary (Timeline collapsible) ===
if summary is not None:
   st.subheader("Project Summary")
   for section, content in summary.items():
       if section == "Timeline" and isinstance(content, str):
           with st.expander("Timeline", expanded=False):
               import re
               # Only split by new lines to avoid breaking ranges
               timeline_items = re.split(r"\n+", content)
               for item in timeline_items:
                   item = item.strip()
                   if not item:
                       continue
                   # Match single dates, months, years, or ranges (keeps ranges together)
                   if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2}/\d{1,2}|\d{4})(?:\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2}/\d{1,2}|\d{4}))?\b", item, re.IGNORECASE):
                       st.markdown(f"- {item}")
                   else:
                       st.markdown(item)


       else:
           st.markdown(f"**{section}:**")
           if isinstance(content, list):
               for item in content:
                   st.markdown(format_list_item(item))
           else:
               st.markdown(format_list_item(content))
       st.markdown("")


else:
   st.info("Upload a PDF to see the project summary.")


# === Eligibility Matrix ===
if matrix is not None:
   st.markdown("---")
   st.subheader("Eligibility Matrix")
   for g, data in matrix.items():
       status, missing, reasoning = data
       with st.expander(f"{g} – Status: {status}"):
           st.write(f"**Missing Requirements:** {', '.join(missing) if missing else 'None'}")
           with st.expander("View Consultant's Reasoning"):
               st.write(reasoning)
else:
   st.info("Upload a PDF to check eligibility.")


# === PDF Export Class ===
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


# === Generate PDF ===
def generate_pdf(summary, matrix):
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
   for g, data in matrix.items():
       pdf.safe_write("cell", 50, 8, g, border=1)
       pdf.safe_write("cell", 30, 8, data[0], border=1)
       pdf.safe_write("multi_cell", 110, 8, ", ".join(data[1]) if data[1] else "-", border=1)


   buffer = BytesIO()
   buffer.write(pdf.output(dest='S').encode("latin-1", "replace"))
   buffer.seek(0)
   return buffer


# === Download Button ===
if uploaded_file:
   st.download_button(
       "Download Professional PDF Report",
       generate_pdf(summary, matrix),
       "grant_review.pdf",
       mime="application/pdf"
   )


# === Feedback UI (bottom of file) ===
if st.session_state.get("ai_output_for_feedback") and st.session_state.get("feedback_context", {}).get("page_name"):
   show_feedback_ui(
       st.session_state["feedback_context"]["page_name"],
       st.session_state["ai_output_for_feedback"]
   )



