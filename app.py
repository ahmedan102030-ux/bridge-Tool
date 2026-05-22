import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

# إعداد الصفحة
st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("🚀 Operations Bridge Management System")

# --- الإعدادات العامة (Sidebar) ---
with st.sidebar:
    st.header("⚙️ AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Enter Gemini API Key:", type="password")

# --- إنشاء التابات ---
tab_otp, tab_closure = st.tabs(["📊 OTP Bridge", "🔒 Store Closure Bridge"])

# ==============================================================================
# --- Tab 1: OTP Bridge (الكود الخاص بك بالكامل) ---
# ==============================================================================
with tab_otp:
    st.subheader("1. Upload Primary Data Sheet")
    primary_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="primary_otp")

    st.subheader("2. Upload Forecast vs Actual Sheet")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary_otp")

    st.write("---")
    st.subheader("🧮 Operational Volume & Report Configuration")
    report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"], key="otp_type")
    
    if report_type == "Daily Bridge":
        total_volume = st.number_input("Enter Total Shift/Day Orders Volume:", min_value=1, value=10000, key="vol_daily")
    else:
        total_volume = st.number_input("Enter Total Weekly Orders Volume:", min_value=1, value=70000, key="vol_weekly")

    # (هنا يوضع باقي الكود الخاص بك: الـ functions والـ if primary_file...)
    # [ملاحظة: تأكد من استخدام key="primary_otp" و key="secondary_otp" داخل الـ file_uploader]
    if primary_file:
        st.success("✅ OTP Primary Data is loaded.")
        # ضع هنا باقي منطق المعالجة الخاص بك (الـ rename_dict, extract, etc.)

# ==============================================================================
# --- Tab 2: Store Closure Bridge (المنطق الجديد) ---
# ==============================================================================
with tab_closure:
    st.subheader("Store Closure Data Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        # تنظيف الأعمدة
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        
        st.write("### 📂 Data Preview:")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Closure Report", key="gen_closure"):
            report = "**Store Closure Report**\n\n"
            grouped = df.groupby('issue')
            for issue, group in grouped:
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            
            st.text_area("Final Output:", value=report, height=300)
