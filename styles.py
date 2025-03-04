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
            font-size: 20px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .category-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }
        .category-item {
            padding: 10px;
            border-radius: 5px;
            background-color: #F8F9FA;
            margin: 5px 0;
        }
        .findings-text {
            margin-top: 5px;
            font-size: 14px;
            color: #666;
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