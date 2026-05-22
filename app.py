import streamlit as st
import pandas as pd
import re
from collections import Counter
import json

try:
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Please install 'google-generativeai'")

st.set_page_config(page_title="Operations Bridge Center", layout="wide")
st.title("📊 Operations Bridge Assistant")

# --- دالة التنظيف ---
def extract_english_only(text):
    txt_str = str(text).strip()
    if txt_str in ["", "nan", "None", "0", "0.0"]: return "Others"
    cleaned = re.sub(r'[\u0600-\u06FF]', '', txt_str)
    cleaned = cleaned.replace("-", "").strip()
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else "Others"

# --- القائمة الجانبية للتحكم ---
with st.sidebar:
    st.header("⚙️ Bridge Type")
    bridge_type = st.radio("Select Bridge:", ["OTP Bridge", "Store Closure Bridge"])
    st.markdown("---")
    st.header("🔮 AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False)
    ai_key = st.text_input("Enter Gemini API Key:", type="password")

# --- 1. OTP Bridge (الكود الأصلي الخاص بك) ---
if bridge_type == "OTP Bridge":
    st.header("📊 OTP Bridge (Hour-by-Hour Forecast Matcher)")
    # [هنا تضع منطق الـ OTP Bridge الخاص بك كاملاً]
    # (لقد تركت هذا الجزء ليكون كما هو في كودك)
    primary_file = st.file_uploader("Upload Primary Data", type=["xlsx", "csv"], key="otp_primary")
    # ... (باقي كود الـ OTP الخاص بك)

# --- 2. Store Closure Bridge (المنطق الجديد) ---
else:
    st.header("🔒 Store Closure Bridge Analysis")
    closure_file = st.file_uploader("Upload Store Closure CSV", type=["csv"], key="closure_file")
    
    if closure_file:
        df = pd.read_csv(closure_file)
        # تنظيف الأعمدة تلقائياً
        df.columns = [c.strip().lower().replace(" ", "") for c in df.columns]
        
        if st.button("🚀 Generate Closure Report"):
            # منطق استخراج التقرير حسب الشكل الذي أرسلته
            st.write("### 📝 Generated Report:")
            report = ""
            for issue, group in df.groupby('issue'):
                total_mins = group['closuremins'].sum()
                slots = group['slot'].unique()
                slots_str = ", ".join(map(str, sorted(slots)))
                # التنسيق الذي طلبته
                report += f"**{issue}**: Closed for {total_mins} mins (slots {slots_str}).\n\n"
            
            st.text_area("Final Output:", value=report, height=300)
