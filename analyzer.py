import anthropic
import os
import streamlit as st

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
    Analyze the following Terms and Conditions document for potential concerns in each category. 
    For each category, provide:
    1. Risk Level (High/Medium/Low)
    2. Specific findings and concerns

    Document text:
    {text}

    Please analyze for these categories:
    {', '.join(ANALYSIS_CATEGORIES)}

    For each category, consider:
    - Clarity and completeness of terms
    - Potential risks to users
    - Compliance with standard practices
    - Fairness and reasonableness
    - Delivery terms and conditions (if applicable)
    - International considerations
    - Consumer protection requirements

    Format the response as a Python dictionary with categories as keys and values as dictionaries containing 'risk_level' and 'findings'.
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
                if "high risk" in content.lower():
                    risk_level = "High"
                elif "medium risk" in content.lower():
                    risk_level = "Medium"
                else:
                    risk_level = "Low"

                findings = content.split(category)[1].split("\n")[0]

                analysis_results[category] = {
                    'risk_level': risk_level,
                    'findings': findings.strip()
                }
            else:
                analysis_results[category] = {
                    'risk_level': 'Low',
                    'findings': 'No specific concerns identified.'
                }

        return analysis_results
    except Exception as e:
        st.error(f"Error parsing Claude's response: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed'} for cat in ANALYSIS_CATEGORIES}