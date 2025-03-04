import anthropic
import os
import streamlit as st
import re

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

def is_financial_term(phrase):
    financial_keywords = [
        'fee', 'cost', 'price', 'payment', 'charge', 'refund', 'credit',
        'billing', 'subscription', 'money', 'financial', 'dollar', 'rate',
        'expense', 'pay', 'compensation', 'penalty', 'fine'
    ]
    return any(keyword in phrase.lower() for keyword in financial_keywords)

def analyze_document(text):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""
    Analyze the following Terms and Conditions document, focusing on identifying unusual or special terms that deviate from standard T&Cs.

    For each category, evaluate and provide:
    1. Risk Level based on the following criteria:
       - High Risk: Unusual clauses, special requirements, or terms that significantly deviate from standard T&Cs
       - Medium Risk: Terms that contain specific requirements or conditions that warrant attention
       - Low Risk: Standard, commonly found terms
       - None: Topics not mentioned in the document
    2. Extract and quote the exact phrases that are unusual or contain special requirements
    3. Explain why these specific phrases are considered unusual or special

    Document text:
    {text}

    Please analyze for these categories:
    {', '.join(ANALYSIS_CATEGORIES)}

    For each category, identify:
    - Direct quotes of unusual or non-standard terms
    - Specific phrases containing special requirements, especially those with financial implications
    - Text showing deviations from common industry practices
    - Unique or complex conditions
    - Region-specific requirements
    - Novel clauses or unusual stipulations

    Format each quoted phrase on a new line with a brief explanation of why it's unusual or important.
    Ensure financial terms are clearly identified for special highlighting.
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1500,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    try:
        content = response.content[0].text
        analysis_results = {}
        for category in ANALYSIS_CATEGORIES:
            if category.lower() in content.lower():
                result_section = content.split(category)[1].split(next((c for c in ANALYSIS_CATEGORIES if c.lower() in content.lower() and c != category), ""))[0]

                # Extract quotes and their types
                quoted_phrases = []
                quotes = re.findall(r'"([^"]*)"', result_section)

                # Process each quote to determine if it's financial
                processed_quotes = []
                for quote in quotes:
                    processed_quotes.append({
                        'text': quote.strip(),
                        'is_financial': is_financial_term(quote)
                    })

                # Determine risk level based on content and quotes
                if processed_quotes and any(q['is_financial'] for q in processed_quotes):
                    risk_level = "High"
                elif processed_quotes:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"

                findings = result_section.strip()

                analysis_results[category] = {
                    'risk_level': risk_level,
                    'findings': findings,
                    'quoted_phrases': processed_quotes
                }
            else:
                analysis_results[category] = {
                    'risk_level': 'None',
                    'findings': 'Not mentioned in document.',
                    'quoted_phrases': []
                }

        return analysis_results
    except Exception as e:
        st.error(f"Error parsing Claude's response: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}