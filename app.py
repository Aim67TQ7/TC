import streamlit as st
import anthropic
import os
from typing import Dict, Any

def analyze_tc_document(text: str) -> Dict[str, Any]:
    """Analyze T&C document using Claude."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = """
    Analyze this Terms & Conditions document. Focus on:
    1. Financial terms and obligations
    2. Unusual or non-standard requirements
    3. Important legal clauses

    Format your response exactly as:

    RISK LEVEL: [High/Medium/Low]

    KEY FINDINGS:
    - [Brief bullet points of important findings]

    FINANCIAL TERMS:
    "[Quote the exact financial terms]"

    UNUSUAL REQUIREMENTS:
    "[Quote any unusual or non-standard terms]"

    RECOMMENDATIONS:
    - [Action items or points to review]
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": f"{prompt}\n\nDocument:\n{text}"}]
        )

        return {
            'success': True,
            'analysis': response.content[0].text if response.content else "Analysis failed"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    st.title("T&C Document Analyzer")
    st.markdown("Upload your Terms & Conditions document for quick analysis")

    uploaded_file = st.file_uploader("Upload document (PDF, DOCX, or TXT)", 
                                   type=["pdf", "docx", "txt"])

    if uploaded_file:
        # Simple text extraction based on file type
        try:
            document_text = uploaded_file.getvalue().decode('utf-8')
        except UnicodeDecodeError:
            st.error("Could not read the document. Please ensure it's a text file.")
            return

        if st.button("Analyze Document"):
            with st.spinner("Analyzing document..."):
                result = analyze_tc_document(document_text)

                if result['success']:
                    st.markdown(result['analysis'])
                else:
                    st.error(f"Analysis failed: {result['error']}")

if __name__ == "__main__":
    main()