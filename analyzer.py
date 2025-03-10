import os
import requests
import streamlit as st
import re
from typing import Dict, List, Any
import langdetect

# Constants
ANALYSIS_CATEGORIES = [
    "Introduction and Overview",
    "User Rights and Responsibilities",
    "Privacy Policy and Data Usage",
    "Payment Terms",
    "Intellectual Property Rights",
    "Limitation of Liability",
    "Termination and Suspension",
    "Dispute Resolution",
    "Amendments and Updates",
    "Governing Law",
    "Force Majeure",
    "Severability",
    "User Consent for Marketing",
    "Specific Rights for Certain Regions",
    "Quality Assurance and Performance",
    "Audits and Monitoring",
    "Regulatory Compliance",
    "Product Safety Certifications",
    "Liability for Regulatory Breaches",
    "Third-Party Audits",
    "International Standards Compliance",
    "Regulatory Violation Recourse",
    "Delivery Process and Timeframes",
    "Delivery Costs",
    "Delivery Risk and Responsibility",
    "Delayed or Failed Deliveries",
    "Delivery Location and Restrictions",
    "International Delivery",
    "Returns and Delivery Failures",
    "Acceptance of Delivery",
    "Subscription Services Delivery",
    "Failed Delivery Handling"
]

risk_levels = ['None', 'Low', 'Medium', 'High']

def detect_language(text: str) -> str:
    """Detect the language of the document."""
    try:
        return langdetect.detect(text)
    except:
        return 'en'  # Default to English if detection fails

def chunk_document(text: str, chunk_size: int = 8000) -> List[str]:
    """Split document into manageable chunks."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            chunks.append(current_chunk)
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def is_financial_term(phrase: str) -> bool:
    """Check if a phrase contains financial terms."""
    financial_keywords = [
        'fee', 'cost', 'price', 'payment', 'charge', 'refund', 'credit',
        'billing', 'subscription', 'money', 'financial', 'dollar', 'rate',
        'expense', 'pay', 'compensation', 'penalty', 'fine'
    ]
    return any(keyword in phrase.lower() for keyword in financial_keywords)

def calculate_metrics(analysis_results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate various metrics based on the analysis results."""
    total_categories = len(ANALYSIS_CATEGORIES)
    risky_categories = sum(1 for k, r in analysis_results.items() 
                          if k not in ['metrics', 'metadata'] and r.get('risk_level') in ['High', 'Medium'])

    # Count financial and unusual terms only from actual category results
    financial_terms = sum(1 for k, r in analysis_results.items()
                         if k not in ['metrics', 'metadata']
                         for q in r.get('quoted_phrases', [])
                         if q.get('is_financial', False))

    unusual_terms = sum(1 for k, r in analysis_results.items()
                       if k not in ['metrics', 'metadata']
                       for q in r.get('quoted_phrases', [])
                       if not q.get('is_financial', True))

    return {
        'complexity_score': (risky_categories / total_categories) * 100,
        'financial_impact': (financial_terms / max(1, financial_terms + unusual_terms)) * 100,
        'unusual_terms_ratio': (unusual_terms / max(1, len([k for k in analysis_results.keys() if k not in ['metrics', 'metadata']]))) * 100
    }

def analyze_document(text: str) -> Dict[str, Any]:
    """Main function to analyze the document."""
    # Check document length and language
    is_long_document = len(text) > 8000
    detected_lang = detect_language(text)
    requires_translation = detected_lang != 'en'

    if requires_translation:
        st.warning("⚠️ Document appears to be in a non-English language. Translation will be performed, which may require additional processing time for thorough analysis.")

    if is_long_document:
        st.info("📄 Document is lengthy and will be processed in chunks for optimal analysis. This may take a few moments.")
        chunks = chunk_document(text)
        # Process chunks and merge results
        all_results = []
        for i, chunk in enumerate(chunks, 1):
            st.write(f"Processing chunk {i} of {len(chunks)}...")
            chunk_results = analyze_chunk(chunk)
            all_results.append(chunk_results)
        merged_results = merge_analysis_results(all_results)

        # Add metadata
        merged_results['metadata'] = {
            'language': detected_lang,
            'length': len(text),
            'required_translation': requires_translation
        }
        return merged_results
    else:
        results = analyze_chunk(text)
        results['metadata'] = {
            'language': detected_lang,
            'length': len(text),
            'required_translation': requires_translation
        }
        return results

