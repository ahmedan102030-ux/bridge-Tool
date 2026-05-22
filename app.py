import streamlit as st
import pandas as pd
import re
from collections import Counter
import json

# Official Google Generative AI library
try:
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Please add 'google-generativeai' to your requirements.txt file on GitHub!")

st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Hour-by-Hour Forecast Matcher)")

with st.sidebar:
    st.header("⚙️ AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False, 
                            help="Turn on to get deep AI justifications.")
    ai_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="AIzaSy...")
    if enable_ai and not ai_key:
        st.warning("⚠️ Please provide an API key.")

st.subheader("1. Upload Primary Data Sheet")
primary_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="primary")

st.subheader("2. Upload Forecast vs Actual Sheet")
secondary_file = st.file_uploader("Upload Forecast Sheet", type=["xlsx", "csv"], key="secondary")

st.write("---")
st.subheader("🧮 Operational Volume & Report Configuration")
report_type = st.radio("Select Bridge Report Type:", ["Daily Bridge", "Weekly Bridge"])

if report_type == "Daily Bridge":
    total_volume = st.number_input("Enter Total Shift/Day Orders Volume:", min_value=1, value=10000, step=1)
else:
    total_volume = st.number_input("Enter Total Weekly Orders Volume:", min_value=1, value=70000, step=1)

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

    if "order count" in reason.lower():
        peak_parts = [f"Hour {h} had {c} cases" for h, c in sorted_hours[:3]]
        ctx = f"This driver impacted {real_percentage:.2f}% of our total volume. Disruptions concentrated heavily during {period_str} ({', '.join(peak_parts)})."
        return ctx
    elif "net" in reason.lower():
        return f"Network connectivity constraints registered across {period_str}, holding a minor share against total dispatched volume."
    elif "multi" in reason.lower():
        return f"Delays related to multiple package orders, appearing consistently in the {period_str}."
    elif count <= 2:
        return f"Isolated case recorded during the {hours_list[0]}:00 shift."
    else:
        return f"Observed operational bottleneck during {period_str}."

def generate_bulk_ai_contexts(summary_df, total_vol, forecast_data_str, key):
    input_data = []
    for row in summary_df.itertuples():
        real_percentage = (row.Count / total_vol) * 100
        input_data.append({"Issue": row.Sub_reason, "Cases": row.Count, "Impact": f"{real_percentage:.2f}%"})
        
    prompt = f"Expert Logistics Manager report context. Write a 2-line context for each issue: {json.dumps(input_data)}. Forecast Data: {forecast_data_str}. Output: JSON only."
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        st.sidebar.error(f"Gemini AI Error: {e}")
    return {}

if primary_file:
    df = pd.read_excel(primary_file) if primary_file.name.endswith('.xlsx') else pd.read_csv(primary_file)
    rename_dict = {}
    for col in df.columns:
        c = str(col).strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        if "date" in c: rename_dict[col] = "Date"
        elif "hour" in c or "hr" in c: rename_dict[col] = "Hour_Index"
        elif "sub" in c or "reason" in c: rename_dict[col] = "Sub_reason"
    df = df.rename(columns=rename_dict)
    
    if "Sub_reason" in df.columns:
        df['Sub_reason'] = df['Sub_reason'].apply(extract_english_only)
    else:
        df['Sub_reason'] = "Others"

    if st.button("🚀 Generate Final Integrated Report"):
        summary_data = df.groupby("Sub_reason").size().reset_index(name="Count")
        ai_responses = generate_bulk_ai_contexts(summary_data, total_volume, "N/A", ai_key) if enable_ai else {}
        
        report_text = f"Operational Bridge Report ({report_type})\nTotal Volume: {total_volume:,}\n\n"
        for _, row in summary_data.iterrows():
            context = ai_responses.get(row.Sub_reason, "Standard operational fluctuation.")
            report_text += f"- {row.Sub_reason}: {row.Count} cases. Context: {context}\n"
            
        st.subheader("📋 Generated Bridge Report")
        st.text_area("Final Output:", value=report_text, height=400)
