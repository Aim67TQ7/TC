import io
import PyPDF2
from docx import Document
import pandas as pd
from fpdf import FPDF

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(uploaded_file)
    else:
        return uploaded_file.getvalue().decode("utf-8")

def generate_pdf_report(analysis_results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Terms and Conditions Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    for category, details in analysis_results.items():
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=category, ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=f"Risk Level: {details['risk_level']}")
        pdf.multi_cell(0, 10, txt=f"Findings: {details['findings']}")
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin-1')

def generate_csv_report(analysis_results):
    data = []
    for category, details in analysis_results.items():
        data.append({
            'Category': category,
            'Risk Level': details['risk_level'],
            'Findings': details['findings']
        })
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')
