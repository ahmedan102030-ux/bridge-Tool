import streamlit as st
import pandas as pd
import re
from collections import Counter
import json

# دالة لتوليد التمبلت للتحميل
def get_csv_template(columns):
    df = pd.DataFrame(columns=columns)
    return df.to_csv(index=False).encode('utf-8')

# استيراد المكتبة الرسمية من جوجل
try:
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Please add 'google-generativeai' to your requirements.txt file!")

st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Flexible & Integrated)")

# --- منطق اكتشاف الأعمدة بمرونة ---
def rename_columns_flexibly(df):
    rename_map = {}
    for col in df.columns:
        c = str(col).lower().replace("_", "").replace("-", "").replace(" ", "")
        if 'date' in c: rename_map[col] = 'Date'
        elif 'hour' in c or 'hr' in c: rename_map[col] = 'Hour Index'
        elif 'sub' in c or 'reason' in c: rename_map[col] = 'Sub-reason'
        elif 'comment' in c or 'ملاحظ' in c: rename_map[col] = 'Comment'
    return df.rename(columns=rename_map)

# --- إعدادات الذكاء الاصطناعي ---
with st.sidebar:
    st.header("⚙️ AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Enter Gemini API Key:", type="password")

# --- الواجهة ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Primary Data")
    st.download_button("📥 Download Primary Template", get_csv_template(["Date", "Hour Index", "Order", "DSP_Bridge_Sub_Reason", "Comment"]), "primary_template.csv")
    primary_file = st.file_uploader("Upload Primary Sheet", type=["csv", "xlsx"], key="primary")

with col2:
    st.subheader("2. Forecast Data")
    st.download_button("📥 Download Forecast Template", get_csv_template(["Hour Index", "Forecast", "Actual"]), "forecast_template.csv")
    secondary_file = st.file_uploader("Upload Forecast Sheet", type=["csv", "xlsx"], key="secondary")

# --- الدوال البرمجية (Extract & Context) ---
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

# --- معالجة الملفات ---
if primary_file:
    df = pd.read_excel(primary_file) if primary_file.name.endswith('.xlsx') else pd.read_csv(primary_file)
    df = rename_columns_flexibly(df)
    
    # التأكد من وجود الأعمدة
    if 'Sub-reason' in df.columns:
        df['Sub-reason'] = df['Sub-reason'].apply(extract_english_only)
        df['Hour Index'] = pd.to_numeric(df['Hour Index'], errors='coerce').fillna(0).astype(int)
        
        st.success("✅ تم معالجة البيانات بنجاح.")
        st.dataframe(df.head())
        
        if st.button("🚀 Generate Final Integrated Report"):
            summary_df = df.groupby("Sub-reason").size().reset_index(name="Count")
            summary_df['HoursList'] = df.groupby("Sub-reason")['Hour Index'].apply(list).values
            
            # (هنا يتم دمج منطق التقرير ونداء Gemini كما في كودك السابق)
            st.write("### 📋 التقرير النهائي")
            st.table(summary_df[['Sub-reason', 'Count']])
    else:
        st.error("❌ لم يتم العثور على عمود الـ Sub-reason. تأكد من وجوده في الملف.")
else:
    st.info("💡 قم برفع ملف الـ Primary Data للبدء.")
