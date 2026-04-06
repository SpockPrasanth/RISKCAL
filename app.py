import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Executive Risk Dashboard", layout="wide")

# -----------------------------
# UI DESIGN (HOMEPAGE STYLE)
# -----------------------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #1e293b, #0f172a);
}

.main-box {
    background-color: white;
    padding: 40px;
    border-radius: 16px;
    max-width: 800px;
    margin: auto;
    text-align: center;
}

.title {
    font-size: 34px;
    font-weight: bold;
    color: #4f46e5;
}

.subtitle {
    color: #6b7280;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="main-box">', unsafe_allow_html=True)

st.markdown('<div class="title">Executive Risk Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload your Job Overview Report to begin analysis</div>', unsafe_allow_html=True)

file = st.file_uploader("Upload CSV File", type=["csv"])

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# PROCESS FILE
# -----------------------------
if file:

    # -----------------------------
    # READ RAW FILE (NO PARSER)
    # -----------------------------
    content = file.getvalue().decode("latin1")
    lines = content.split("\n")

    data_rows = []

    for line in lines:
        if "Phase:" in line:

            try:
                parts = line.split(",")

                phase_text = parts[0]
                phase_code = phase_text.split(":")[1].strip().split(" ")[0]

                cost_type = parts[2].strip()

                cost_map = {
                    "L": "Labor",
                    "E": "Equipment",
                    "M": "Material",
                    "S": "Subcontractor",
                    "T": "Travel",
                    "O": "Other"
                }
                cost_type = cost_map.get(cost_type, cost_type)

                def safe_float(x):
                    try:
                        return float(x.replace(",", "").strip())
                    except:
                        return 0

                jtd_hours = safe_float(parts[6])
                projected_hours = safe_float(parts[7])

                jtd_cost = safe_float(parts[11])
                projected_cost = safe_float(parts[12])

                data_rows.append({
                    "JobNumber": "25057",
                    "PhaseCode": phase_code,
                    "PhaseDescription": phase_text,
                    "CostType": cost_type,
                    "JTD_Cost": jtd_cost,
                    "Projected_Cost": projected_cost,
                    "JTD_Hours": jtd_hours,
                    "Projected_Hours": projected_hours
                })

            except:
                continue

    # -----------------------------
    # CREATE DATAFRAME
    # -----------------------------
    df = pd.DataFrame(data_rows)

    if df.empty:
        st.error("No usable data found. Please check file format.")
        st.stop()

    # -----------------------------
    # CALCULATIONS (YOUR LOGIC)
    # -----------------------------
    df["Remaining_Cost"] = df["Projected_Cost"] - df["JTD_Cost"]
    df["Remaining_Hours"] = df["Projected_Hours"] - df["JTD_Hours"]

    df["JTD_Rate"] = np.where(df["JTD_Hours"] != 0,
                             df["JTD_Cost"] / df["JTD_Hours"], 0)

    df["Remaining_Rate"] = np.where(df["Remaining_Hours"] != 0,
                                   df["Remaining_Cost"] / df["Remaining_Hours"], 0)

    df["Rate_Diff"] = df["JTD_Rate"] - df["Remaining_Rate"]

    df["Calculated_Risk"] = df["Rate_Diff"] * df["Remaining_Hours"]

    # -----------------------------
    # TOTALS
    # -----------------------------
    total_risk = df["Calculated_Risk"].sum()
    total_projected_cost = df["Projected_Cost"].sum()

    # -----------------------------
    # CONTRACT INPUT
    # -----------------------------
    contract = st.number_input("Contract Value", value=179620000)

    # -----------------------------
    # CONTINGENCY & GAINSHARE
    # -----------------------------
    contingency = df[df["PhaseCode"] == "CONT"]["Projected_Cost"].sum()
    gainshare = df[df["PhaseCode"] == "GNSH"]["Projected_Cost"].sum()

    # -----------------------------
    # USER INPUT
    # -----------------------------
    st.sidebar.header("Assumed Risk")

    labor = st.sidebar.slider("Labor", -100000, 100000, 0)
    material = st.sidebar.slider("Material", -100000, 100000, 0)
    equipment = st.sidebar.slider("Equipment", -100000, 100000, 0)

    total_assumed = labor + material + equipment

    # -----------------------------
    # PROFIT
    # -----------------------------
    gross_profit = contract - total_projected_cost
    total_profit = gross_profit + contingency + total_assumed
    profit_pct = (total_profit / contract * 100)

    # -----------------------------
    # STATUS
    # -----------------------------
    coverage = contingency + gainshare

    if total_risk <= 0:
        status = "GOOD"
    elif total_risk > coverage:
        status = "CRITICAL"
    else:
        status = "WARNING"

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    st.markdown("## Key Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Risk", f"${total_risk:,.0f}")
    c2.metric("Profit", f"${total_profit:,.0f}")
    c3.metric("Profit %", f"{profit_pct:.2f}%")

    st.markdown(f"### Risk Status: {status}")

    # -----------------------------
    # CHART
    # -----------------------------
    st.markdown("## Risk by Cost Type")
    st.bar_chart(df.groupby("CostType")["Calculated_Risk"].sum())

    # -----------------------------
    # TABLE
    # -----------------------------
    st.markdown("## Detailed Data")
    st.dataframe(df)

else:
    st.info("Upload your SAP Job Overview CSV file")
