import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Risk Dashboard", layout="wide")

st.title("Executive Risk Dashboard")

file = st.file_uploader("Upload CSV File", type=["csv"])

if file:

    # -----------------------------
    # LOAD RAW FILE
    # -----------------------------
    raw = pd.read_csv(file, encoding="latin1", header=None)

    # -----------------------------
    # CLEAN RAW DATA
    # -----------------------------
    raw = raw.fillna("")

    # Convert all rows to string
    raw = raw.astype(str)

    # -----------------------------
    # EXTRACT ONLY PHASE ROWS
    # -----------------------------
    data_rows = []

    for i in range(len(raw)):
        row = raw.iloc[i].tolist()

        # Look for actual phase data rows
        if "Phase:" in row[0]:

            try:
                phase_text = row[0]
                phase_code = phase_text.split(":")[1].strip().split(" ")[0]

                cost_type = row[2]
                cost_type_map = {
                    "L": "Labor",
                    "E": "Equipment",
                    "M": "Material",
                    "S": "Subcontractor",
                    "T": "Travel",
                    "O": "Other"
                }

                cost_type = cost_type_map.get(cost_type, cost_type)

                # Extract values (based on your file structure)
                jtd_hours = float(row[6]) if row[6] else 0
                projected_hours = float(row[7]) if row[7] else 0

                jtd_cost = float(row[11].replace(",", "")) if row[11] else 0
                projected_cost = float(row[12].replace(",", "")) if row[12] else 0

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
    # CREATE CLEAN DATAFRAME
    # -----------------------------
    df = pd.DataFrame(data_rows)

    if df.empty:
        st.error("No usable data found in file")
        st.stop()

    st.subheader("Cleaned Data")
    st.dataframe(df)

    # -----------------------------
    # RISK CALCULATIONS
    # -----------------------------
    df["Remaining_Cost"] = df["Projected_Cost"] - df["JTD_Cost"]
    df["Remaining_Hours"] = df["Projected_Hours"] - df["JTD_Hours"]

    df["JTD_Rate"] = np.where(df["JTD_Hours"] != 0,
                             df["JTD_Cost"] / df["JTD_Hours"], 0)

    df["Remaining_Rate"] = np.where(df["Remaining_Hours"] != 0,
                                   df["Remaining_Cost"] / df["Remaining_Hours"], 0)

    df["Rate_Diff"] = df["JTD_Rate"] - df["Remaining_Rate"]
    df["Calculated_Risk"] = df["Rate_Diff"] * df["Remaining_Hours"]

    total_risk = df["Calculated_Risk"].sum()
    total_projected_cost = df["Projected_Cost"].sum()

    # -----------------------------
    # CONTRACT INPUT
    # -----------------------------
    contract = st.number_input("Contract Value", value=179620000)

    # -----------------------------
    # CONTINGENCY / GAINSHARE
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
    st.subheader("Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Risk", f"${total_risk:,.0f}")
    c2.metric("Profit", f"${total_profit:,.0f}")
    c3.metric("Profit %", f"{profit_pct:.2f}%")

    st.subheader(f"Status: {status}")

    st.subheader("Risk by Cost Type")
    st.bar_chart(df.groupby("CostType")["Calculated_Risk"].sum())

else:
    st.info("Upload your SAP Job Overview CSV")
