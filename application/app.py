import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
import custom_pyodbc

# Set Streamlit to wide mode
st.set_page_config(layout="wide")

# Function to connect to Access Database and load data from a query and convert to CSV
def convert_access_to_df(file_path):
    try:
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + file_path + ';'
        )
        conn = custom_pyodbc.connect(conn_str)
        query = 'SELECT * FROM [data query]'  # Replace with your query name
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading or converting data: {e}")
        return None

# App layout and functionality
st.title("Volume Data Analysis")

# Step 1: Upload the Access Database file
uploaded_file = st.file_uploader("Upload Volume.accdb file", type="accdb")
if uploaded_file:
    if uploaded_file.name.endswith('.accdb'):
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.accdb') as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name

        # Convert Access to DataFrame (done only once and stored in session state)
        if "df" not in st.session_state:
            with st.spinner("Converting Access database to DataFrame..."):
                st.session_state.df = convert_access_to_df(tmp_file_path)
        
        df = st.session_state.df
        
        if df is not None:
            st.success(f"Successfully loaded data from Access database.")
            
            # Step 2: Load data into memory for filtering and charting
            if df is not None and not df.empty:
                # Sidebar filters
                st.sidebar.header("Filters")
                
                # Create a copy of the original DataFrame for filtering
                filtered_df = df.copy()

                # Dynamically apply filters
                filters = {
                    "Units": "Units",
                    "Function_": "Function_",
                    "Cost Category": "Cost Category",
                    "T_dept_Vol": "T_dept_Vol",
                    "T_dept": "T_dept"
                }

                for key, column in filters.items():
                    if column in filtered_df.columns:
                        selected = st.sidebar.multiselect(key, options=filtered_df[column].unique())
                        if selected:
                            filtered_df = filtered_df[filtered_df[column].isin(selected)]

                # Handle missing values before plotting
                filtered_df = filtered_df.fillna(0)

                # Ensure Wk_no_ is treated as numeric
                filtered_df["Wk_no_"] = pd.to_numeric(filtered_df["Wk_no_"], errors='coerce')

                # Layout: Create two columns
                col1, col2 = st.columns([1, 1])  # Equal width columns for wide layout

                # Column 1: Time Series Graph and 2nd Bar Chart - Shifts by Day
                with col1:
                    # Time Series Graph with Plotly (Summing Value Total per Week and sorting by Wk_no_)
                    df_weekly = filtered_df.groupby("Wk_no_")["Value Total"].sum().reset_index()

                    # Ensure the data is sorted by Wk_no_
                    df_weekly = df_weekly.sort_values(by="Wk_no_")

                    # Create the time series plot without specifying width to let it adapt
                    fig1 = px.line(df_weekly, x="Wk_no_", y="Value Total", title="Time Series Graph of Value Total by Week No")
                    fig1.update_layout(xaxis_title="Week No", yaxis_title="Value Total", height=500)  # Adjust height only
                    st.plotly_chart(fig1, use_container_width=True)  # Use container width

                    # Define the correct order of days
                    day_order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
                    
                    # Convert Day_ column to categorical with correct order
                    filtered_df["Day_"] = pd.Categorical(filtered_df["Day_"], categories=day_order, ordered=True)

                    # 2nd Bar Chart: Shifts color coded by day using Plotly
                    df_grouped_day = filtered_df.groupby(["Day_", "Shifts"])["Value Total"].sum().reset_index()
                    fig3 = px.bar(df_grouped_day, x="Day_", y="Value Total", color="Shifts", title="Bar Chart of Volume by Shifts by Day")
                    fig3.update_layout(xaxis_title="Day", yaxis_title="Value Total", height=500)  # Adjust height only
                    st.plotly_chart(fig3, use_container_width=True)  # Use container width

                # Column 2: 1st Bar Chart - Shifts by Week
                with col2:
                    df_grouped = filtered_df.groupby(["Wk_no_", "Shifts"])["Value Total"].sum().reset_index()
                    fig2 = px.bar(df_grouped, x="Wk_no_", y="Value Total", color="Shifts", title="Bar Chart of Volume by Shifts by Week")
                    fig2.update_layout(xaxis_title="Week No", yaxis_title="Value Total", height=1000)  # Adjust height only
                    st.plotly_chart(fig2, use_container_width=True)  # Use container width

                # Option to download filtered dataset
                st.sidebar.subheader("Download Filtered Data")
                csv = filtered_df.to_csv(index=False)
                st.sidebar.download_button(
                    label="Download Filtered CSV",
                    data=csv,
                    file_name='filtered_data.csv',
                    mime='text/csv'
                )
            else:
                st.warning("No data to display. Please check your query or file format.")
        
        # Clean up the temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
    else:
        st.error("Please upload a valid .accdb file.")
