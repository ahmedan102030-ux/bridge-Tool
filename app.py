import streamlit as st
import pandas as pd
import re
from collections import Counter
import json
import io
import google.generativeai as genai

# Page Config
st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Integrated Version)")

# Template Generation Helper
def get_csv_template(columns):
    df = pd.DataFrame(columns=columns)
    return df.to_csv(index=False).encode('utf-8')

# Sidebar Config
with st.sidebar:
    st.header("⚙️ AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="AIzaSy...")

# 1. Primary Data Section
st.subheader("1. Upload Primary Data Sheet")
st.download_button("📥 Download Primary Data Template", data=get_csv_template(["Date", "Hour Index", "Sub-reason", "Comment"]), file_name="primary_data.csv", mime="text/csv")
primary_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="primary")

# 2. Forecast Data Section
st.subheader("2. Upload Forecast vs Actual Sheet")
st.download_button("📥 Download Forecast Data Template", data=get_csv_template(["Hour Index", "Forecast", "Actual"]), file_name="forecast_data.csv", mime="text/csv")
secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary")

st.write("---")
report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"])
total_volume = st.number_input("Total Orders Volume:", min_value=1, value=10000, step=1)

# Logic Functions
def extract_english_only(text):
    txt_str = str(text).strip()
    if txt_str in ["", "nan", "None", "0", "0.0"]: return "Others"
    cleaned = re.sub(r'[\u0600-\u06FF]', '', txt_str)
    cleaned = " ".join(cleaned.split())
    cl = cleaned.lower()
    if "order" in cl: return "Order Count Issue"
    if "net" in cl: return "Net Issue"
    if "multi" in cl: return "Multi Package Count"
    if "late" in cl: return "Late Delivery"
    if "da" in cl or "shortage" in cl: return "DA Issue"
    return cleaned if cleaned else "Others"

def generate_standard_context(reason, count, total_vol, hours_list):
    real_percentage = (count / total_vol) * 100
    return f"This issue impacted {real_percentage:.2f}% of volume, concentrated during hours: {list(set(hours_list))}."

def generate_bulk_ai_contexts(summary_df, total_vol, key):
    input_data = summary_df.to_dict(orient='records')
    prompt = f"Analyze these logistics issues: {json.dumps(input_data)}. Write professional context. Return JSON only."
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        res = model.generate_content(prompt)
        text = re.sub(r"^```json|```$", "", res.text.strip())
        return json.loads(text)
    except: return {}

# Main Process
if primary_file:
    df = pd.read_excel(primary_file) if primary_file.name.endswith('.xlsx') else pd.read_csv(primary_file)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    
    # Simple rename for processing
    for col in df.columns:
        if "sub" in col or "reason" in col: df = df.rename(columns={col: "Sub_reason"})
        if "hour" in col: df = df.rename(columns={col: "Hour_Index"})
    
    if "Sub_reason" not in df.columns: df["Sub_reason"] = "Others"
    df["Sub_reason"] = df["Sub_reason"].apply(extract_english_only)
    if "Hour_Index" not in df.columns: df["Hour_Index"] = 0

    if st.button("🚀 Generate Final Integrated Report"):
        summary = df.groupby("Sub_reason").agg({'Hour_Index': list, 'Sub_reason': 'count'}).rename(columns={'Sub_reason': 'Count'})
        ai_responses = generate_bulk_ai_contexts(summary.reset_index(), total_volume, ai_key) if enable_ai else {}
        
        report = f"Operational Bridge Report ({report_type})\nTotal Volume: {total_volume:,}\n\n"
        for idx, row in summary.iterrows():
            ctx = ai_responses.get(idx, generate_standard_context(idx, row['Count'], total_volume, row['Hour_Index']))
            report += f"- {idx}: {row['Count']} cases. Context: {ctx}\n"
            
        st.text_area("Final Output:", value=report, height=500)
