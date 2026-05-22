import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

# إعدادات الصفحة
st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("📊 Operations Bridge Management System")

# --- 1. الإعدادات العامة (في الـ Sidebar) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    enable_ai = st.checkbox("🔮 Enable AI Analysis", value=False)
    ai_key = st.text_input("Gemini API Key:", type="password")

# --- 2. الـ Tabs (لضمان بقاء كل بريدج مستقلاً) ---
tab_otp, tab_closure = st.tabs(["📊 OTP Bridge", "🔒 Store Closure Bridge"])

# --- كود الـ OTP (كما كان يعمل عندك تماماً) ---
with tab_otp:
    st.subheader("OTP Bridge (Hour-by-Hour Forecast Matcher)")
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="primary_otp")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary_otp")
    
    # باقي كود الـ OTP الخاص بك (الـ Logic) يوضع هنا
    if primary_file:
        st.success("✅ OTP Data Loaded.")
        # ضع هنا باقي كود المعالجة والـ AI الخاص بك...

# --- كود الـ Store Closure ---
with tab_closure:
    st.subheader("Store Closure Bridge Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        # التنظيف الأساسي
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        
        if st.button("🚀 Generate Closure Report", key="gen_closure"):
            report = "**Store Closure Report**\n\n"
            for issue, group in df.groupby('issue'):
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            st.text_area("Final Output:", value=report, height=300)

# --- كود الـ AI (يعمل فقط إذا كان الـ Checkbox مفعل) ---
if enable_ai and ai_key:
    st.sidebar.success("✅ AI Engine is Ready.")
    # هنا يوضع الكود الذي يستخدم الـ AI (لن يعمل إلا إذا اخترت Enable)
elif enable_ai and not ai_key:
    st.sidebar.warning("⚠️ Enter API Key to activate AI.")
