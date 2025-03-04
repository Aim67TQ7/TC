import anthropic
import os
import streamlit as st
import re
from typing import Dict, List, Any
import langdetect

def has_chinese_characters(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def detect_language_sections(text: str) -> Dict[str, Any]:
    """Analyze different sections of the document for language detection."""
    # Split into paragraphs for granular analysis
    paragraphs = text.split('\n\n')
    sections_analysis = {
        'primary_language': 'en',
        'has_mixed_content': False,
        'sections_requiring_translation': [],
        'translation_confidence': 1.0
    }

    try:
        # Check for Chinese characters first
        has_chinese = has_chinese_characters(text)
        if has_chinese:
            sections_analysis['has_mixed_content'] = True
            sections_analysis['primary_language'] = 'zh'
            sections_analysis['translation_confidence'] = 0.9

        # Detect primary language from full text
        try:
            detected_lang = langdetect.detect(text)
            if detected_lang != 'en':
                sections_analysis['primary_language'] = detected_lang
        except:
            if has_chinese:
                sections_analysis['primary_language'] = 'zh'
            else:
                sections_analysis['primary_language'] = 'en'

        # Analyze individual paragraphs
        non_english_sections = []
        paragraph_languages = set()

        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 20:  # Lower threshold to catch shorter sections
                # Check for Chinese characters first
                if has_chinese_characters(para):
                    non_english_sections.append({
                        'index': i,
                        'language': 'zh',
                        'preview': para[:100] + '...' if len(para) > 100 else para
                    })
                    paragraph_languages.add('zh')
                    continue

                try:
                    lang = langdetect.detect(para)
                    paragraph_languages.add(lang)
                    if lang != 'en':
                        non_english_sections.append({
                            'index': i,
                            'language': lang,
                            'preview': para[:100] + '...' if len(para) > 100 else para
                        })
                except:
                    continue

        sections_analysis['has_mixed_content'] = len(paragraph_languages) > 1 or has_chinese
        sections_analysis['sections_requiring_translation'] = non_english_sections
        sections_analysis['translation_confidence'] = 0.8 if has_chinese else (
            1.0 if len(paragraph_languages) == 1 else 0.9
        )

    except Exception as e:
        st.error(f"Error in language detection: {str(e)}")
        sections_analysis['translation_confidence'] = 0.5

    return sections_analysis

def translate_text(text: str, source_lang: str) -> str:
    """Translate text to English using Claude."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""
    Translate the following text from {source_lang} to English, maintaining the original formatting and structure.
    Preserve any technical terms, numbers, and special characters.

    Text to translate:
    {text}

    Provide only the translated text in your response, without any additional commentary.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text if response.content else text
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

def analyze_document(text: str) -> Dict[str, Any]:
    """Analyze the document text (assumes text is in English)."""
    # Check document length
    is_long_document = len(text) > 8000
    if is_long_document:
        st.info("📄 Document is lengthy and will be processed in chunks for optimal analysis. This may take a few moments.")
        chunks = chunk_document(text)
        all_results = []
        for i, chunk in enumerate(chunks, 1):
            st.write(f"Processing chunk {i} of {len(chunks)}...")
            chunk_results = analyze_chunk(chunk)
            all_results.append(chunk_results)
        results = merge_analysis_results(all_results)
    else:
        results = analyze_chunk(text)

    return results

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

def analyze_chunk(text: str) -> Dict[str, Any]:
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

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
        # Make API call with error handling
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as api_error:
            st.error(f"API call failed: {str(api_error)}")
            return {cat: {'risk_level': 'Error', 'findings': 'API call failed', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}

        # Process response
        if not response or not hasattr(response, 'content') or not response.content:
            st.error("Invalid response structure from Claude")
            return {cat: {'risk_level': 'Error', 'findings': 'Invalid response', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}

        content = response.content[0].text if response.content else ""

        analysis_results = process_analysis_response(content)

        # Add metadata about document processing
        analysis_results['metadata'] = {
            'language': detect_language(text),
            'length': len(text),
            'required_translation': detect_language(text) != 'en'
        }

        return analysis_results

    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}

def process_analysis_response(content: str) -> Dict[str, Any]:
    """Process Claude's response and extract structured analysis results."""
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
                if risk_levels.index(cat_data['risk_level']) > risk_levels.index(merged[category]['risk_level']):
                    merged[category]['risk_level'] = cat_data['risk_level']

                # Combine findings
                if cat_data['findings'] != "No specific findings." and cat_data['findings'] != "Not mentioned in document.":
                    merged[category]['findings'].append(cat_data['findings'])

                # Combine quoted phrases, avoiding duplicates
                seen_phrases = {(q['text'], q['is_financial']) for q in merged[category]['quoted_phrases']}
                for phrase in cat_data['quoted_phrases']:
                    if (phrase['text'], phrase['is_financial']) not in seen_phrases:
                        merged[category]['quoted_phrases'].append(phrase)
                        seen_phrases.add((phrase['text'], phrase['is_financial']))

        # Clean up merged data
        merged[category]['findings'] = '\n'.join(merged[category]['findings']) if merged[category]['findings'] else "No specific findings."

    # Calculate overall metrics
    metrics = calculate_metrics(merged)
    merged['metrics'] = metrics

    return merged

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
    financial_keywords = [
        'fee', 'cost', 'price', 'payment', 'charge', 'refund', 'credit',
        'billing', 'subscription', 'money', 'financial', 'dollar', 'rate',
        'expense', 'pay', 'compensation', 'penalty', 'fine'
    ]
    return any(keyword in phrase.lower() for keyword in financial_keywords)

def calculate_metrics(analysis_results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate various metrics based on the analysis results."""
    total_categories = len(ANALYSIS_CATEGORIES)
    risky_categories = sum(1 for r in analysis_results.values() if r['risk_level'] in ['High', 'Medium'])
    financial_terms = sum(1 for r in analysis_results.values()
                         for q in r['quoted_phrases'] if q['is_financial'])
    unusual_terms = sum(1 for r in analysis_results.values()
                       for q in r['quoted_phrases'] if not q['is_financial'])

    return {
        'complexity_score': (risky_categories / total_categories) * 100,
        'financial_impact': (financial_terms / max(1, financial_terms + unusual_terms)) * 100,
        'unusual_terms_ratio': (unusual_terms / max(1, len(analysis_results))) * 100
    }

# Constants
risk_levels = ['None', 'Low', 'Medium', 'High']