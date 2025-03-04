import streamlit as st
import os
import pandas as pd
from utils import extract_text_from_file, generate_pdf_report, generate_csv_report
from analyzer import analyze_document, ANALYSIS_CATEGORIES
from language_utils import detect_language_sections, translate_text
from styles import apply_custom_styles, show_risk_indicator

def display_language_analysis(metadata):
    """Display language analysis information."""
    language_analysis = metadata.get('language_analysis', {})
    translation_status = metadata.get('translation_status', 'not_needed')

    if language_analysis.get('has_mixed_content'):
        if translation_status == 'completed':
            st.success("✅ Mixed language content has been translated to English for analysis")

        # Show original sections that required translation
        non_english = language_analysis.get('sections_requiring_translation', [])
        if non_english:
            with st.expander("View original non-English sections"):
                for section in non_english:
                    st.markdown(f"""
                        **Original Language**: {section['language']}
                        ```
                        {section['preview']}
                        ```
                        """)
    elif metadata.get('required_translation'):
        if translation_status == 'completed':
            st.success(f"✅ Document has been translated from {language_analysis.get('primary_language', 'non-English')} to English")

    confidence = language_analysis.get('translation_confidence', 1.0)
    if confidence < 1.0:
        st.info(f"ℹ️ Translation confidence: {confidence*100:.1f}%")

def preprocess_document(text: str) -> tuple[str, dict]:
    """Preprocess document text, including translation if needed."""
    # First analyze language composition
    language_analysis = detect_language_sections(text)
    requires_translation = language_analysis['primary_language'] != 'en' or language_analysis['has_mixed_content']

    metadata = {
        'length': len(text),
        'language_analysis': language_analysis,
        'required_translation': requires_translation,
        'translation_status': 'not_needed'
    }

    if requires_translation:
        if language_analysis['has_mixed_content']:
            st.warning("⚠️ Document contains mixed language content. Translating to English...")
            # Handle mixed content by translating non-English sections
            paragraphs = text.split('\n\n')
            translated_paragraphs = []

            # Create a progress bar for translation
            progress_bar = st.progress(0)
            total_paragraphs = len(paragraphs)

            for i, para in enumerate(paragraphs):
                if len(para.strip()) > 20:  # Only translate substantial paragraphs
                    try:
                        lang = language_analysis['sections_requiring_translation'][i]['language'] if i < len(language_analysis['sections_requiring_translation']) else 'en'
                        if lang != 'en':
                            translated_para = translate_text(para, lang)
                            translated_paragraphs.append(translated_para)
                        else:
                            translated_paragraphs.append(para)
                    except:
                        translated_paragraphs.append(para)
                else:
                    translated_paragraphs.append(para)

                # Update progress bar
                progress_bar.progress((i + 1) / total_paragraphs)

            text = '\n\n'.join(translated_paragraphs)
            st.success("✅ Mixed language content has been translated to English")

        else:
            st.warning(f"⚠️ Document appears to be in {language_analysis['primary_language']}. Translating to English...")
            text = translate_text(text, language_analysis['primary_language'])
            st.success("✅ Document has been translated to English")

        metadata['translation_status'] = 'completed'

    return text, metadata

def analyze_and_display_results(processed_text: str, metadata: dict):
    """Perform analysis and display results."""
    with st.spinner("Analyzing document..."):
        # Perform analysis
        analysis_results = analyze_document(processed_text)
        analysis_results['metadata'] = metadata

        # Validate analysis results
        if not analysis_results or not isinstance(analysis_results, dict):
            st.error("Failed to analyze document. Please try again.")
            return

        # Show document metadata and language analysis
        display_language_analysis(metadata)
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

def main():
    apply_custom_styles()

    st.title("T&C Review Agent")
    st.markdown("Upload your T&C document for comprehensive analysis across key areas of concern.")

    uploaded_file = st.file_uploader(
        "Upload your document (PDF, DOCX, or TXT) - Supports multiple languages", 
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:
        # Extract text from document
        with st.spinner("Extracting text from document..."):
            document_text = extract_text_from_file(uploaded_file)

        # Show original document preview
        with st.expander("Original Document Preview"):
            st.text_area("Original Text", document_text[:1000] + "...", height=200)

        # First step: Translation if needed
        if st.button("Step 1: Check Language & Translate if Needed"):
            processed_text, metadata = preprocess_document(document_text)

            if metadata['translation_status'] == 'completed':
                # Show translated preview
                with st.expander("Translated Document Preview"):
                    st.text_area("Translated Text", processed_text[:1000] + "...", height=200)

                # Store the processed text and metadata in session state
                st.session_state['processed_text'] = processed_text
                st.session_state['metadata'] = metadata

                st.success("Translation completed! You can now proceed with the analysis.")

            elif metadata['translation_status'] == 'not_needed':
                st.success("Document is already in English! You can proceed with the analysis.")
                st.session_state['processed_text'] = processed_text
                st.session_state['metadata'] = metadata

        # Second step: Analysis
        if st.session_state.get('processed_text') is not None:
            if st.button("Step 2: Analyze Document"):
                analyze_and_display_results(
                    st.session_state['processed_text'],
                    st.session_state['metadata']
                )

if __name__ == "__main__":
    main()