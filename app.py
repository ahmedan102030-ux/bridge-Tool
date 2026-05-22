import streamlit as st
import pandas as pd
import re
from collections import Counter
import json

# ✨ استيراد المكتبة الرسمية من جوجل لمنع أخطاء الاتصال تماماً
try:
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Please add 'google-generativeai' to your requirements.txt file on GitHub!")

st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Hour-by-Hour Forecast Matcher)")

with st.sidebar:
    st.header("⚙️ AI Configuration")
    enable_ai = st.checkbox("🔮 Enable Gemini AI Analysis", value=False, 
                            help="Turn on to get deep AI justifications, turn off to use standard logic and save API limits.")
    ai_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="AIzaSy...")
    if enable_ai and not ai_key:
        st.warning("⚠️ Please provide an API key to use the AI feature.")

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
        peak_str = ", ".join(peak_parts)
        ctx = f"This driver impacted {real_percentage:.2f}% of our total volume. Disruptions concentrated heavily during {period_str} ({peak_str})."
        if forecast_df is not None and not forecast_df.empty:
            justifications = []
            for h, _ in sorted_hours[:3]:
                match = forecast_df[forecast_df['Hour Index'] == h]
                if not match.empty:
                    act_v = match.iloc[0]['Actual']
                    for_v = match.iloc[0]['Forecast']
                    if act_v > for_v:
                        justifications.append(f"Hour {h} spiked with Actual volume reaching {int(act_v):,} against a forecast of {int(for_v):,}")
            if justifications:
                ctx += " Driven by volume mismatches where " + ", and ".join(justifications) + "."
        return ctx
    elif "net" in reason.lower():
        hours_formatted = ", ".join([str(h) for h in sorted(list(set(hours_list)))])
        return f"Network/system connectivity constraints registered across {period_str} (Hours {hours_formatted}), holding a minor share against total dispatched volume."
    elif "multi" in reason.lower():
        hours_formatted = ", ".join([str(h) for h in sorted(list(set(hours_list)))])
        return f"Delays related to multiple package orders, appearing consistently in the {period_str} (Hours {hours_formatted})."
    elif count <= 2 and len(hours_list) > 0:
        return f"Isolated case recorded during the {hours_list[0]}:00 shift."
    else:
        hours_formatted = ", ".join([str(h) for h in sorted(list(set(hours_list)))])
        return f"Observed operational bottleneck during {period_str} (Hours {hours_formatted})."

