import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .stProgress > div > div > div > div {
            background-color: #FF4B4B;
        }
        .risk-high {
            color: #FF4B4B;
            font-weight: bold;
        }
        .risk-medium {
            color: #FFA500;
            font-weight: bold;
        }
        .risk-low {
            color: #00CC00;
            font-weight: bold;
        }
        .risk-none {
            color: #0066FF;
            font-weight: bold;
        }
        .section-header {
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
            margin-bottom: 10px;
            color: #262730;
        }
        .item-container {
            margin: 2px 0;
            padding: 0;
        }
        .findings-text {
            margin-top: 5px;
            font-size: 14px;
            color: #666;
            line-height: 1.4;
        }
        .summary-box {
            padding: 10px 15px;
            border-radius: 5px;
            background-color: #f8f9fa;
            margin-bottom: 20px;
        }
        div.stExpander {
            margin-bottom: 3px;
        }
        /* Remove extra space after title */
        .st-emotion-cache-1629p8f h1 {
            margin-bottom: 0.5rem;
        }
        
        /* Hide all Streamlit warning and error elements */
        .st-emotion-cache-16txtl3, 
        .st-emotion-cache-r421ms,
        .stException,
        div[data-baseweb="notification"],
        div[class*="stAlert"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

def show_risk_indicator(risk_level):
    if risk_level == "High":
        return '🔴'  # Red circle for high risk
    elif risk_level == "Medium":
        return '🟡'  # Yellow circle for medium risk
    elif risk_level == "Low":
        return '🟢'  # Green circle for low risk
    else:
        return '🔵'  # Blue circle for not mentioned