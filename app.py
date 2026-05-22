import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("📊 Operations Bridge Management System")

# --- دوال المعالجة (مشتركة) ---
def clean_cols(df):
    df.columns = [str(c).strip().lower().replace("_", "").replace("-", "").replace(" ", "") for c in df.columns]
    return df

def extract_english_only(text):
    txt_str = str(text).strip()
    if txt_str in ["", "nan", "None", "0", "0.0"]: return "Others"
    cleaned = re.sub(r'[\u0600-\u06FF]', '', txt_str)
    cleaned = cleaned.replace("-", "").strip()
    cleaned = " ".join(cleaned.split())
    cl_lower = cleaned.lower()
    # التصنيفات الأصلية اللي كنت بتستخدمها
    if "order count" in cl_lower or "order volume" in cl_lower: return "Order Count Issue"
    if "net issue" in cl_lower or "network" in cl_lower: return "Net Issue"
    if "multi package" in cl_lower: return "Multi Package Count"
    if "customer later" in cl_lower: return "Customer Later Arrival"
    if "late delivery" in cl_lower: return "Late Delivery"
    if "parking" in cl_lower: return "Parking Issue"
    if "wrong scan" in cl_lower: return "Wrong Scan"
    if "da issue" in cl_lower or "shortage" in cl_lower: return "DA Issue"
    return cleaned if cleaned else "Others"

# --- القائمة الجانبية (Controller) ---
with st.sidebar:
    st.header("⚙️ Bridge Selection")
    bridge_type = st.radio("Select Bridge:", ["OTP Bridge", "Store Closure Bridge"])
    st.markdown("---")
    st.header("🔮 AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Enter Gemini API Key:", type="password")

# --- منطق OTP Bridge (النسخة الكاملة) ---
if bridge_type == "OTP Bridge":
    st.header("📊 OTP Bridge (Hour-by-Hour Forecast Matcher)")
    
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="primary")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary")
    report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"])
    
    if report_type == "Daily Bridge":
        total_volume = st.number_input("Enter Total Shift/Day Orders Volume:", min_value=1, value=10000)
    else:
        total_volume = st.number_input("Enter Total Weekly Orders Volume:", min_value=1, value=70000)

    if primary_file:
        # هنا هتحط كود المعالجة بتاعك (الـ Rename والـ Extract والـ Generate Report)
        st.write("✅ Primary data is loaded. Proceeding with analysis...")
        # (باقي كود الـ OTP بتاعك ضعه هنا تحت هذا الشرط)

# --- منطق Store Closure Bridge ---
else:
    st.header("🔒 Store Closure Bridge Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        df = clean_cols(df)
        
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
