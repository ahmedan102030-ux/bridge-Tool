import streamlit as st
import pandas as pd
import re
import json
import io
import google.generativeai as genai

st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Pro Version)")

# --- Helper: Create CSV Templates ---
def get_csv_template(columns):
    return pd.DataFrame(columns=columns).to_csv(index=False).encode('utf-8')

# --- Helper: Clean Text ---
def clean_sub_reason(text):
    text = str(text).strip().lower()
    # Handle variations of 'Others'
    if "other" in text or text == "" or text == "-": return "Others"
    # Unified mapping
    mapping = {"order count": "Order Count Issue", "net": "Net Issue", 
               "multi": "Multi Package Count", "late": "Late Delivery"}
    for key in mapping:
        if key in text: return mapping[key]
    return text.capitalize()

with st.sidebar:
    st.header("⚙️ Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI", value=False)
    ai_key = st.text_input("Gemini API Key:", type="password")

# --- UI: Uploaders & Templates ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Primary Data")
    st.download_button("📥 Download Primary Template", data=get_csv_template(["Date", "Hour Index", "Order ID", "Sub-reason", "Comment"]), file_name="primary_template.csv")
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="p1")

with col2:
    st.subheader("2. Forecast Data")
    st.download_button("📥 Download Forecast Template", data=get_csv_template(["Date", "Hour Index", "Forecast", "Actual"]), file_name="forecast_template.csv")
    secondary_file = st.file_uploader("Upload Forecast Data", type=["xlsx", "csv"], key="p2")

# --- Process Data ---
if primary_file:
    df = pd.read_excel(primary_file) if primary_file.name.endswith('.xlsx') else pd.read_csv(primary_file)
    # Standardize column names
    df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
    
    # Cleaning Sub-reason
    if "sub_reason" in df.columns:
        df["sub_reason"] = df["sub_reason"].apply(clean_sub_reason)
    else:
        df["sub_reason"] = "Others"

    if st.button("🚀 Generate Report"):
        summary = df.groupby("sub_reason").size().reset_index(name="Count")
        
        report = "### Operational Bridge Report\n\n"
        for _, row in summary.iterrows():
            report += f"**{row['sub_reason']}**: {row['Count']} cases.\n"
        
        st.markdown(report)
