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

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Terms and Conditions Analysis Report", ln=True, align='C')
    pdf.ln(10)

    # Section summaries
    sections = {
        "Core Terms": "These fundamental elements form the backbone of the agreement, establishing basic rights, responsibilities, and operational framework.",
        "Quality & Compliance": "This section evaluates regulatory adherence, quality standards, and compliance measures that ensure service reliability and legal conformity.",
        "Delivery & Fulfillment": "These terms outline the logistics, responsibilities, and processes for product/service delivery and customer satisfaction."
    }

    ANALYSIS_CATEGORIES = ["Category1", "Category2", "Category3", "Category4", "Category5", "Category6", "Category7", "Category8", "Category9", "Category10", "Category11", "Category12", "Category13", "Category14", "Category15", "Category16", "Category17", "Category18", "Category19", "Category20", "Category21", "Category22", "Category23"] # Placeholder - needs to be replaced with the actual definition

    current_section = None
    for category, details in analysis_results.items():
        # Determine which section this category belongs to
        if category in ANALYSIS_CATEGORIES[:14]:
            section = "Core Terms"
        elif category in ANALYSIS_CATEGORIES[14:22]:
            section = "Quality & Compliance"
        else:
            section = "Delivery & Fulfillment"

        # Add section header and summary if we're starting a new section
        if section != current_section:
            current_section = section
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=section, ln=True)
            pdf.set_font("Arial", 'I', 12)
            pdf.multi_cell(0, 10, txt=sections[section])
            pdf.ln(5)
            pdf.set_font("Arial", size=12)

        if details['risk_level'] in ['High', 'Medium']:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=category, ln=True)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt=f"Risk Level: {details['risk_level']}")
            pdf.multi_cell(0, 10, txt=f"Findings: {details['findings']}")
            pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

def generate_csv_report(analysis_results):
    # Add section info to each row
    data = []
    ANALYSIS_CATEGORIES = ["Category1", "Category2", "Category3", "Category4", "Category5", "Category6", "Category7", "Category8", "Category9", "Category10", "Category11", "Category12", "Category13", "Category14", "Category15", "Category16", "Category17", "Category18", "Category19", "Category20", "Category21", "Category22", "Category23"] # Placeholder - needs to be replaced with the actual definition

    for category, details in analysis_results.items():
        if category in ANALYSIS_CATEGORIES[:14]:
            section = "Core Terms"
            section_summary = "Fundamental agreement elements and basic rights"
        elif category in ANALYSIS_CATEGORIES[14:22]:
            section = "Quality & Compliance"
            section_summary = "Regulatory adherence and quality standards"
        else:
            section = "Delivery & Fulfillment"
            section_summary = "Logistics and delivery processes"

        data.append({
            'Section': section,
            'Section Summary': section_summary,
            'Category': category,
            'Risk Level': details['risk_level'],
            'Findings': details['findings']
        })
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')