def analyze_chunk(text: str) -> Dict[str, Any]:
    """Analyze a chunk of text using OpenRouter API."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://replit.com",
        "X-Title": "T&C Analysis Agent"
    }

    prompt = f"""
    Analyze this Terms and Conditions document, focusing on identifying unusual or special terms that deviate from standard T&Cs.
    Pay special attention to financial terms or requirements that have monetary impact.

    For each category, provide your analysis in this EXACT format with these EXACT section markers:

    ###[Category Name]###
    RISK: [High/Medium/Low/None]
    FINDINGS: [Brief analysis explaining why terms are unusual/special]
    QUOTES: [List each unusual term in quotes, one per line]

    Example format:
    ###Payment Terms###
    RISK: High
    FINDINGS: Contains unusual fee structures and non-standard payment requirements
    QUOTES: "Monthly service fee of $99.99 non-refundable after 3 days"
    "Late payments subject to 25% compound interest"

    Document text:
    {text}

    Categories to analyze:
    {', '.join(ANALYSIS_CATEGORIES)}

    Guidelines:
    - Mark any terms involving fees, payments, or financial obligations
    - Highlight unusual requirements or non-standard conditions
    - Quote exact phrases from the document
    - Start each category with ###[Category Name]### exactly as shown
    """

    try:
        response = requests.post(
            url,
            headers=headers,
            json={
                "model": "anthropic/claude-3-sonnet",
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response.raise_for_status()
        data = response.json()

        if not data or 'choices' not in data or not data['choices']:
            st.error("Invalid response structure from API")
            return {cat: {'risk_level': 'Error', 'findings': 'Invalid response', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}

        content = data['choices'][0]['message']['content']
        return process_analysis_response(content)

    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}

def process_analysis_response(content: str) -> Dict[str, Any]:
    """Process API response and extract structured analysis results."""
    analysis_results = {}

    for category in ANALYSIS_CATEGORIES:
        try:
            section_marker = f"###{category}###"
            sections = content.split(section_marker)

            if len(sections) > 1:
                section_content = sections[1].split("###")[0].strip()

                risk_match = re.search(r"RISK:\s*(High|Medium|Low|None)", section_content)
                findings_match = re.search(r"FINDINGS:\s*(.+?)(?=QUOTES:|$)", section_content, re.DOTALL)
                quotes_match = re.search(r"QUOTES:\s*(.+?)(?=###|$)", section_content, re.DOTALL)

                quoted_phrases = []
                if quotes_match:
                    quotes_text = quotes_match.group(1).strip()
                    quotes = re.findall(r'"([^"]*)"', quotes_text)
                    quoted_phrases = [
                        {'text': quote.strip(), 'is_financial': is_financial_term(quote)}
                        for quote in quotes if quote.strip()
                    ]

                analysis_results[category] = {
                    'risk_level': risk_match.group(1) if risk_match else 'Low',
                    'findings': findings_match.group(1).strip() if findings_match else "No specific findings.",
                    'quoted_phrases': quoted_phrases
                }
            else:
                analysis_results[category] = {
                    'risk_level': 'None',
                    'findings': 'Not mentioned in document.',
                    'quoted_phrases': []
                }

        except Exception as section_error:
            st.error(f"Error processing section {category}: {str(section_error)}")
            analysis_results[category] = {
                'risk_level': 'Error',
                'findings': f'Error analyzing section: {str(section_error)}',
                'quoted_phrases': []
            }

    return analysis_results

def merge_analysis_results(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge analysis results from multiple chunks."""
    merged = {}

    # Merge all categories
    for category in ANALYSIS_CATEGORIES:
        merged[category] = {
            'risk_level': 'None',
            'findings': [],
            'quoted_phrases': []
        }

        for result in results_list:
            if category in result:
                cat_data = result[category]
                # Take highest risk level
                if risk_levels.index(cat_data.get('risk_level', 'None')) > risk_levels.index(merged[category]['risk_level']):
                    merged[category]['risk_level'] = cat_data['risk_level']

                # Combine findings
                if cat_data.get('findings') and cat_data['findings'] not in ["No specific findings.", "Not mentioned in document."]:
                    merged[category]['findings'].append(cat_data['findings'])

                # Safely merge quoted phrases
                if 'quoted_phrases' in cat_data:
                    for phrase in cat_data['quoted_phrases']:
                        if isinstance(phrase, dict) and 'text' in phrase and 'is_financial' in phrase:
                            if not any(existing['text'] == phrase['text'] for existing in merged[category]['quoted_phrases']):
                                merged[category]['quoted_phrases'].append(phrase)

        # Clean up findings
        merged[category]['findings'] = '\n'.join(merged[category]['findings']) if merged[category]['findings'] else "No specific findings."

    # Calculate metrics
    metrics = calculate_metrics(merged)
    merged['metrics'] = metrics

    return merged