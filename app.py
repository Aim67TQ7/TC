import streamlit as st
import os
import pandas as pd
from utils import extract_text_from_file, generate_pdf_report, generate_csv_report
from analyzer import analyze_document, ANALYSIS_CATEGORIES
from styles import apply_custom_styles, show_risk_indicator

def main():
    apply_custom_styles()

    st.title("AI Analysis of Terms and Conditions")
    uploaded_file = st.file_uploader("", type=["pdf", "docx", "txt"])

    if uploaded_file:
        try:
            with st.spinner("Extracting text from document..."):
                document_text = extract_text_from_file(uploaded_file)

                if not document_text:
                    st.error("Could not extract text from the document. Please ensure it's a valid file.")
                    return

                # Show document preview
                with st.expander("Document Preview"):
                    st.text_area("", document_text[:1000] + "...", height=200)

            if st.button("Analyze Document"):
                with st.spinner("Analyzing document..."):
                    try:
                        # Perform analysis
                        analysis_results = analyze_document(document_text)

                        # Validate analysis results
                        if not analysis_results or not isinstance(analysis_results, dict):
                            st.error("We encountered an issue analyzing the document. Please try again.")
                            return

                        # Process results safely
                        for category in ANALYSIS_CATEGORIES:
                            if category not in analysis_results:
                                analysis_results[category] = {
                                    'risk_level': 'None',
                                    'findings': 'Not analyzed.',
                                    'quoted_phrases': []
                                }

                        # Show document metadata if available
                        if 'metadata' in analysis_results:
                            metadata = analysis_results['metadata']
                            if metadata.get('required_translation'):
                                st.warning("⚠️ Document is not in English. Analysis includes translation, which may affect accuracy.")

                            # Show document stats
                            doc_length = metadata.get('length', 0)
                            st.info(f"📄 Document Length: {doc_length:,} characters")

                        # Count items by risk level (excluding metrics and metadata keys)
                        risk_counts = {
                            "High": sum(1 for k, r in analysis_results.items() 
                                        if k not in ['metrics', 'metadata'] and isinstance(r, dict) and r.get('risk_level') == "High"),
                            "Medium": sum(1 for k, r in analysis_results.items() 
                                        if k not in ['metrics', 'metadata'] and isinstance(r, dict) and r.get('risk_level') == "Medium")
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

                        # Show analysis metrics if available
                        if 'metrics' in analysis_results:
                            metrics = analysis_results['metrics']
                            st.markdown("### Analysis Metrics")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Complexity Score", f"{metrics['complexity_score']:.1f}%")
                            with col2:
                                st.metric("Financial Impact", f"{metrics['financial_impact']:.1f}%")
                            with col3:
                                st.metric("Unusual Terms", f"{metrics['unusual_terms_ratio']:.1f}%")

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
                                                if cat in analysis_results and 
                                                isinstance(analysis_results[cat], dict) and
                                                analysis_results[cat].get('risk_level') in ["High", "Medium"]]

                            if risky_categories:  # Only show section if it has items of concern
                                st.markdown(f"### {section_name}")

                                for category in risky_categories:
                                    result = analysis_results[category]
                                    with st.expander(f"{show_risk_indicator(result['risk_level'])} {category}"):
                                        st.markdown("**Findings:**")
                                        st.write(result['findings'])

                                        # Display quoted phrases if they exist
                                        if result.get('quoted_phrases'):
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
                    except KeyError as ke:
                        st.warning("Processing some parts of the document analysis. Results may be partial.")
                        if 'metrics' not in analysis_results:
                            analysis_results['metrics'] = {
                                'complexity_score': 0.0,
                                'financial_impact': 0.0,
                                'unusual_terms_ratio': 0.0
                            }
                    except Exception as e:
                        st.error("An unexpected error occurred during analysis. Please try again.")
                        return

        except Exception as e:
            st.error("Error processing document. Please ensure the file is not corrupted and try again.")
            if os.getenv('REPLIT_ENVIRONMENT') == 'development':
                st.write("Debug info:", type(e).__name__, str(e))

if __name__ == "__main__":
    main()