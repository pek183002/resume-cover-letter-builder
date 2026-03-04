import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import PyPDF2
import re

# 1. AI Configuration
api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)
# genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

def get_match_score(resume, jd):
    prompt = f"""
    You are an Applicant Tracking System (ATS) analyzer. 
    Compare the Resume and Job Description (JD) below.
    Provide the output in exactly this format:
    SCORE: [0-100]
    MISSING KEYWORDS: [list them]
    EXPLANATION: [1-2 sentences]

    RESUME: {resume}
    JD: {jd}
    """
    response = model.generate_content(prompt)
    return response.text

# 2. PDF Creation Function
def create_pdf(content, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    # Standardizing text for PDF encoding
    pdf.multi_cell(0, 10, txt=content.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# 3. Streamlit Interface
st.set_page_config(page_title="Ultimate ATS Suite", layout="wide")
st.title("🎯 AI Resume Matcher & Builder")

with st.sidebar:
    st.header("Upload Center")
    uploaded_file = st.file_uploader("Upload Master Resume", type="pdf")
    job_desc = st.text_area("Job Description", height=300)
    process_btn = st.button("Analyze & Tailor")

if process_btn and uploaded_file and job_desc:
    # Read Resume
    reader = PyPDF2.PdfReader(uploaded_file)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text()

    # --- PHASE 1: SCORING ---
    with st.spinner("Analyzing Match Score..."):
        analysis = get_match_score(resume_text, job_desc)
        
        # Extract score using regex for the UI gauge
        score_match = re.search(r"SCORE:\s*(\d+)", analysis)
        score = int(score_match.group(1)) if score_match else 0
        
        # Display Score UI
        st.metric(label="ATS Match Score", value=f"{score}%")
        st.progress(score / 100)
        st.info(analysis)

    # --- PHASE 2: GENERATION ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tailored Resume")
        res_prompt = f"Rewrite this resume to match this JD perfectly. Resume: {resume_text} JD: {job_desc}"
        tailored_res = model.generate_content(res_prompt).text
        st.text_area("Edit Resume:", tailored_res, height=400, key="res_edit")
        
        res_pdf = create_pdf(st.session_state.res_edit, "Tailored Resume")
        st.download_button("Download Resume", res_pdf, "Resume.pdf", "application/pdf")

    with col2:
        st.subheader("Tailored Cover Letter")
        cl_prompt = f"Write a cover letter for this JD using this resume. Resume: {resume_text} JD: {job_desc}"
        tailored_cl = model.generate_content(cl_prompt).text
        st.text_area("Edit Letter:", tailored_cl, height=400, key="cl_edit")
        
        cl_pdf = create_pdf(st.session_state.cl_edit, "Cover Letter")
        st.download_button("Download Cover Letter", cl_pdf, "CoverLetter.pdf", "application/pdf")
