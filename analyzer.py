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

def analyze_document(text):
    # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
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
    - Specific phrases containing special requirements
    - Text showing deviations from common industry practices
    - Unique or complex conditions
    - Region-specific requirements
    - Novel clauses or unusual stipulations

    Format the response as a Python dictionary with categories as keys and values as dictionaries containing:
    - 'risk_level': The assessed risk level
    - 'findings': Analysis of why terms are unusual/special
    - 'quoted_phrases': List of exact phrases from the document that triggered the risk assessment
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
                # Extract quotes and determine risk level
                result_section = content.split(category)[1].split(next((c for c in ANALYSIS_CATEGORIES if c.lower() in content.lower() and c != category), ""))[0]

                # Look for quoted text
                quoted_phrases = []
                quotes = re.findall(r'"([^"]*)"', result_section)
                if quotes:
                    quoted_phrases = quotes

                # Determine risk level based on content
                if (any(term in result_section.lower() for term in ['unusual', 'unique', 'special requirement', 'significant deviation', 'non-standard'])) or quoted_phrases:
                    risk_level = "High"
                elif any(term in result_section.lower() for term in ['specific requirement', 'notable condition', 'requires attention']):
                    risk_level = "Medium"
                else:
                    risk_level = "Low"

                findings = result_section.strip()

                analysis_results[category] = {
                    'risk_level': risk_level,
                    'findings': findings,
                    'quoted_phrases': quoted_phrases if quoted_phrases else []
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