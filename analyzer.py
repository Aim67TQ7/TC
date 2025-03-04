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
    Analyze the following Terms and Conditions document, focusing on identifying unusual or special terms that deviate from standard T&Cs.

    For each category, evaluate and provide:
    1. Risk Level based on the following criteria:
       - High Risk: Unusual clauses, special requirements, or terms that significantly deviate from standard T&Cs
       - Medium Risk: Terms that contain specific requirements or conditions that warrant attention
       - Low Risk: Standard, commonly found terms
       - None: Topics not mentioned in the document
    2. Specific findings highlighting any unusual terms, special requirements, or notable deviations from standard T&Cs

    Document text:
    {text}

    Please analyze for these categories:
    {', '.join(ANALYSIS_CATEGORIES)}

    For each category, consider:
    - Unusual or non-standard terms
    - Special requirements or conditions
    - Deviations from common industry practices
    - Region-specific or unusual requirements
    - Novel or unique clauses
    - Complex or intricate conditions

    Format the response as a Python dictionary with categories as keys and values as dictionaries containing 'risk_level' and 'findings'.
    Focus on highlighting what makes certain terms unusual or special rather than just general concerns.
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
                # Determine risk level based on presence of unusual terms
                if "unusual" in content.lower() or "special requirement" in content.lower() or "significant deviation" in content.lower():
                    risk_level = "High"
                elif "specific requirement" in content.lower() or "notable condition" in content.lower():
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
                    'risk_level': 'None',
                    'findings': 'Not mentioned in document.'
                }

        return analysis_results
    except Exception as e:
        st.error(f"Error parsing Claude's response: {str(e)}")
        return {cat: {'risk_level': 'Error', 'findings': 'Analysis failed'} for cat in ANALYSIS_CATEGORIES}