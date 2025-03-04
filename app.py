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

                # Count items by risk level
                risk_counts = {
                    "High": sum(1 for r in analysis_results.values() if r['risk_level'] == "High"),
                    "Medium": sum(1 for r in analysis_results.values() if r['risk_level'] == "Medium")
                }

                # Generate summary message
                if risk_counts["High"] == 0 and risk_counts["Medium"] == 0:
                    st.markdown("""
                        <div class="summary-box">
                        ✅ I reviewed the document and found no unusual terms or special requirements that deviate from standard T&Cs.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    summary = f"""
                        <div class="summary-box">
                        ⚠️ I found {risk_counts["Medium"]} item{"s" if risk_counts["Medium"] != 1 else ""} with specific requirements to review
                        {f' and {risk_counts["High"]} unusual term{"s" if risk_counts["High"] != 1 else ""} that significantly deviate{"s" if risk_counts["High"] == 1 else ""} from standard T&Cs' if risk_counts["High"] > 0 else ''}.
                        </div>
                    """
                    st.markdown(summary, unsafe_allow_html=True)

                # Define sections
                sections = {
                    "Core Terms": ANALYSIS_CATEGORIES[:14],
                    "Quality & Compliance": ANALYSIS_CATEGORIES[14:22],
                    "Delivery & Fulfillment": ANALYSIS_CATEGORIES[22:]
                }

                # Only show sections with concerns
                for section_name, categories in sections.items():
                    # Filter categories with medium or high risk in this section
                    risky_categories = [cat for cat in categories 
                                      if analysis_results[cat]['risk_level'] in ["High", "Medium"]]

                    if risky_categories:  # Only show section if it has items of concern
                        st.markdown(f"### {section_name}")

                        for category in risky_categories:
                            result = analysis_results[category]
                            with st.expander(f"{show_risk_indicator(result['risk_level'])} {category}"):
                                st.markdown("**Findings:**")
                                st.write(result['findings'])

                                # Display quoted phrases if they exist
                                if result['quoted_phrases']:
                                    st.markdown("**Unusual Terms Found:**")
                                    for phrase in result['quoted_phrases']:
                                        # Color code based on type (red for financial, yellow for unusual)
                                        color = "#FF4B4B" if phrase['is_financial'] else "#FFA500"
                                        st.markdown(f"""
                                            <div style='color: {color}; margin-left: 20px;'>
                                            • {phrase['text']}
                                            </div>
                                        """, unsafe_allow_html=True)

                                risk_explanations = {
                                    "High": "⚠️ Contains terms with significant financial impact or unusual requirements",
                                    "Medium": "⚠️ Contains specific requirements or conditions to review"
                                }
                                st.markdown(f"**Risk Level:** {result['risk_level']} - {risk_explanations[result['risk_level']]}")

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