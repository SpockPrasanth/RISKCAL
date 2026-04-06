
import streamlit as st
import pandas as pd
import numpy as np

st.title("Risk Calculator")

file = st.file_uploader("Upload CSV", type=["csv"])

if file:
    df = pd.read_csv(file)

    df["Remaining_Cost"] = df["Projected_Cost"] - df["JTD_Cost"]
    df["Remaining_Hours"] = df["Projected_Hours"] - df["JTD_Hours"]

    df["JTD_Rate"] = df["JTD_Cost"] / df["JTD_Hours"]
    df["Remaining_Rate"] = df["Remaining_Cost"] / df["Remaining_Hours"]

    df["Calculated_Risk"] = (df["JTD_Rate"] - df["Remaining_Rate"]) * df["Remaining_Hours"]

    st.write(df)

    total_risk = df["Calculated_Risk"].sum()
    st.metric("Total Risk", f"${total_risk:,.0f}")

else:
    st.write("Upload a file to start")
