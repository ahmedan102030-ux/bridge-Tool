import streamlit as st
import pandas as pd
import re
from collections import Counter

st.set_page_config(page_title="Operations Bridge Assistant", layout="wide")
st.title("📊 Operations Bridge Assistant (Hour-by-Hour Forecast Matcher)")

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

def generate_hourly_integrated_context(reason, count, total_vol, hours_list, forecast_df):
    real_percentage = (count / total_vol) * 100
    hour_counts = Counter(hours_list)
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    
    time_periods = []
    if any(0 <= h <= 6 for h in hours_list): time_periods.append("midnight/early morning")
    if any(7 <= h <= 15 for h in hours_list): time_periods.append("midday peaks")
    if any(16 <= h <= 23 for h in hours_list): time_periods.append("afternoon and evening shifts")
    period_str = " and ".join(time_periods) if time_periods else "various shifts"

    if "order count" in reason.lower():
        peak_parts = []
        for h, c in sorted_hours[:3]:
            peak_parts.append(f"Hour {h} had {c} cases")
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
        return (f"Network/system connectivity constraints registered across {period_str} "
                f"(Hours {hours_formatted}), holding a minor share against total dispatched volume.")
                
    elif "multi" in reason.lower():
        hours_formatted = ", ".join([str(h) for h in sorted(list(set(hours_list)))])
        return (f"Delays related to multiple package orders, appearing consistently in the "
                f"{period_str} (Hours {hours_formatted}).")
                
    elif count <= 2:
        if len(hours_list) > 0:
            h = hours_list[0]
            if "customer" in reason.lower(): return f"Isolated customer unavailability issue during the {h}:00 shift."
            return f"Isolated case recorded during the {h}:00 shift."
        return ""
    else:
        hours_formatted = ", ".join([str(h) for h in sorted(list(set(hours_list)))])
        return f"Observed operational bottleneck during {period_str} (Hours {hours_formatted})."

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
                st.success("✅ Forecast Sheet processed successfully. Hourly mapper active.")
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
        
        report_text = f"**Operational Bridge Report - Amazon Egypt Logistics ({report_type})**\n\n"
        report_text += "Dear Team,\n\n"
        report_text += f"This report provides an operational overview of metrics relative to a Total Volume of {total_volume:,} orders, capturing {total_incidents} logged incidents.\n\n"
        
        for idx, row in enumerate(summary_df.itertuples(), 1):
            v_percentage = (row.Count / total_volume) * 100
            suffix = ' "Courier Support"' if "multi package" in row._1.lower() else ""
            
            report_text += f"{idx}- {row._1}: {row.Count} cases ({v_percentage:.2f}% of Total Volume){suffix}\n"
            context_string = generate_hourly_integrated_context(row._1, row.Count, total_volume, row.HoursList, forecast_df_clean)
            if context_string: report_text += f"Context: {context_string}\n\n"
            else: report_text += "\n"
            
        report_text += "Best regards,\nAmazon Egypt Logistics Team"
        
        st.subheader("📋 Generated Bridge Report (Hour-by-Hour Mapping)")
        st.text_area("Final Output:", value=report_text, height=500)
else:
    st.info("💡 Please upload the Primary Data Sheet to activate.")