def generate_bulk_ai_contexts(summary_df, total_vol, forecast_data_str, key):
    input_data = []
    for row in summary_df.itertuples():
        real_percentage = (row.Count / total_vol) * 100
        hour_counts = dict(Counter(row.HoursList))
        input_data.append({
            "Issue": row._1,
            "Cases": row.Count,
            "Impact": f"{real_percentage:.2f}%",
            "Hours_Distribution": hour_counts
        })
        
    prompt = (
        f"You are an expert Amazon Logistics Operations Manager writing a bridge report.\n"
        f"Write a concise, professional, 2-line 'Context' for EACH issue listed below.\n\n"
        f"Data:\n{json.dumps(input_data, indent=2)}\n\n"
        f"Forecast Data:\n{forecast_data_str}\n\n"
        f"OUTPUT INSTRUCTION:\n"
        f"Return ONLY a pure JSON object mapping each issue name to its 2-line context string. Do not include markdown code block syntax like ```json. Your response must be clean JSON text only.\n"
        f"Example format:\n"
        f"{{\n"
        f"  \"Order Count Issue\": \"Text here...\",\n"
        f"  \"Net Issue\": \"Text here...\"\n"
        f"}}"
    )
    
    # تنظيف المفتاح تماماً من أي شوائب خفية
    clean_key = str(key).strip().replace("'", "").replace('"', "")
    
    try:
        # تشغيل الاتصال الآمن والمباشر عبر مكتبة جوجل الرسمية
        genai.configure(api_key=clean_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # تنظيف أي كود بلوك لو الذكاء الاصطناعي كتبه بالخطأ
        raw_text = re.sub(r"^```[a-zA-Z]*\n", "", raw_text)
        raw_text = re.sub(r"\n```$", "", raw_text)
        raw_text = raw_text.strip()
        
        return json.loads(raw_text)
    except Exception as e:
        st.sidebar.error(f"🔴 Gemini Library Error: {e}")
    return {}

if primary_file:
    if primary_file.name.endswith('.xlsx'): df = pd.read_excel(primary_file)
    else: df = pd.read_csv(primary_file)
    
    rename_dict = {}
    for col in df.columns:
        col_cleaned = str(col).strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        if "date" in col_cleaned: rename_dict[col] = "Date"
        elif "hour" in col_cleaned or "hr" in col_cleaned: rename_dict[col] = "Hour Index"
        elif "order" in col_cleaned: rename_dict[col] = "Order"
        elif "sub" in col_cleaned or "reason" in col_cleaned: rename_dict[col] = "Sub-reason"
        elif "comment" in col_cleaned or "ملاحظ" in col_cleaned: rename_dict[col] = "Comment"
            
    df = df.rename(columns=rename_dict)
    for rc in ["Date", "Hour Index", "Order", "Sub-reason", "Comment"]:
        if rc not in df.columns: df[rc] = ""

    df['Sub-reason'] = df['Sub-reason'].apply(extract_english_only)
    def clean_hour(val):
        try: return int(float(str(val).split(".")[0].strip()))
        except: return 0
    df['Hour Index'] = df['Hour Index'].apply(clean_hour)

    selected_df = df.copy()
    if report_type == "Daily Bridge" and 'Date' in df.columns and str(df['Date'].iloc[0]).strip() != "":
        df['Date'] = df['Date'].astype(str)
        unique_dates = df['Date'].unique()
        selected_date = st.selectbox("Select Date for Daily Analysis:", unique_dates)
        selected_df = df[df['Date'] == selected_date]

    forecast_df_clean = None
    forecast_str_for_ai = "No Forecast sheet provided"
    if secondary_file:
        try:
            if secondary_file.name.endswith('.xlsx'): df_sec = pd.read_excel(secondary_file)
            else: df_sec = pd.read_csv(secondary_file)
            df_sec.columns = [str(c).strip() for c in df_sec.columns]
            for h_col in df_sec.columns:
                if "hour" in str(h_col).lower(): df_sec = df_sec.rename(columns={h_col: "Hour Index"})
            f_col = [c for c in df_sec.columns if "fore" in str(c).lower()]
            a_col = [c for c in df_sec.columns if "act" in str(c).lower() or "order" in str(c).lower()]
            
            if f_col and a_col and 'Hour Index' in df_sec.columns:
                df_sec = df_sec.rename(columns={f_col[0]: "Forecast", a_col[0]: "Actual"})
                df_sec['Actual'] = pd.to_numeric(df_sec['Actual'], errors='coerce').fillna(0)
                df_sec['Forecast'] = pd.to_numeric(df_sec['Forecast'], errors='coerce').fillna(0)
                df_sec['Hour Index'] = df_sec['Hour Index'].apply(clean_hour)
                forecast_df_clean = df_sec
                forecast_str_for_ai = df_sec[['Hour Index', 'Forecast', 'Actual']].to_string(index=False)
                st.success("✅ Forecast Sheet processed successfully.")
        except Exception as e:
            st.error(f"Error parsing forecast data: {e}")

    st.write("---")
    if st.button("🚀 Generate Final Integrated Report"):
        total_incidents = len(selected_df)
        summary_data = []
        for reason in selected_df['Sub-reason'].unique():
            reason_df = selected_df[selected_df['Sub-reason'] == reason]
            summary_data.append({
                "Sub-reason": reason,
                "Count": len(reason_df),
                "HoursList": reason_df['Hour Index'].tolist()
            })
            
        summary_df = pd.DataFrame(summary_data).sort_values(by='Count', ascending=False)
        
        ai_bulk_responses = {}
        if enable_ai and ai_key:
            with st.spinner("🔮 AI is analyzing all operational metrics at once... Please wait."):
                ai_bulk_responses = generate_bulk_ai_contexts(summary_df, total_volume, forecast_str_for_ai, ai_key)
        elif enable_ai and not ai_key:
            st.error("❌ AI Checkbox is checked but Key is missing in sidebar!")
        
        report_text = f"**Operational Bridge Report - Amazon Egypt Logistics ({report_type})**\n\n"
        report_text += "Dear Team,\n\n"
        report_text += f"This report provides an operational overview of metrics relative to a Total Volume of {total_volume:,} orders, capturing {total_incidents} logged incidents.\n\n"
        
        for idx, row in enumerate(summary_df.itertuples(), 1):
            v_percentage = (row.Count / total_volume) * 100
            suffix = ' "Courier Support"' if "multi package" in row._1.lower() else ""
            report_text += f"{idx}- {row._1}: {row.Count} cases ({v_percentage:.2f}% of Total Volume){suffix}\n"
            
            matched_context = None
            if ai_bulk_responses:
                for k, v in ai_bulk_responses.items():
                    if str(k).strip().lower() == str(row._1).strip().lower():
                        matched_context = v
                        break
            
            if enable_ai and ai_key and matched_context:
                context_string = matched_context
            else:
                context_string = generate_standard_context(row._1, row.Count, total_volume, row.HoursList, forecast_df_clean)
                if enable_ai and not matched_context:
                    context_string = "[Fallback to Standard] " + context_string
                
            if context_string: report_text += f"Context: {context_string}\n\n"
            else: report_text += "\n"
            
        report_text += "Best regards,\nAmazon Egypt Logistics Team"
        st.subheader("📋 Generated Bridge Report")
        st.text_area("Final Output:", value=report_text, height=500)
else:
    st.info("💡 Please upload the Primary Data Sheet to activate.")
