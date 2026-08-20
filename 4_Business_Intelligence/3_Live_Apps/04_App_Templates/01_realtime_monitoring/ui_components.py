"""Reusable UI Components"""
import streamlit as st

def render_kpi_card(title: str, value: str, alert=False):
    if alert:
        st.markdown(f"""
        <div style="background-color: #FEE2E2; padding: 20px; border-radius: 10px; border-left: 5px solid #DC2626;">
            <p style="color: #6B7280; font-size: 14px; margin: 0;">{title}</p>
            <h2 style="color: #DC2626; margin: 10px 0;">{value}</h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.metric(label=title, value=value)

def apply_custom_theme():
    st.markdown("""
    <style>
    .stApp {
        background-color: #F9FAFB;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
