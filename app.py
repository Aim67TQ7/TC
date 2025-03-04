import streamlit as st
import os
import pandas as pd
from utils import extract_text_from_file, generate_pdf_report, generate_csv_report
from analyzer import analyze_document, ANALYSIS_CATEGORIES
from styles import apply_custom_styles, show_risk_indicator

def main():
    apply_custom_styles()

    st.title("T&C Review Agent")
    st.markdown("Upload your T&C document for comprehensive analysis across key areas of concern.")

    uploaded_file = st.file_uploader(
        "Upload your document (PDF, DOCX, or TXT)", 
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:
        with st.spinner("Extracting text from document..."):
            document_text = extract_text_from_file(uploaded_file)

        # Show document preview
        with st.expander("Document Preview"):
            st.text_area("", document_text[:1000] + "...", height=200)

        if st.button("Analyze Document"):
            with st.spinner("Analyzing document..."):
                # Perform analysis
                analysis_results = analyze_document(document_text)

                # Define category sections
                sections = {
                    "Core Terms": ANALYSIS_CATEGORIES[:14],
                    "Quality & Compliance": ANALYSIS_CATEGORIES[14:22],
                    "Delivery & Fulfillment": ANALYSIS_CATEGORIES[22:]
                }

                # Display results by section
                for section_name, categories in sections.items():
                    st.markdown(f"### {section_name}")

                    # Create three columns for the grid layout
                    cols = st.columns(3)

                    # Distribute categories across columns
                    for idx, category in enumerate(categories):
                        col_idx = idx % 3
                        result = analysis_results[category]

                        with cols[col_idx]:
                            st.markdown(f"""
                                {show_risk_indicator(result['risk_level'])} **{category}**  
                                <div class='findings-text'>{result['findings'][:100]}...</div>
                            """, unsafe_allow_html=True)

                # Download options
                st.markdown("### Download Reports")
                col1, col2 = st.columns(2)
                with col1:
                    pdf_report = generate_pdf_report(analysis_results)
                    st.download_button(
                        "Download PDF Report",
                        pdf_report,
                        "tc_analysis_report.pdf",
                        "application/pdf"
                    )

                with col2:
                    csv_report = generate_csv_report(analysis_results)
                    st.download_button(
                        "Download CSV Report",
                        csv_report,
                        "tc_analysis_report.csv",
                        "text/csv"
                    )

if __name__ == "__main__":
    main()