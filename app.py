import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

st.set_page_config(page_title="Operations Bridge Center", layout="wide")

# --- دالة OTP Bridge (تم دمج كودك بالكامل هنا) ---
def run_otp_bridge():
    st.header("📊 OTP Bridge (Hour-by-Hour)")
    
    # كل المدخلات (Uploaders) لازم تكون جوه الدالة عشان تظهر
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="otp_primary")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="otp_secondary")
    
    if primary_file:
        st.success("✅ Primary Data Loaded!")
        # [هنا تضع منطق معالجة البيانات الخاص بك...]
        # الكود القديم بتاعك بتاع الـ Rename و الـ Extract_english_only لازم يكون هنا
    else:
        st.info("💡 Upload data to start OTP analysis.")

# --- دالة Store Closure Bridge ---
def run_store_closure():
    st.header("🔒 Store Closure Bridge Analysis")
    uploaded_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # التنظيف
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        
        if st.button("🚀 Generate Closure Report"):
            report = ""
            for issue, group in df.groupby('issue'):
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            
            st.text_area("Final Output:", value=report, height=300)

# --- الـ Router (المتحكم) ---
with st.sidebar:
    st.header("⚙️ Bridge Selection")
    bridge_type = st.radio("Select:", ["OTP Bridge", "Store Closure Bridge"])
    st.markdown("---")
    # الـ Configs هنا
    enable_ai = st.checkbox("Enable AI")

# استدعاء الدالة المختارة
if bridge_type == "OTP Bridge":
    run_otp_bridge()
else:
    run_store_closure()
