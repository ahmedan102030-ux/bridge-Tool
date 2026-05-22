import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import google.generativeai as genai

# إعدادات الصفحة
st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("📊 Operations Bridge Management System")

# --- الإعدادات العامة (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Gemini API Key:", type="password", placeholder="AIzaSy...")

# --- تعريف الدوال (Functions الخاصة بك) ---
def extract_english_only(text):
    txt_str = str(text).strip()
    if txt_str in ["", "nan", "None", "0", "0.0"]: return "Others"
    cleaned = re.sub(r'[\u0600-\u06FF]', '', txt_str)
    cleaned = cleaned.replace("-", "").strip()
    cleaned = " ".join(cleaned.split())
    cl_lower = cleaned.lower()
    if "order count" in cl_lower or "order volume" in cl_lower: return "Order Count Issue"
    if "net issue" in cl_lower or "network" in cl_lower: return "Net Issue"
    if "multi package" in cl_lower: return "Multi Package Count"
    if "customer later" in cl_lower: return "Customer Later Arrival"
    if "late delivery" in cl_lower: return "Late Delivery"
    if "parking" in cl_lower: return "Parking Issue"
    if "wrong scan" in cl_lower: return "Wrong Scan"
    if "da issue" in cl_lower or "shortage" in cl_lower: return "DA Issue"
    return cleaned if cleaned else "Others"

def generate_standard_context(reason, count, total_vol, hours_list, forecast_df):
    real_percentage = (count / total_vol) * 100
    hour_counts = Counter(hours_list)
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    time_periods = []
    if any(0 <= h <= 6 for h in hours_list): time_periods.append("midnight/early morning")
    if any(7 <= h <= 15 for h in hours_list): time_periods.append("midday peaks")
    if any(16 <= h <= 23 for h in hours_list): time_periods.append("afternoon and evening shifts")
    period_str = " and ".join(time_periods) if time_periods else "various shifts"
    return f"Operational bottleneck observed during {period_str}."

def generate_bulk_ai_contexts(summary_df, total_vol, forecast_data_str, key):
    # (هنا يوضع كود الـ AI الخاص بك كما كان)
    return {}

# --- التابات ---
tab_otp, tab_closure = st.tabs(["📊 OTP Bridge", "🔒 Store Closure Bridge"])

# --- Tab 1: OTP Bridge ---
with tab_otp:
    st.subheader("1. Upload Primary Data Sheet")
    primary_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="primary_otp")
    st.subheader("2. Upload Forecast vs Actual Sheet")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary_otp")
    
    report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"], key="otp_type")
    total_volume = st.number_input("Enter Total Orders Volume:", min_value=1, value=10000, key="vol_otp")

    if primary_file:
        st.success("✅ Data Loaded.")
        if st.button("🚀 Generate Final Integrated Report", key="gen_otp_final"):
            # (هنا ضع كود المعالجة والتقرير الخاص بالـ OTP الخاص بك)
            st.write("Generating OTP Report...")

# --- Tab 2: Store Closure Bridge ---
with tab_closure:
    st.subheader("Store Closure Data Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        df.columns = [str(c).strip().lower().replace("_", "").replace(" ", "") for c in df.columns]
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Closure Report", key="gen_closure_final"):
            report = "**Store Closure Report**\n\n"
            for issue, group in df.groupby('issue'):
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            st.text_area("Final Output:", value=report, height=300)
