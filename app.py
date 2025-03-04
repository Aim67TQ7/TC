import streamlit as st
import os
import pandas as pd
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
        Our agent analyzes Terms & Conditions documents across these key categories:

        ### Core Terms:
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

        ### Quality & Compliance:
        15. **Quality Assurance and Performance**: Service level agreements and quality standards
        16. **Audits and Monitoring**: Audit rights and compliance monitoring
        17. **Regulatory Compliance**: Industry-specific regulatory requirements
        18. **Product Safety Certifications**: Safety standards and regulatory approvals
        19. **Liability for Regulatory Breaches**: Consequences of regulatory non-compliance
        20. **Third-Party Audits**: External auditing and certification requirements
        21. **International Standards Compliance**: Global regulatory framework adherence
        22. **Regulatory Violation Recourse**: Consumer rights and remedies

        ### Delivery & Fulfillment:
        23. **Delivery Process and Timeframes**: Estimated delivery times and guarantees
        24. **Delivery Costs**: Shipping fees, handling charges, and payment terms
        25. **Delivery Risk and Responsibility**: Transfer of risk and ownership during shipping
        26. **Delayed or Failed Deliveries**: Handling of delays and delivery failures
        27. **Delivery Location and Restrictions**: Geographic limitations and address requirements
        28. **International Delivery**: Cross-border shipping terms and customs handling
        29. **Returns and Delivery Failures**: Return shipping policies and procedures
        30. **Acceptance of Delivery**: Inspection requirements and signature protocols
        31. **Subscription Services Delivery**: Recurring delivery terms and modifications
        32. **Failed Delivery Handling**: Unclaimed package policies and resolution
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
                # Perform analysis
                analysis_results = analyze_document(document_text)

                # Create data for the bar chart
                risk_levels = {'High': 3, 'Medium': 2, 'Low': 1}
                chart_data = pd.DataFrame({
                    'Category': list(analysis_results.keys()),
                    'Risk Score': [risk_levels[result['risk_level']] for result in analysis_results.values()],
                    'Risk Level': [result['risk_level'] for result in analysis_results.values()]
                })

                # Display bar chart
                st.markdown("### Risk Assessment Overview")
                chart = st.bar_chart(
                    data=chart_data.set_index('Category')['Risk Score'],
                    height=400
                )

                # Display detailed results in expandable sections
                st.markdown("### Detailed Analysis")
                for category in ANALYSIS_CATEGORIES:
                    result = analysis_results[category]
                    with st.expander(f"{category} - {result['risk_level']} Risk"):
                        st.markdown(show_risk_level(result['risk_level']), unsafe_allow_html=True)
                        st.markdown("**Findings:**")
                        st.write(result['findings'])

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