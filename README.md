# SME Grant Assistant

**SME Grant Assistant** is a Streamlit web app built to help 
Singapore-based Small and Medium Enterprises (SMEs) evaluate their 
eligibility for key government grants like EDG, PSG, and SFEC. It offers 
eligibility screening, business document analysis, live scraped grant 
listings, and AI-powered justification output.

---

## 🎯 Key Features

- **Eligibility Screening**  
  Evaluate your company's eligibility for the EDG, PSG, and SFEC schemes 
based on official EnterpriseSG and SkillsFuture guidelines.

- **Smart Grant Recommendation**  
  Provides clean, bullet-pointed results with justifications, recommended 
documents, and steps to improve eligibility.

- **Document Upload & Extraction**  
  Upload ACRA BizFile or financial statements (PDF). The tool extracts UEN 
and industry information for personalized analysis.

- **Live PSG & EDG Grant Listings**  
  Scrapes official grant pages for updated grant tools, categories, and 
resource links.

- **PDF/Text Report Download**  
  Get a professional downloadable output of your eligibility results.

- **Tips & Recommendations**  
  Practical advice to improve approval chances, including using 
pre-approved vendors, meeting eligibility requirements, and combining 
grants effectively.

- **FAQ & Feedback**  
  Ask questions about grants and leave feedback.

---

## ⚙️ Requirements

- Python 3.8+
- pip
- A `.env` file with your OpenAI API key (optional if using dummy mode)

### Python Dependencies

The app uses:

- `streamlit`
- `openai`
- `python-dotenv`
- `requests`
- `beautifulsoup4`
- `pdfplumber`
- `fpdf`
- `pandas`

---

## 📄 Grant Schemes Covered

### Enterprise Development Grant (EDG)
For strategic business transformation and internationalisation.

### Productivity Solutions Grant (PSG)
For adopting pre-approved IT and equipment solutions.

### SkillsFuture Enterprise Credit (SFEC)
For businesses that invest in upskilling and business transformation.

The eligibility logic is designed to reflect current public criteria but 
should be verified against official EnterpriseSG and GoBusiness sites.

---

## 🚀 How to Run

### 1. Clone the repository

### 2. Install dependencies
`pip install -r requirements.txt`

### 3. Add your OpenAI API key
Create a `.env` file in the project root folder and paste your key like 
this:
`OPENAI_API_KEY=sk-your-api-key-here`

### 4. Run the app locally
`streamlit run app.py`

---

## 🔐 Security Notice

Your `.env` file is ignored by `.gitignore` and not tracked by Git.

Do not share your API key publicly or commit it to version control.

---

## 💡 Why This Tool?

This assistant helps SMEs save time and get clear, actionable advice on 
Singapore government grants without needing to interpret dense documents 
or search across websites.




