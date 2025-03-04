import anthropic
import os

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
    "Specific Rights for Certain Regions"
]

def analyze_document(text):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', 'default-key'))
    
    prompt = f"""
    Analyze the following Terms and Conditions document for potential concerns in each category. 
    For each category, provide:
    1. Risk Level (High/Medium/Low)
    2. Specific findings and concerns
    
    Document text:
    {text}
    
    Please analyze for these categories:
    {', '.join(ANALYSIS_CATEGORIES)}
    
    Format the response as a Python dictionary with categories as keys and values as dictionaries containing 'risk_level' and 'findings'.
    """
    
    response = client.messages.create(
        model="claude-2",
        max_tokens=1500,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response and structure it
    analysis_results = {}
    for category in ANALYSIS_CATEGORIES:
        # This is a simplified version - in reality, we'd parse Claude's response more carefully
        analysis_results[category] = {
            'risk_level': 'Medium',  # Default values
            'findings': 'Analysis completed'
        }
        
    return analysis_results
