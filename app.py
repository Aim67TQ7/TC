import streamlit as st
import os
from utils import extract_text_from_file, generate_pdf_report, generate_csv_report
from analyzer import analyze_document, ANALYSIS_CATEGORIES
from styles import apply_custom_styles, show_risk_level

def main():
    apply_custom_styles()

    st.title("T&C Review Agent")
    st.markdown("Upload your T&C document for comprehensive analysis across key areas of concern.")

    # Add explanation of analysis categories
    with st.expander("📋 What We Review"):
        st.markdown("""
        Our agent analyzes Terms & Conditions documents across these 14 key areas:

        1. **Introduction and Overview**: Purpose, scope, and acceptance methods
        2. **User Rights and Responsibilities**: Usage rights, restrictions, and account obligations
        3. **Privacy Policy and Data Usage**: Data collection, sharing, and protection practices
        4. **Payment Terms**: Pricing, refunds, and payment processing details
        5. **Intellectual Property Rights**: Content ownership and usage rights
        6. **Limitation of Liability**: Company's liability scope and warranty disclaimers
        7. **Termination and Suspension**: Account termination conditions and processes
        8. **Dispute Resolution**: Conflict resolution methods and jurisdiction
        9. **Amendments and Updates**: Terms modification processes and notification methods
        10. **Governing Law**: Applicable legal jurisdiction and frameworks
        11. **Force Majeure**: Provisions for unforeseeable circumstances
        12. **Severability**: Impact of invalid terms on overall agreement
        13. **User Consent for Marketing**: Marketing communications and opt-out rights
        14. **Specific Rights for Certain Regions**: Region-specific legal requirements
        """)

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
                progress_bar = st.progress(0)

                # Perform analysis
                analysis_results = analyze_document(document_text)

                # Display results
                st.markdown("### Analysis Results")

                # Filter categories
                selected_categories = st.multiselect(
                    "Filter by category",
                    ANALYSIS_CATEGORIES,
                    default=ANALYSIS_CATEGORIES
                )

                # Display results for selected categories
                for category in selected_categories:
                    result = analysis_results[category]
                    with st.expander(category):
                        st.markdown(show_risk_level(result['risk_level']), unsafe_allow_html=True)
                        st.markdown("**Findings:**")
                        st.write(result['findings'])

                # Download options
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