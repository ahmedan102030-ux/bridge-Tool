import streamlit as st
import pandas as pd
import re
from collections import Counter
import requests
import json

st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Forecast Matcher)")

with st.sidebar:
    st.header("AI Configuration")
    enable_ai = st.checkbox("Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="AIzaSy...")
    if enable_ai and not ai_key:
        st.warning("Please provide an API key.")

st.subheader("1. Upload Primary Data")
primary_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="primary")

st.subheader("2. Upload Forecast Data")
secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary")

st.write("---")
st.subheader("Configuration")
report_type = st.radio("Select Report Type:", ["Daily Bridge", "Weekly Bridge"])
total_volume = st.number_input("Total Orders Volume:", min_value=1, value=10000, step=1)

def clean_input(text):
    txt_str = str(text).strip()
    if txt_str in ["", "nan", "None", "0", "0.0"]: return "Others"
    cleaned = re.sub(r'[\u0600-\u06FF]', '', txt_str)
    cleaned = " ".join(cleaned.split())
    cl_lower = cleaned.lower()
    if "order" in cl_lower: return "Order Count Issue"
    if "net" in cl_lower or "network" in cl_lower: return "Net Issue"
    if "multi" in cl_lower: return "Multi Package"
    if "late" in cl_lower: return "Late Delivery"
    if "da" in cl_lower or "shortage" in cl_lower: return "DA Issue"
    return cleaned if cleaned else "Others"

def get_ai_context(summary_df, total_vol, forecast_str, key):
    data_list = []
    for row in summary_df.itertuples():
        data_list.append({"Issue": row.sub_reason, "Count": row.Count})
    
    prompt = f"Analyze these logistics issues and write a 2-line context for each: {json.dumps(data_list)}. Forecast: {forecast_str}. Return JSON only."
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    try:
        res = requests.post(url, params={"key": key}, json={"contents": [{"parts": [{"text": prompt}]}]})
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text']
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)
    except Exception as e:
        st.sidebar.error(f"AI Error: {e}")
    return {}

if primary_file:
    df = pd.read_excel(primary_file) if primary_file.name.endswith('.xlsx') else pd.read_csv(primary_file)
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "") for c in df.columns]
    
    # Smart detection for the Sub-reason column
    target_col = None
    for col in df.columns:
        if "sub" in col or "reason" in col:
            target_col = col
            break
            
    if target_col:
        df = df.rename(columns={target_col: "sub_reason"})
        df["sub_reason"] = df["sub_reason"].apply(clean_input)
        
        if st.button("Generate Report"):
            summary = df.groupby("sub_reason").size().reset_index(name="Count")
            ai_resp = get_ai_context(summary, total_volume, "N/A", ai_key) if enable_ai else {}
            
            st.subheader("Generated Report")
            out = f"Operational Bridge Report\nTotal Volume: {total_volume:,}\n\n"
            for row in summary.itertuples():
                out += f"- {row.sub_reason}: {row.Count} cases. "
                out += f"Context: {ai_resp.get(row.sub_reason, 'Standard operational fluctuation.')}\n"
            st.text_area("Final Output:", value=out, height=400)
    else:
        st.error(f"Could not find a 'Sub-reason' column. Found: {list(df.columns)}")
