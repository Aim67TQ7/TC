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

    # Add metrics summary if available
    if 'metrics' in analysis_results:
        metrics = analysis_results['metrics']
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Analysis Metrics", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=f"Complexity Score: {metrics['complexity_score']:.1f}%")
        pdf.multi_cell(0, 10, txt=f"Financial Impact: {metrics['financial_impact']:.1f}%")
        pdf.multi_cell(0, 10, txt=f"Unusual Terms Ratio: {metrics['unusual_terms_ratio']:.1f}%")
        pdf.ln(10)

    # Section summaries
    sections = {
        "Core Terms": "These fundamental elements form the backbone of the agreement, establishing basic rights, responsibilities, and operational framework.",
        "Quality & Compliance": "This section evaluates regulatory adherence, quality standards, and compliance measures that ensure service reliability and legal conformity.",
        "Delivery & Fulfillment": "These terms outline the logistics, responsibilities, and processes for product/service delivery and customer satisfaction."
    }

    current_section = None
    for category, details in analysis_results.items():
        if category == 'metrics':
            continue

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

            # Add quoted phrases with ASCII indicators instead of emoji
            if details['quoted_phrases']:
                pdf.multi_cell(0, 10, txt="Notable Terms:")
                for phrase in details['quoted_phrases']:
                    marker = "[!]" if phrase['is_financial'] else "[*]"  # ASCII markers instead of emoji
                    pdf.multi_cell(0, 10, txt=f"{marker} {phrase['text']}")
            pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

def generate_csv_report(analysis_results):
    # Add section info to each row
    data = []

    for category, details in analysis_results.items():
        if category == 'metrics':
            continue

        if category in ANALYSIS_CATEGORIES[:14]:
            section = "Core Terms"
            section_summary = "Fundamental agreement elements and basic rights"
        elif category in ANALYSIS_CATEGORIES[14:22]:
            section = "Quality & Compliance"
            section_summary = "Regulatory adherence and quality standards"
        else:
            section = "Delivery & Fulfillment"
            section_summary = "Logistics and delivery processes"

        # Create a row for each quoted phrase
        if details['quoted_phrases']:
            for phrase in details['quoted_phrases']:
                data.append({
                    'Section': section,
                    'Section Summary': section_summary,
                    'Category': category,
                    'Risk Level': details['risk_level'],
                    'Findings': details['findings'],
                    'Term': phrase['text'],
                    'Is Financial': 'Yes' if phrase['is_financial'] else 'No'
                })
        else:
            data.append({
                'Section': section,
                'Section Summary': section_summary,
                'Category': category,
                'Risk Level': details['risk_level'],
                'Findings': details['findings'],
                'Term': '',
                'Is Financial': ''
            })

    # Add metrics as a separate section if available
    if 'metrics' in analysis_results:
        metrics = analysis_results['metrics']
        data.append({
            'Section': 'Metrics Summary',
            'Section Summary': 'Overall analysis metrics',
            'Category': 'Complexity Score',
            'Risk Level': f"{metrics['complexity_score']:.1f}%",
            'Findings': 'Percentage of categories with specific requirements or unusual terms',
            'Term': '',
            'Is Financial': ''
        })

    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

ANALYSIS_CATEGORIES = ["Category1", "Category2", "Category3", "Category4", "Category5", "Category6", "Category7", "Category8", "Category9", "Category10", "Category11", "Category12", "Category13", "Category14", "Category15", "Category16", "Category17", "Category18", "Category19", "Category20", "Category21", "Category22", "Category23"]