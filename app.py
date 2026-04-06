import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Risk Dashboard", layout="wide")

st.title("Executive Risk Dashboard")

file = st.file_uploader("Upload Spectrum CSV File", type=["csv"])

if file:

    # -----------------------------
    # SAFE READ FOR SPECTRUM
    # -----------------------------
    try:
        df = pd.read_csv(file, encoding="latin1", sep=";")
    except:
        try:
            df = pd.read_csv(file, encoding="latin1", sep=",")
        except:
            df = pd.read_csv(file, encoding="latin1", engine="python", on_bad_lines="skip")

    # -----------------------------
    # CLEAN DATA
    # -----------------------------
    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")

    st.subheader("Detected Columns")
    st.write(df.columns.tolist())

    st.subheader("Preview")
    st.dataframe(df.head())

    # -----------------------------
    # MAP YOUR COLUMN NAMES HERE
    # -----------------------------
    # ⚠️ UPDATE THESE BASED ON YOUR FILE
    col_map = {
        "Job": "JobNumber",
        "Phase": "PhaseCode",
        "Phase Description": "PhaseDescription",
        "Cost Type": "CostType",
        "JTD Cost": "JTD_Cost",
        "Projected Cost": "Projected_Cost",
        "JTD Hours": "JTD_Hours",
        "Projected Hours": "Projected_Hours"
    }

    # Rename if matches found
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    required_cols = [
        "PhaseCode", "CostType",
        "JTD_Cost", "Projected_Cost",
        "JTD_Hours", "Projected_Hours"
    ]

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # -----------------------------
    # CLEAN NUMERIC VALUES
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
    # CALCULATIONS
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

    contract = st.number_input("Contract Value", value=1000000)

    # -----------------------------
    # CONT & GNSH
    # -----------------------------
    contingency = df[df["PhaseCode"] == "CONT"]["Projected_Cost"].sum()
    gainshare = df[df["PhaseCode"] == "GNSH"]["Projected_Cost"].sum()

    # -----------------------------
    # USER INPUT
    # -----------------------------
    st.sidebar.header("Assumed Risk")

    assumed = (
        st.sidebar.slider("Labor", -100000, 100000, 0) +
        st.sidebar.slider("Material", -100000, 100000, 0) +
        st.sidebar.slider("Equipment", -100000, 100000, 0)
    )

    # -----------------------------
    # PROFIT
    # -----------------------------
    gross_profit = contract - total_projected_cost
    total_profit = gross_profit + contingency + assumed
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
    # UI
    # -----------------------------
    st.subheader("Key Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Risk", f"${total_risk:,.0f}")
    c2.metric("Profit", f"${total_profit:,.0f}")
    c3.metric("Profit %", f"{profit_pct:.2f}%")

    st.subheader(f"Status: {status}")

    st.subheader("Risk by Cost Type")
    st.bar_chart(df.groupby("CostType")["Calculated_Risk"].sum())

    st.subheader("Detailed Data")
    st.dataframe(df)

else:
    st.info("Upload Spectrum CSV file")
