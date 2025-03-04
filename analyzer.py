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
        # Debug: Print prompt
        st.write("Debug - Analyzing document...")

        # Make API call
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        # Safely get content
        if not response or not response.content:
            st.error("No response received from Claude")
            return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}

        content = response.content[0].text if response.content else ""

        # Debug logging
        st.write("Debug - Raw Claude Response:", content[:500] + "...")

        analysis_results = {}

        # Process each category
        for category in ANALYSIS_CATEGORIES:
            try:
                # Look for section using exact markers
                section_marker = f"###{category}###"
                section_parts = content.split(section_marker)

                if len(section_parts) > 1:
                    # Get content until next section marker or end
                    section_content = section_parts[1].split("###")[0].strip()

                    # Extract components using clear markers
                    risk_match = re.search(r"RISK:\s*(High|Medium|Low|None)", section_content)
                    findings_match = re.search(r"FINDINGS:\s*(.+?)(?=QUOTES:|$)", section_content, re.DOTALL)
                    quotes_match = re.search(r"QUOTES:\s*(.+?)(?=###|$)", section_content, re.DOTALL)

                    # Process quotes
                    quoted_phrases = []
                    if quotes_match:
                        # Split by newlines and extract quoted text
                        quotes_text = quotes_match.group(1).strip()
                        quotes = re.findall(r'"([^"]*)"', quotes_text)

                        # Process each quote to identify financial terms
                        quoted_phrases = [
                            {'text': quote.strip(), 'is_financial': is_financial_term(quote)}
                            for quote in quotes
                        ]

                    # Determine risk level
                    risk_level = (
                        risk_match.group(1) if risk_match else
                        "High" if any(q['is_financial'] for q in quoted_phrases) else
                        "Medium" if quoted_phrases else
                        "Low"
                    )

                    analysis_results[category] = {
                        'risk_level': risk_level,
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

    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed', 'quoted_phrases': []} for cat in ANALYSIS_CATEGORIES}