import streamlit as st
import pandas as pd
import re
from collections import Counter
import json

# محاولة استيراد مكتبة جوجل
try:
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Please install 'google-generativeai'")

st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("🚀 Operations Bridge Management System")

# --- دالة تنظيف الأعمدة (عامة) ---
def clean_cols(df):
    df.columns = [str(c).strip().lower().replace("_", "").replace("-", "").replace(" ", "") for c in df.columns]
    return df

# --- القائمة الجانبية للتحكم ---
st.sidebar.header("⚙️ Bridge Selector")
bridge_option = st.sidebar.selectbox("اختر نوع البريدج:", ["OTP Bridge", "Store Closure Bridge"])

# --- قسم الـ OTP Bridge ---
def run_otp_bridge():
    st.subheader("📊 OTP Bridge (Hour-by-Hour)")
    primary_file = st.file_uploader("Upload Primary Data", type=["csv", "xlsx"], key="otp_primary")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["csv", "xlsx"], key="otp_secondary")
    
    # [هنا تضع منطق الـ OTP Bridge الذي أرسلته سابقاً بالكامل]
    st.info("OTP Bridge Engine is ready. Integrate your processing logic here.")

# --- قسم الـ Store Closure Bridge ---
def run_store_closure():
    st.subheader("🔒 Store Closure Bridge Analysis")
    uploaded_file = st.file_uploader("Upload Store Closure Raw Data (CSV)", type=["csv"], key="closure_file")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df = clean_cols(df)
        
        st.write("### 📂 معاينة البيانات:")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Closure Report"):
            # منطق تحليل الـ Closure
            summary = df.groupby('issue')['closuremins'].agg(['sum', 'count']).reset_index()
            st.write("### 📝 تحليل الغلق:")
            st.table(summary)
            
            # هنا يمكنك إضافة الـ Prompt الخاص بالذكاء الاصطناعي للـ Closure
            st.success("التقرير جاهز (سيتم ربط النتائج بالصيغة التي طلبتها في الخطوة التالية).")

# --- توجيه التنفيذ ---
if bridge_option == "OTP Bridge":
    run_otp_bridge()
elif bridge_option == "Store Closure Bridge":
    run_store_closure()

# --- إعدادات الذكاء الاصطناعي (موحدة) ---
with st.sidebar:
    st.markdown("---")
    st.header("🔮 AI Configuration")
    enable_ai = st.checkbox("Enable Gemini AI Analysis")
    ai_key = st.text_input("Gemini API Key:", type="password")
