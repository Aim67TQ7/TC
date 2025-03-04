import anthropic
import os
import streamlit as st
import re
from typing import Dict, List, Any

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

def is_financial_term(phrase: str) -> bool:
    """Check if a phrase contains financial terms."""
    financial_keywords = [
        'fee', 'cost', 'price', 'payment', 'charge', 'refund', 'credit',
        'billing', 'subscription', 'money', 'financial', 'dollar', 'rate',
        'expense', 'pay', 'compensation', 'penalty', 'fine', '$', '€', '£',
        'usd', 'eur', 'gbp', 'amount', 'fund', 'deposit', 'transaction'
    ]
    phrase_lower = phrase.lower()
    return any(keyword in phrase_lower for keyword in financial_keywords)

def chunk_document(text: str, chunk_size: int = 6500) -> List[str]:
    """Split document into smaller chunks for analysis while maintaining context.

    Uses a larger chunk size (6500 chars) to:
    - Keep related clauses together
    - Provide sufficient context for analysis
    - Balance processing efficiency
    """
    # Split into paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para)
        # Check if adding this paragraph would exceed chunk size
        if current_size + para_size > chunk_size and current_chunk:
            # Join current chunk and add to chunks
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size

    # Add the last chunk if it exists
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    # Ensure we have at least one chunk
    if not chunks:
        chunks = [text]

    return chunks

def analyze_document(text: str) -> Dict[str, Any]:
    """Analyze the document, chunking if necessary."""
    # Chunk the document regardless of size to ensure consistent analysis
    chunks = chunk_document(text)
    chunk_sizes = [len(chunk) for chunk in chunks]
    avg_chunk_size = sum(chunk_sizes) / len(chunks)

    st.info(f"""📄 Document Analysis Setup:
    - Total length: {len(text):,} characters
    - Split into {len(chunks)} chunks
    - Average chunk size: {avg_chunk_size:,.0f} characters
    - Processing chunks for thorough analysis...""")

    all_results = []
    progress_bar = st.progress(0)

    for i, chunk in enumerate(chunks):
        st.write(f"Analyzing chunk {i+1} of {len(chunks)}...")
        chunk_results = analyze_chunk(chunk)
        all_results.append(chunk_results)
        progress_bar.progress((i + 1) / len(chunks))

    # Merge results from all chunks
    merged_results = merge_analysis_results(all_results)

    # Calculate metrics
    metrics = calculate_metrics(merged_results)
    merged_results['metrics'] = metrics

    return merged_results

def analyze_chunk(text: str) -> Dict[str, Any]:
    """Analyze a single chunk of text."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""
    Analyze this Terms and Conditions document chunk thoroughly. You must identify:
    1. ANY terms that deviate from standard T&Cs
    2. ALL financial terms or requirements that have monetary impact
    3. ALL specific obligations or restrictions
    4. ANY terms that pose potential risks

    Use this EXACT format for each category:

    ###[Category Name]###
    RISK: [High/Medium/Low/None]
    FINDINGS: [Detailed explanation of why terms are unusual/concerning]
    QUOTES: [Each relevant quote from the document, one per line in quotes]

    Example output format:
    ###Payment Terms###
    RISK: High
    FINDINGS: Contains multiple non-standard payment requirements and severe penalties that significantly deviate from industry norms.
    QUOTES: "Monthly service fee of $99.99 non-refundable after 3 days"
    "Late payments subject to 25% compound interest"
    "Automatic renewal with 50% price increase without notice"

    Document chunk to analyze:
    {text}

    Categories to analyze: {', '.join(ANALYSIS_CATEGORIES)}

    Guidelines:
    - Flag ANY terms that seem unusual or deviate from standard practice
    - Mark ALL financial obligations and requirements
    - Note ALL specific requirements or restrictions
    - Include EXACT quotes from the document
    - Start each category with ###[Category Name]###
    - Be thorough - if something seems unusual, flag it
    - Pay special attention to terms with financial impact
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text if response.content else ""
        return process_analysis_response(content)

    except Exception as e:
        st.error(f"Error analyzing chunk: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed', 'quoted_phrases': []} 
                for cat in ANALYSIS_CATEGORIES}

def process_analysis_response(content: str) -> Dict[str, Any]:
    """Process Claude's response into structured analysis results."""
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
    risk_levels = ['None', 'Low', 'Medium', 'High']

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
                current_risk_idx = risk_levels.index(merged[category]['risk_level'])
                new_risk_idx = risk_levels.index(cat_data.get('risk_level', 'None'))
                if new_risk_idx > current_risk_idx:
                    merged[category]['risk_level'] = cat_data['risk_level']

                # Combine findings
                if cat_data.get('findings') and cat_data['findings'] not in ["No specific findings.", "Not mentioned in document."]:
                    merged[category]['findings'].append(cat_data['findings'])

                # Combine quoted phrases, avoiding duplicates
                if cat_data.get('quoted_phrases'):
                    seen_phrases = {(q['text'], q['is_financial']) for q in merged[category]['quoted_phrases']}
                    for phrase in cat_data['quoted_phrases']:
                        if (phrase['text'], phrase['is_financial']) not in seen_phrases:
                            merged[category]['quoted_phrases'].append(phrase)
                            seen_phrases.add((phrase['text'], phrase['is_financial']))

        # Clean up merged data
        merged[category]['findings'] = '\n'.join(merged[category]['findings']) if merged[category]['findings'] else "No specific findings."

    return merged

def calculate_metrics(analysis_results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate analysis metrics."""
    total_categories = len(ANALYSIS_CATEGORIES)
    risky_categories = sum(1 for r in analysis_results.values() 
                          if isinstance(r, dict) and r.get('risk_level') in ['High', 'Medium'])

    financial_terms = sum(1 for r in analysis_results.values() 
                         if isinstance(r, dict) and r.get('quoted_phrases')
                         for q in r.get('quoted_phrases', []) if q.get('is_financial'))

    unusual_terms = sum(1 for r in analysis_results.values()
                       if isinstance(r, dict) and r.get('quoted_phrases')
                       for q in r.get('quoted_phrases', []) if not q.get('is_financial'))

    return {
        'complexity_score': (risky_categories / total_categories) * 100,
        'financial_impact': (financial_terms / max(1, financial_terms + unusual_terms)) * 100,
        'unusual_terms_ratio': (unusual_terms / max(1, len(analysis_results))) * 100
    }