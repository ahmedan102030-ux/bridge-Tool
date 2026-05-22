import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("📊 Operations Bridge Management System")

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("⚙️ Bridge Selection")
    bridge_type = st.radio("Select Bridge:", ["OTP Bridge", "Store Closure Bridge"])
    st.markdown("---")

# --- منطق الـ OTP Bridge (نسخة كاملة من كودك) ---
if bridge_type == "OTP Bridge":
    st.header("📊 OTP Bridge (Hour-by-Hour Forecast Matcher)")
    
    # كل المدخلات القديمة بتاعتك
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="primary")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary")
    report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"])
    
    if report_type == "Daily Bridge":
        total_volume = st.number_input("Enter Total Shift/Day Orders Volume:", min_value=1, value=10000)
    else:
        total_volume = st.number_input("Enter Total Weekly Orders Volume:", min_value=1, value=70000)

    # --- حط هنا الـ Logic بتاع الـ OTP بتاعك كاملاً (الـ Functions والـ if primary_file) ---
    if primary_file:
        st.success("✅ OTP Data is ready. Proceed with your analysis logic.")
        # هنا هتحط كود المعالجة القديم بتاعك كله

# --- منطق الـ Store Closure Bridge ---
else:
    st.header("🔒 Store Closure Bridge Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        # تنظيف الأعمدة
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        
        st.write("### 📂 Data Preview:")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Closure Report"):
            report = "**Store Closure Report**\n\n"
            grouped = df.groupby('issue')
            for issue, group in grouped:
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            
            st.text_area("Final Output:", value=report, height=300)
