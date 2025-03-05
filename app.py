import streamlit as st
import os
from utils import extract_text_from_file, generate_pdf_report, generate_csv_report
from analyzer import (
    analyze_document, 
    ANALYSIS_CATEGORIES, 
    COMPLIANCE_FRAMEWORKS,
    check_compliance
)
from styles import apply_custom_styles, show_risk_indicator
import anthropic

def chat_with_ai(text: str, question: str) -> str:
    """Have a conversation about specific terms in the document."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""
    Given this Terms and Conditions document, please answer the following question:

    Document:
    {text}

    Question: {question}

    Provide a clear, concise answer based on the document content.
    If the information isn't found in the document, clearly state that.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text if response.content else "Sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error: {str(e)}"

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

                # Validate analysis results
                if not analysis_results or not isinstance(analysis_results, dict):
                    st.error("Failed to analyze document. Please try again.")
                    return

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

        # Add Compliance Check section
        st.markdown("### Compliance Analysis")

        # Select compliance frameworks to check
        selected_frameworks = st.multiselect(
            "Select compliance frameworks to check against:",
            list(COMPLIANCE_FRAMEWORKS.keys()),
            default=["GDPR"]
        )

        if st.button("Check Compliance"):
            for framework in selected_frameworks:
                with st.spinner(f"Checking {framework} compliance..."):
                    compliance_results = check_compliance(document_text, framework)

                    # Display compliance results
                    st.subheader(f"{framework} Compliance")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Compliance Score", f"{compliance_results['score']}%")
                    with col2:
                        status_color = {
                            "Compliant": "green",
                            "Partially Compliant": "orange",
                            "Non-Compliant": "red"
                        }.get(compliance_results['status'], "gray")
                        st.markdown(f"Status: :{status_color}[{compliance_results['status']}]")

                    with st.expander("Detailed Findings"):
                        st.markdown("**Key Findings:**")
                        st.write(compliance_results['findings'])
                        st.markdown("**Gaps Identified:**")
                        st.write(compliance_results['gaps'])
                        st.markdown("**Recommendations:**")
                        st.write(compliance_results['recommendations'])

        # Add AI Conversation section
        st.markdown("### Ask Questions About the Document")
        user_question = st.text_input("What would you like to know about this document?")

        if user_question and st.button("Ask AI"):
            with st.spinner("Getting answer..."):
                answer = chat_with_ai(document_text, user_question)
                st.markdown("**Answer:**")
                st.write(answer)

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