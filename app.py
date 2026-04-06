import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Risk Calculator", layout="wide")

st.title("Executive Risk Dashboard")

# -----------------------------
# FILE UPLOAD
# -----------------------------
file = st.file_uploader("Upload CSV File", type=["csv"])

if file is not None:

    # -----------------------------
    # SAFE CSV READ (handles SAP messy files)
    # -----------------------------
    try:
        df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    except:
        df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')

    st.subheader("Data Preview")
    st.dataframe(df.head())

    # -----------------------------
    # REQUIRED COLUMNS CHECK
    # -----------------------------
    required_cols = [
        "JobNumber", "PhaseCode", "PhaseDescription", "CostType",
        "JTD_Cost", "Projected_Cost", "JTD_Hours", "Projected_Hours"
    ]

    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # -----------------------------
    # CLEAN NUMERIC DATA
    # -----------------------------
    num_cols = ["JTD_Cost", "Projected_Cost", "JTD_Hours", "Projected_Hours"]

    for col in num_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # -----------------------------
    # CORE CALCULATIONS
    # -----------------------------
    df["Remaining_Cost"] = df["Projected_Cost"] - df["JTD_Cost"]
    df["Remaining_Hours"] = df["Projected_Hours"] - df["JTD_Hours"]

    df["JTD_Rate"] = np.where(
        df["JTD_Hours"] != 0,
        df["JTD_Cost"] / df["JTD_Hours"],
        0
    )

    df["Remaining_Rate"] = np.where(
        df["Remaining_Hours"] != 0,
        df["Remaining_Cost"] / df["Remaining_Hours"],
        0
    )

    df["Rate_Diff"] = df["JTD_Rate"] - df["Remaining_Rate"]

    df["Calculated_Risk"] = df["Rate_Diff"] * df["Remaining_Hours"]

    # -----------------------------
    # LABOR CATEGORY
    # -----------------------------
    office_codes = ["1000", "9310", "9410", "9510", "9520", "9610"]

    def get_category(row):
        if row["CostType"] != "Labor":
            return "NA"
        if str(row["PhaseCode"]) in office_codes:
            return "Office"
        desc = str(row["PhaseDescription"]).lower()
        keywords = ["engineering", "design", "management", "admin", "project"]
        if any(k in desc for k in keywords):
            return "Office"
        return "Field"

    df["Labor_Category"] = df.apply(get_category, axis=1)

    # -----------------------------
    # TOTALS
    # -----------------------------
    total_projected_cost = df["Projected_Cost"].sum()
    total_risk = df["Calculated_Risk"].sum()

    # -----------------------------
    # CONTRACT INPUT
    # -----------------------------
    contract_value = st.number_input("Contract Value", value=1000000)

    # -----------------------------
    # CONTINGENCY & GAINSHARE
    # -----------------------------
    contingency = df[df["PhaseCode"] == "CONT"]["Projected_Cost"].sum()
    gainshare = df[df["PhaseCode"] == "GNSH"]["Projected_Cost"].sum()

    # -----------------------------
    # USER INPUT (WHAT-IF)
    # -----------------------------
    st.sidebar.header("Assumed Risk")

    labor_field = st.sidebar.slider("Labor Field", -100000, 100000, 0)
    labor_office = st.sidebar.slider("Labor Office", -100000, 100000, 0)
    material = st.sidebar.slider("Material", -100000, 100000, 0)
    equipment = st.sidebar.slider("Equipment", -100000, 100000, 0)
    subcontractor = st.sidebar.slider("Subcontractor", -100000, 100000, 0)
    travel = st.sidebar.slider("Travel", -100000, 100000, 0)
    other = st.sidebar.slider("Other Direct", -100000, 100000, 0)

    total_assumed = (
        labor_field + labor_office + material +
        equipment + subcontractor + travel + other
    )

    # -----------------------------
    # PROFIT
    # -----------------------------
    gross_profit = contract_value - total_projected_cost

    total_profit = gross_profit + contingency + total_assumed

    profit_pct = (total_profit / contract_value * 100) if contract_value != 0 else 0

    # -----------------------------
    # RISK STATUS
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
    st.subheader("Key Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Contract Value", f"${contract_value:,.0f}")
    col2.metric("Calculated Risk", f"${total_risk:,.0f}")
    col3.metric("Contingency", f"${contingency:,.0f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Gainshare", f"${gainshare:,.0f}")
    col5.metric("Total Profit", f"${total_profit:,.0f}")
    col6.metric("Profit %", f"{profit_pct:.2f}%")

    st.subheader(f"Risk Status: {status}")

    # -----------------------------
    # CHART
    # -----------------------------
    st.subheader("Risk by Cost Type")
    chart = df.groupby("CostType")["Calculated_Risk"].sum()
    st.bar_chart(chart)

    # -----------------------------
    # DATA TABLE
    # -----------------------------
    st.subheader("Detailed Data")
    st.dataframe(df)

else:
    st.info("Please upload a CSV file to begin.")
