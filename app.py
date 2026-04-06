import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Executive Risk Dashboard", layout="wide")

# -----------------------------
# CUSTOM CSS (UI DESIGN)
# -----------------------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #1e293b, #0f172a);
}

.main-container {
    background-color: white;
    padding: 40px;
    border-radius: 16px;
    max-width: 900px;
    margin: auto;
    text-align: center;
}

.title {
    font-size: 36px;
    font-weight: bold;
    color: #4f46e5;
}

.subtitle {
    color: #6b7280;
    margin-bottom: 30px;
}

.upload-box {
    border: 2px dashed #cbd5e1;
    padding: 40px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER UI
# -----------------------------
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.image("https://upload.wikimedia.org/wikipedia/commons/4/4f/Iconic_image_placeholder.png", width=80)

st.markdown('<div class="title">Executive Risk Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload your Job Overview Report to begin analysis</div>', unsafe_allow_html=True)

# -----------------------------
# FILE UPLOAD
# -----------------------------
file = st.file_uploader("Upload CSV File", type=["csv"])

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# PROCESS DATA
# -----------------------------
if file:

    # SAFE LOAD
    try:
        df = pd.read_csv(file, encoding='latin1', sep=',')
    except:
        try:
            df = pd.read_csv(file, encoding='latin1', sep=';')
        except:
            df = pd.read_csv(file, encoding='latin1', engine='python', on_bad_lines='skip')

    df = df.dropna(axis=1, how='all')
    df = df.dropna(how='all')

    # REQUIRED COLUMNS
    required_cols = [
        "JobNumber", "PhaseCode", "PhaseDescription", "CostType",
        "JTD_Cost", "Projected_Cost", "JTD_Hours", "Projected_Hours"
    ]

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    # CLEAN NUMBERS
    for col in ["JTD_Cost", "Projected_Cost", "JTD_Hours", "Projected_Hours"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # CALCULATIONS
    df["Remaining_Cost"] = df["Projected_Cost"] - df["JTD_Cost"]
    df["Remaining_Hours"] = df["Projected_Hours"] - df["JTD_Hours"]

    df["JTD_Rate"] = np.where(df["JTD_Hours"] != 0, df["JTD_Cost"] / df["JTD_Hours"], 0)
    df["Remaining_Rate"] = np.where(df["Remaining_Hours"] != 0, df["Remaining_Cost"] / df["Remaining_Hours"], 0)

    df["Rate_Diff"] = df["JTD_Rate"] - df["Remaining_Rate"]
    df["Calculated_Risk"] = df["Rate_Diff"] * df["Remaining_Hours"]

    # TOTALS
    total_risk = df["Calculated_Risk"].sum()
    total_projected_cost = df["Projected_Cost"].sum()

    # CONTRACT INPUT
    contract = st.number_input("Contract Value", value=1000000)

    # CONT & GNSH
    contingency = df[df["PhaseCode"] == "CONT"]["Projected_Cost"].sum()
    gainshare = df[df["PhaseCode"] == "GNSH"]["Projected_Cost"].sum()

    # USER INPUT
    st.sidebar.header("Assumed Risk")

    sliders = {
        "Labor Field": st.sidebar.slider("Labor Field", -100000, 100000, 0),
        "Labor Office": st.sidebar.slider("Labor Office", -100000, 100000, 0),
        "Material": st.sidebar.slider("Material", -100000, 100000, 0),
        "Equipment": st.sidebar.slider("Equipment", -100000, 100000, 0),
        "Subcontractor": st.sidebar.slider("Subcontractor", -100000, 100000, 0),
        "Travel": st.sidebar.slider("Travel", -100000, 100000, 0),
        "Other": st.sidebar.slider("Other Direct", -100000, 100000, 0),
    }

    total_assumed = sum(sliders.values())

    # PROFIT
    gross_profit = contract - total_projected_cost
    total_profit = gross_profit + contingency + total_assumed
    profit_pct = (total_profit / contract * 100) if contract != 0 else 0

    # STATUS
    coverage = contingency + gainshare

    if total_risk <= 0:
        status = "GOOD"
    elif total_risk > coverage:
        status = "CRITICAL"
    else:
        status = "WARNING"

    # -----------------------------
    # DASHBOARD UI
    # -----------------------------
    st.markdown("## Key Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Contract", f"${contract:,.0f}")
    c2.metric("Risk", f"${total_risk:,.0f}")
    c3.metric("Contingency", f"${contingency:,.0f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Gainshare", f"${gainshare:,.0f}")
    c5.metric("Profit", f"${total_profit:,.0f}")
    c6.metric("Profit %", f"{profit_pct:.2f}%")

    st.markdown(f"### Risk Status: {status}")

    # CHART
    st.markdown("## Risk by Cost Type")
    st.bar_chart(df.groupby("CostType")["Calculated_Risk"].sum())

    # TABLE
    st.markdown("## Detailed Data")
    st.dataframe(df)

else:
    st.info("Upload a CSV file to begin")
