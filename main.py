import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime

# Theme toggle
st.set_page_config(initial_sidebar_state="expanded", layout="wide")
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# Sidebar for settings and data cleaning
with st.sidebar:
    st.title("Settings")
    if st.button("Toggle Theme 🌓"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
    
    # Apply theme
    if st.session_state.theme == "dark":
        st.markdown("""
            <style>
                .stApp {
                    background-color: #1E1E1E;
                    color: white;
                }
            </style>
        """, unsafe_allow_html=True)
    
    st.title("Data Cleaning Options")
    handle_missing = st.selectbox(
        "Handle Missing Values",
        ["Drop", "Fill with Mean", "Fill with Median", "Fill with Zero", "None"]
    )
    remove_duplicates = st.checkbox("Remove Duplicate Rows")

st.title("Advanced Data Dashboard")

# Multiple file upload
uploaded_files = st.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    # Dictionary to store multiple dataframes
    dfs = {}
    
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_csv(uploaded_file, parse_dates=True)
            
            # Data Cleaning
            if handle_missing != "None":
                if handle_missing == "Drop":
                    df = df.dropna()
                elif handle_missing == "Fill with Mean":
                    df = df.fillna(df.mean(numeric_only=True))
                elif handle_missing == "Fill with Median":
                    df = df.fillna(df.median(numeric_only=True))
                elif handle_missing == "Fill with Zero":
                    df = df.fillna(0)
            
            if remove_duplicates:
                df = df.drop_duplicates()
            
            dfs[uploaded_file.name] = df
            
            # Data Statistics Cards
            st.header(f"Dataset: {uploaded_file.name}")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("Missing Values", df.isna().sum().sum())
            with col4:
                st.metric("Duplicate Rows", len(df) - len(df.drop_duplicates()))
            
            # Data Column Analysis
            st.subheader("Column Analysis")
            col_analysis = []
            for col in df.columns:
                analysis = {
                    "Column": col,
                    "Type": str(df[col].dtype),
                    "Missing": df[col].isna().sum(),
                    "Unique Values": df[col].nunique()
                }
                if pd.api.types.is_numeric_dtype(df[col]):
                    analysis.update({
                        "Mean": df[col].mean(),
                        "Median": df[col].median(),
                        "Std": df[col].std()
                    })
                col_analysis.append(analysis)
            st.dataframe(pd.DataFrame(col_analysis))
            
            # Data Preview
            st.subheader("Data Preview")
            st.write(df.head())
            
            # Export Data Button
            def get_csv_download_link(df, filename):
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="{filename}_exported.csv">Download CSV File</a>'
                return href
            
            st.markdown(get_csv_download_link(df, uploaded_file.name.split('.')[0]), unsafe_allow_html=True)
            
            # Plotting Section
            st.subheader("Advanced Plotting")
            
            # Convert numeric columns if possible
            for col in df.columns:
                try:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    continue
            
            numeric_columns = df.select_dtypes(include=['float64', 'int64', 'float32', 'int32']).columns.tolist()
            
            if len(numeric_columns) >= 1:
                # Chart Type Selection
                chart_type = st.selectbox(
                    "Select Chart Type",
                    ["Line Chart", "Bar Chart", "Scatter Plot", "Pie Chart", "Box Plot", "Violin Plot"],
                    key=f"chart_type_{uploaded_file.name}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    x_column = st.selectbox("Select x-axis column", df.columns.tolist(), key=f'x_axis_{uploaded_file.name}')
                with col2:
                    y_column = st.selectbox("Select y-axis column", numeric_columns, key=f'y_axis_{uploaded_file.name}')
                
                if st.button("Generate Plot", key=f"plot_{uploaded_file.name}"):
                    try:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        if chart_type == "Line Chart":
                            sns.lineplot(data=df, x=x_column, y=y_column, ax=ax)
                        elif chart_type == "Bar Chart":
                            sns.barplot(data=df, x=x_column, y=y_column, ax=ax)
                        elif chart_type == "Scatter Plot":
                            sns.scatterplot(data=df, x=x_column, y=y_column, ax=ax)
                        elif chart_type == "Pie Chart":
                            plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
                        elif chart_type == "Box Plot":
                            sns.boxplot(data=df, x=x_column, y=y_column, ax=ax)
                        elif chart_type == "Violin Plot":
                            sns.violinplot(data=df, x=x_column, y=y_column, ax=ax)
                        
                        plt.title(f'{chart_type}: {y_column} vs {x_column}')
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
                        
                    except Exception as e:
                        st.error(f"""
                            Error generating plot. Please check that:
                            1. The selected columns contain valid data for the chosen chart type
                            2. There are no missing values
                            3. The data is properly formatted
                            
                            Technical details: {str(e)}
                        """)
            
            # Comparison of multiple files
            if len(dfs) > 1:
                st.subheader("Dataset Comparison")
                comparison_stats = []
                for name, df in dfs.items():
                    stats = {
                        "Dataset": name,
                        "Rows": len(df),
                        "Columns": len(df.columns),
                        "Missing Values": df.isna().sum().sum(),
                        "Memory Usage (MB)": df.memory_usage().sum() / 1024 / 1024
                    }
                    comparison_stats.append(stats)
                st.dataframe(pd.DataFrame(comparison_stats))
        
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
else:
    st.write("Upload one or more CSV files to begin analysis")
