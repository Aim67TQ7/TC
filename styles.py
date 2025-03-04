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
        .section-header {
            font-size: 20px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .result-box {
            padding: 20px;
            border-radius: 5px;
            background-color: #F8F9FA;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)

def show_risk_level(risk_level):
    if risk_level == "High":
        return '<span class="risk-high">⚠️ High Risk</span>'
    elif risk_level == "Medium":
        return '<span class="risk-medium">⚠️ Medium Risk</span>'
    else:
        return '<span class="risk-low">✓ Low Risk</span>'
