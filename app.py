import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Risk Dashboard", layout="wide")

st.title("Executive Risk Dashboard")

file = st.file_uploader("Upload Spectrum CSV File", type=["csv"])

if file:

    # -----------------------------
    # READ RAW LINES
    # -----------------------------
    content = file.getvalue().decode("latin1")
    lines = content.split("\n")

    # -----------------------------
    # FIND HEADER ROW
    # -----------------------------
    header_index = None

    for i, line in enumerate(lines):
        if "Phase" in line and "Cost" in line:
            header_index = i
            break

    if header_index is None:
        st.error("Could not detect header row")
        st.stop()

    # -----------------------------
    # LOAD DATA FROM HEADER
    # -----------------------------
    data = "\n".join(lines[header_index:])

    from io import StringIO
    df = pd.read_csv(StringIO(data), sep=",", engine="python")

    # -----------------------------
    # CLEAN DATA
    # -----------------------------
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    st.subheader("Detected Columns")
    st.write(df.columns.tolist())

    st.subheader("Preview")
    st.dataframe(df.head())

    # -----------------------------
    # AUTO COLUMN MAPPING (SMART)
    # -----------------------------
    def find_col(name_list):
        for col in df.columns:
            for keyword in name_list:
                if keyword.lower() in col.lower():
                    return col
        return None

    col_map = {
        "PhaseCode": find_col(["phase"]),
        "CostType": find_col(["cost type"]),
        "JTD_Cost": find_col(["jtd cost", "cost to date"]),
        "Projected_Cost": find_col(["projected cost"]),
        "JTD_Hours": find_col(["jtd hours"]),
        "Projected_Hours": find_col(["projected hours"])
    }

    missing = [k for k, v in col_map.items() if v is None]

    if missing:
        st.error(f"Could not map columns: {missing}")
        st.stop()

    # Rename columns
    df = df.rename(columns={v: k for k, v in col_map.items()})

    # -----------------------------
    # CLEAN NUMERIC DATA
    # -----------------------------
    for col in ["JTD_Cost", "Projected_Cost", "JTD_Hours", "Projected_Hours"]:
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

    total_risk = df["Calculated_Risk"].sum()
    total_projected_cost = df["Projected_Cost"].sum()

    # -----------------------------
    # CONTRACT INPUT
    # -----------------------------
    contract = st.number_input("Contract Value", value=1000000)

    # -----------------------------
    # CONTINGENCY / GAINSHARE
    # -----------------------------
    contingency = df[df["PhaseCode"].astype(str).str.contains("CONT", na=False)]["Projected_Cost"].sum()
    gainshare = df[df["PhaseCode"].astype(str).str.contains("GNSH", na=False)]["Projected_Cost"].sum()

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
