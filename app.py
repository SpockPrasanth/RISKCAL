import streamlit as st
import pandas as pd

st.set_page_config(page_title="Passenger Entry App", layout="wide")

st.title("Passenger Data Entry System")

# -------------------------------
# Step 1: Platform Selection
# -------------------------------
platform_keys = ["DEL", "MUM", "BLR", "HYD"]

selected_platform = st.selectbox(
    "Select Platform Key",
    options=platform_keys
)

# -------------------------------
# Step 2: Initialize Session State
# -------------------------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(
        columns=["PLATFORMKEY", "MONTH", "YEAR", "PASSENGERS"]
    )

# -------------------------------
# Step 3: Show Table After Selection
# -------------------------------
if selected_platform:

    st.subheader(f"Enter Data for {selected_platform}")

    # Pre-fill one row if empty
    if st.session_state.data.empty:
        st.session_state.data = pd.DataFrame([{
            "PLATFORMKEY": selected_platform,
            "MONTH": 1,
            "YEAR": 2024,
            "PASSENGERS": 0
        }])

    # Editable table
    edited_data = st.data_editor(
        st.session_state.data,
        column_config={
            "PLATFORMKEY": st.column_config.SelectboxColumn(
                "Platform Key",
                options=platform_keys,
                required=True,
            ),
            "MONTH": st.column_config.SelectboxColumn(
                "Month",
                options=list(range(1, 13)),
                required=True,
            ),
            "YEAR": st.column_config.NumberColumn(
                "Year",
                format="%d",
                min_value=2000,
                max_value=3000,
            ),
            "PASSENGERS": st.column_config.NumberColumn(
                "Passengers",
                format="%d",
                min_value=0,
            ),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor"
    )

    # Update session state
    st.session_state.data = edited_data

    # -------------------------------
    # Step 4: Show Output
    # -------------------------------
    st.subheader("Preview Data")

    if not edited_data.empty:
        st.dataframe(edited_data, use_container_width=True)

        st.subheader("JSON Output")
        st.json(edited_data.to_dict(orient="records"))
    else:
        st.info("No data entered yet.")

    # -------------------------------
    # Step 5: Submit Button
    # -------------------------------
    if st.button("Submit Data"):
        st.success("Data submitted successfully!")
        st.write(edited_data)

    # -------------------------------
    # Step 6: Clear Data Button
    # -------------------------------
    if st.button("Clear Data"):
        st.session_state.data = pd.DataFrame(
            columns=["PLATFORMKEY", "MONTH", "YEAR", "PASSENGERS"]
        )
        st.experimental_rerun()
