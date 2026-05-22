import streamlit as st
import pandas as pd
import re
from collections import Counter
import json

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Flexible & Integrated)")

# --- 2. دوال مساعدة ---
def get_csv_template(columns):
    return pd.DataFrame(columns=columns).to_csv(index=False).encode('utf-8')

def extract_english_only(text):
    txt_str = str(text).strip()
    if txt_str in ["", "nan", "None", "0", "0.0"]: return "Others"
    cleaned = re.sub(r'[\u0600-\u06FF]', '', txt_str)
    cleaned = " ".join(cleaned.replace("-", "").split())
    cl_lower = cleaned.lower()
    mapping = {"order": "Order Count Issue", "net": "Net Issue", "multi": "Multi Package", 
               "late": "Late Delivery", "parking": "Parking Issue", "wrong": "Wrong Scan", "da": "DA Issue"}
    for key, val in mapping.items():
        if key in cl_lower: return val
    return cleaned if cleaned else "Others"

# --- 3. دالة اكتشاف الأعمدة بمرونة (بدون KeyError) ---
def rename_columns_flexibly(df):
    rename_map = {}
    for col in df.columns:
        c = str(col).lower().replace("_", "").replace("-", "").replace(" ", "")
        if 'date' in c: rename_map[col] = 'Date'
        elif 'hour' in c or 'hr' in c: rename_map[col] = 'Hour Index'
        elif 'sub' in c or 'reason' in c: rename_map[col] = 'Sub-reason'
        elif 'comment' in c or 'ملاحظ' in c: rename_map[col] = 'Comment'
    return df.rename(columns=rename_map)

# --- 4. واجهة المستخدم ---
with st.sidebar:
    st.header("⚙️ Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis")
    ai_key = st.text_input("Gemini API Key:", type="password")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Primary Data")
    st.download_button("📥 Download Template", get_csv_template(["Date", "Hour Index", "Order", "DSP_Bridge_Sub_Reason", "Comment"]), "template.csv")
    primary_file = st.file_uploader("Upload Primary Sheet", type=["csv", "xlsx"])

with col2:
    st.subheader("2. Forecast Data")
    st.download_button("📥 Download Forecast Template", get_csv_template(["Hour Index", "Forecast", "Actual"]), "forecast_template.csv")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["csv", "xlsx"])

# --- 5. منطق المعالجة ---
if primary_file:
    df = pd.read_excel(primary_file) if primary_file.name.endswith('.xlsx') else pd.read_csv(primary_file)
    df = rename_columns_flexibly(df)
    
    # التأكد من وجود الأعمدة
    if 'Sub-reason' in df.columns:
        df['Sub-reason'] = df['Sub-reason'].apply(extract_english_only)
        df['Hour Index'] = pd.to_numeric(df['Hour Index'], errors='coerce').fillna(0).astype(int)
        
        st.success("✅ تم قراءة الملف بنجاح.")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Final Bridge Report"):
            summary = df.groupby("Sub-reason").size().reset_index(name="Count")
            
            report = "**Operational Bridge Report**\n\n"
            for _, row in summary.iterrows():
                report += f"- **{row['Sub-reason']}**: {row['Count']} cases\n"
            
            st.text_area("Final Report Output:", value=report, height=300)
    else:
        st.error("❌ لم أستطع تحديد عمود الـ Sub-reason. تأكد من وجود كلمة (Sub أو Reason) في رأس العمود.")
else:
    st.info("💡 قم برفع ملف الـ Primary Data للبدء.")
