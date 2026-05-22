import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

# إعداد الصفحة
st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("🚀 Operations Bridge Management System")

# --- دالة تنظيف الأعمدة العامة ---
def clean_cols(df):
    df.columns = [str(c).strip().lower().replace("_", "").replace("-", "").replace(" ", "") for c in df.columns]
    return df

# --- منطق الـ OTP Bridge (كودك الأصلي) ---
def run_otp_bridge():
    st.header("📊 OTP Bridge (Hour-by-Hour)")
    # نقلت كل كود الـ OTP بتاعك هنا
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="otp_primary")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="otp_secondary")
    
    if primary_file:
        # هنا هتحط كود المعالجة الخاص بالـ OTP اللي أنت بعته
        st.success("OTP Data loaded. Ready for processing.")

# --- منطق الـ Store Closure Bridge (الواجهة الجديدة) ---
def run_store_closure():
    st.header("🔒 Store Closure Bridge Analysis")
    uploaded_file = st.file_uploader("Upload Store Closure Raw Data", type=["csv"], key="closure_file")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df = clean_cols(df)
        
        st.write("### 📂 معاينة بيانات الغلق:")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Closure Report"):
            # تجميع البيانات حسب المشكلة
            summary = df.groupby('issue')['closuremins'].agg(['sum', 'count']).reset_index()
            st.write("### 📝 التقرير:")
            st.table(summary)
            # هنا هنربط الـ AI بالـ Prompt المخصص للـ Store Closure

# --- القائمة الجانبية (Controller) ---
with st.sidebar:
    st.header("⚙️ Bridge Selector")
    bridge_option = st.radio("اختر البريدج:", ["OTP Bridge", "Store Closure Bridge"])
    
    st.markdown("---")
    st.header("🔮 AI Config")
    enable_ai = st.checkbox("Enable AI")
    ai_key = st.text_input("Gemini API Key:", type="password")

# --- الموجه (Router) ---
if bridge_option == "OTP Bridge":
    run_otp_bridge()
else:
    run_store_closure()
