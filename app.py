import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("📊 Operations Bridge Management System")

# إعدادات الـ AI في الـ Sidebar (موحدة للكل)
with st.sidebar:
    st.header("🔮 Global Settings")
    enable_ai = st.checkbox("Enable Gemini AI Analysis")
    ai_key = st.text_input("Gemini API Key:", type="password")

# --- استخدام الـ Tabs بدلاً من الـ Radio لتجنب اختفاء الواجهة ---
tab1, tab2 = st.tabs(["📊 OTP Bridge", "🔒 Store Closure Bridge"])

# --- Tab 1: OTP Bridge ---
with tab1:
    st.header("OTP Bridge (Hour-by-Hour Forecast Matcher)")
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="primary_otp")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary_otp")
    
    report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"], key="otp_type")
    total_volume = st.number_input("Enter Total Orders Volume:", min_value=1, value=10000, key="otp_vol")

    if primary_file:
        st.success("✅ OTP Data Loaded Successfully!")
        # [هنا تضع منطق الـ OTP الخاص بك...]

# --- Tab 2: Store Closure Bridge ---
with tab2:
    st.header("Store Closure Bridge Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        # التنظيف الأساسي
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        
        st.write("### Data Preview:")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Closure Report", key="gen_closure"):
            report = "**Store Closure Report**\n\n"
            for issue, group in df.groupby('issue'):
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            st.text_area("Final Output:", value=report, height=300)
