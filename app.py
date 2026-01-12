import streamlit as st
import tempfile
import os
from pathlib import Path
import time
from datetime import datetime
from codescan import CodeAnalyzer
from utils import display_code_with_highlights, create_file_tree
from styles import apply_custom_styles
import base64
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import pandas as pd
import zipfile

# Page config
st.set_page_config(
    page_title="CodeLens - Code Utility",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styles
apply_custom_styles()

# Creator information
st.sidebar.markdown("""
### Created by:
**Zensar Project Diamond Team**
""")

def get_file_download_link(file_path):
    """Generate a download link for a file"""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        data = f.read()
    b64 = base64.b64encode(data.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{os.path.basename(file_path)}" class="download-button">Download</a>'

def parse_timestamp_from_filename(filename):
    """Extract timestamp from filename format app_name_code_analysis_YYYYMMDD_HHMMSS"""
    try:
        # Extract date and time part
        date_time_str = filename.split('_')[-2] + '_' + filename.split('_')[-1].split('.')[0]
        return datetime.strptime(date_time_str, '%Y%m%d_%H%M%S')
    except:
        return datetime.min

def create_dashboard_charts(results):
    """Create visualization charts for the dashboard"""
    # Summary Stats at the top
    st.subheader("Summary")
    stats_cols = st.columns(4)
    stats_cols[0].metric("Files Analyzed", results['summary']['files_analyzed'])
    stats_cols[1].metric("Demographic Fields", results['summary']['demographic_fields_found'])
    stats_cols[2].metric("Integration Patterns", results['summary']['integration_patterns_found'])
    stats_cols[3].metric("Unique Fields", len(results['summary']['unique_demographic_fields']))

    st.markdown("----")  # Add a separator line

    # 1. Demographic Fields Distribution - Side by side charts
    field_frequencies = {}
    for file_data in results['demographic_data'].values():
        for field_name, data in file_data.items():
            if field_name not in field_frequencies:
                field_frequencies[field_name] = len(data['occurrences'])
            else:
                field_frequencies[field_name] += len(data['occurrences'])

    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)

    with col1:
        # Pie Chart
        fig_demo_pie = px.pie(
            values=list(field_frequencies.values()),
            names=list(field_frequencies.keys()),
            title="Distribution of Demographic Fields (Pie Chart)",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_demo_pie, use_container_width=True)

    with col2:
        # Bar Chart
        fig_demo_bar = px.bar(
            x=list(field_frequencies.keys()),
            y=list(field_frequencies.values()),
            title="Distribution of Demographic Fields (Bar Chart)",
            labels={'x': 'Field Name', 'y': 'Occurrences'},
            color=list(field_frequencies.keys()),
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_demo_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_demo_bar, use_container_width=True)

    # 2. Files by Language Bar Chart
    file_extensions = [Path(file['file_path']).suffix for file in results['summary']['file_details']]
    file_counts = Counter(file_extensions)

    fig_files = px.bar(
        x=list(file_counts.keys()),
        y=list(file_counts.values()),
        title="Files by Language",
        labels={'x': 'File Extension', 'y': 'Count'},
        color=list(file_counts.keys()),
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_files.update_layout(showlegend=False)
    st.plotly_chart(fig_files)

    # 3. Integration Patterns Line Graph
    pattern_types = Counter(pattern['pattern_type'] for pattern in results['integration_patterns'])

    fig_patterns = go.Figure()
    fig_patterns.add_trace(go.Scatter(
        x=list(pattern_types.keys()),
        y=list(pattern_types.values()),
        mode='lines+markers',
        name='Pattern Count',
        line=dict(color='#0066cc', width=2),
        marker=dict(size=10)
    ))
    fig_patterns.update_layout(
        title="Integration Patterns Distribution",
        xaxis_title="Pattern Type",
        yaxis_title="Count",
        showlegend=False
    )
    st.plotly_chart(fig_patterns)

    # 4. Files and Fields Correlation
    fig_correlation = go.Figure()

    # Extract data for each file
    file_names = [os.path.basename(detail['file_path']) for detail in results['summary']['file_details']]
    demographic_counts = [detail['demographic_fields_found'] for detail in results['summary']['file_details']]
    integration_counts = [detail['integration_patterns_found'] for detail in results['summary']['file_details']]

    fig_correlation.add_trace(go.Bar(
        name='Demographic Fields',
        x=file_names,
        y=demographic_counts,
        marker_color='#0066cc'
    ))
    fig_correlation.add_trace(go.Bar(
        name='Integration Patterns',
        x=file_names,
        y=integration_counts,
        marker_color='#90EE90'
    ))

    fig_correlation.update_layout(
        title="Fields and Patterns by File",
        xaxis_title="File Name",
        yaxis_title="Count",
        barmode='group'
    )
    st.plotly_chart(fig_correlation)

def main():
    st.title("🔍 CodeLens")
    st.markdown("### Code Analysis Utility")

    # Sidebar
    # Add navigation in sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Code Analysis", "Excel Demographic Analysis", "Documentation"]
    )

    if page == "Code Analysis":
        st.sidebar.header("Analysis Settings")
        # Input method selection
        input_method = st.sidebar.radio(
            "Choose Input Method",
            ["Upload Files", "Repository Path"]
        )
    elif page == "Excel Demographic Analysis":
        st.header("📊 Excel Demographic Data Analysis")
        st.markdown("Upload an Excel file to analyze demographic data based on attr_description and export to 20 files.")

        # Sample file download
        st.subheader("📋 Sample Excel Format")
        st.markdown("""
        **Required Columns:** `table_name`, `attr_name`, `business_name`, `attr_description`

        Download the sample Excel file to understand the expected format:
        """)

        if os.path.exists('sample_demographic_data.xlsx'):
            with open('sample_demographic_data.xlsx', 'rb') as f:
                st.download_button(
                    label="📥 Download Sample Excel Format",
                    data=f.read(),
                    file_name="sample_demographic_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Sample file not found. Please create it first by running the application setup.")

        st.markdown("---")

        # Application name input for Excel analysis
        excel_app_name = st.sidebar.text_input("Application Name for Excel Analysis", "C360_Demographics")

        # Excel file upload
        uploaded_excel = st.sidebar.file_uploader(
            "Upload Excel File",
            type=['xlsx', 'xls'],
            help="Upload an Excel file containing demographic data with attr_description column"
        )

        if uploaded_excel and st.sidebar.button("Analyze Excel Data"):
            try:
                # Save uploaded file temporarily
                temp_excel_path = f"temp_{uploaded_excel.name}"
                with open(temp_excel_path, 'wb') as f:
                    f.write(uploaded_excel.getbuffer())

                with st.spinner("Analyzing Excel demographic data..."):
                    analyzer = CodeAnalyzer(".", excel_app_name)
                    excel_results = analyzer.analyze_excel_demographic_data(temp_excel_path)

                    # Display results
                    st.subheader("Excel Analysis Results")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Records", excel_results['summary']['total_records'])
                    col2.metric("Demographic Records", excel_results['summary']['demographic_fields_found'])
                    col3.metric("Files Exported", len(excel_results['summary']['exported_files']))

                    if excel_results['demographic_data']:
                        st.subheader("Sample Demographic Data")
                        # Display first 10 records as preview
                        sample_data = excel_results['demographic_data'][:10]
                        df_sample = pd.DataFrame(sample_data)
                        st.dataframe(df_sample)

                        st.subheader("Exported Files")
                        st.success(f"Successfully exported demographic data to {len(excel_results['summary']['exported_files'])} files:")
                        for i, filename in enumerate(excel_results['summary']['exported_files'], 1):
                            st.text(f"{i}. {filename}")
                    else:
                        st.warning("No demographic data found in the uploaded Excel file.")

                # Clean up temp file
                os.remove(temp_excel_path)

            except Exception as e:
                st.error(f"Error analyzing Excel file: {str(e)}")
                if os.path.exists(temp_excel_path):
                    os.remove(temp_excel_path)

        return

    elif page == "Documentation":
        st.header("📖 Documentation")

        doc_section = st.sidebar.radio(
            "Select Section",
            ["Overview", "README File", "Installation Steps", "Features"]
        )

        if doc_section == "Overview":
            st.subheader("CodeLens - Advanced Code Analysis Utility")
            st.markdown("""
            ### Key Features
            - Demographic data detection in source code
            - Integration pattern analysis
            - ZIP folder upload support for bulk file analysis
            - Excel demographic data analysis with attr_description
            - Export to multiple files (20 files for Excel analysis)
            - Interactive dashboards
            - Detailed reports generation
            - Multi-language support (Java, Python, JavaScript, TypeScript, C#, PHP, Ruby, XSD)
            - Advanced pattern recognition with fuzzy matching algorithms

            ### Built by Zensar Project Diamond Team
            A comprehensive web-based source code analysis tool designed to extract demographic data and integration patterns across multiple programming languages.
            """)

        elif doc_section == "README File":
            st.subheader("📄 Complete README Documentation")

            # Read and display the README file content
            try:
                with open('README.md', 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                st.markdown(readme_content)
            except FileNotFoundError:
                st.error("README.md file not found")
            except Exception as e:
                st.error(f"Error reading README.md: {str(e)}")

        elif doc_section == "Installation Steps":
            st.subheader("🛠 Installation & Setup Guide")
            
            st.markdown("""
            ### Prerequisites
            - **Python 3.11+** installed on your system
            - **Web Browser** with JavaScript enabled

            ### Installation Steps
            1. **Download/Clone** the project files to your local machine
            2. **Install Dependencies**:
               ```bash
               pip install streamlit plotly pandas openpyxl pygments fuzzywuzzy python-levenshtein
               ```
            3. **Run the Application**:
               ```bash
               streamlit run app.py --server.address 0.0.0.0 --server.port 5000
               ```
            4. **Access**: Navigate to `http://localhost:5000` in your browser

            ### Alternative Installation
            You can also install dependencies using pip with the following packages:
            - streamlit - Web application framework
            - plotly - Interactive visualizations
            - pandas - Data manipulation and analysis
            - openpyxl - Excel file handling
            - pygments - Code syntax highlighting
            - fuzzywuzzy - Fuzzy string matching
            - python-levenshtein - String distance calculations

            ### Quick Start Guide
            This application is designed to run seamlessly on any Python environment. Simply:
            1. **Download the project** files to your system
            2. **Install dependencies** using pip as shown above
            3. **Run the application** using the streamlit command
            4. **Access your application** at `http://0.0.0.0:5000`

            ### Dependencies
            The following packages are automatically installed:
            - `streamlit` - Web application framework
            - `plotly` - Interactive visualizations
            - `pandas` - Data manipulation and analysis
            - `openpyxl` - Excel file handling
            - `pygments` - Code syntax highlighting
            - `fuzzywuzzy` - Fuzzy string matching
            - `python-levenshtein` - String distance calculations
            """)

        elif doc_section == "Features":
            st.subheader("🚀 Detailed Features Overview")

            st.markdown("""
            ### Core Analysis Capabilities
            - **Multi-Language Support**: Analyzes code across 8+ programming languages
              - Java, Python, JavaScript, TypeScript, C#, PHP, Ruby, XSD
            - **Demographic Data Detection**: Advanced pattern recognition for personal information
            - **Integration Pattern Analysis**: Identifies REST APIs, SOAP services, database operations, messaging systems
            - **ZIP File Support**: Upload entire project folders as ZIP files for bulk analysis
            - **Excel Analysis**: Demographic data extraction from Excel files using fuzzy matching algorithms

            ### Data Types Detected

            #### Personal Information
            - **Names**: Embossed Name, Primary Name, Secondary Name, Legal Name, DBA Name, Double Byte Name
            - **Identity**: Gender, Date of Birth (DOB), Government IDs, SSN, Tax ID, Passport
            - **Contact Information**: Multiple phone types, email addresses, preference language

            #### Address Information  
            - **Multiple Address Types**: Home, Business, Alternate, Temporary, Other
            - **Address Arrays**: Support for multiple address entries

            #### Advanced Analysis
            - **Fuzzy Matching Algorithm**: Identifies demographic data with variations in naming
            - **Pattern Confidence Scoring**: Provides match reliability metrics
            - **Export Capabilities**: Generate reports in multiple formats (HTML, JSON, Excel)

            ### Interactive Dashboard
            - **Visual Analytics**: Pie charts, bar graphs, line charts for data distribution
            - **File Statistics**: Language distribution and analysis metrics
            - **Integration Patterns**: Visual representation of detected patterns
            - **Real-time Analysis**: Live progress tracking during code scanning

            ### Export & Reporting
            - **Multi-Format Export**: HTML, JSON, Excel support
            - **Batch Processing**: Handle multiple files simultaneously
            - **Historical Reports**: Timestamped report management
            - **Download Management**: Organized file download system
            """)

            # Add download button for README file
            st.markdown("---")
            st.subheader("📥 Download Documentation")
            try:
                with open('README.md', 'rb') as f:
                    st.download_button(
                        label="Download Complete README.md",
                        data=f.read(),
                        file_name="CodeLens_README.md",
                        mime="text/markdown"
                    )
            except FileNotFoundError:
                st.info("README.md file not available for download")
        return

    # Application name input
    app_name = st.sidebar.text_input("Application Name", "MyApp")

    analysis_triggered = False
    temp_dir = None

    if input_method == "Upload Files":
        uploaded_files = st.sidebar.file_uploader(
            "Upload Code Files or ZIP Folder",
            accept_multiple_files=True,
            type=['py', 'java', 'js', 'ts', 'cs', 'php', 'rb', 'xsd', 'zip']
        )

        if uploaded_files:
            temp_dir = tempfile.mkdtemp()
            for uploaded_file in uploaded_files:
                if uploaded_file.name.endswith('.zip'):
                    # Handle ZIP file extraction
                    import zipfile
                    zip_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(zip_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # Extract ZIP contents
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)

                    # Remove the ZIP file after extraction
                    os.remove(zip_path)
                else:
                    # Handle regular files
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

            if st.sidebar.button("Run Analysis"):
                analysis_triggered = True
                repo_path = temp_dir

    else:
        repo_path = st.sidebar.text_input("Enter Repository Path")
        if repo_path and st.sidebar.button("Run Analysis"):
            analysis_triggered = True

    if analysis_triggered:
        try:
            with st.spinner("Analyzing code..."):
                analyzer = CodeAnalyzer(repo_path, app_name)
                progress_bar = st.progress(0)

                # Run analysis
                results = analyzer.scan_repository()
                progress_bar.progress(100)

                # Create tabs for Dashboard, Analysis Results, and Export Reports
                tab1, tab2, tab3 = st.tabs(["Dashboard", "Analysis Results", "Export Reports"])

                with tab1:
                    st.header("Analysis Dashboard")
                    st.markdown("""
                    This dashboard provides visual insights into the code analysis results,
                    showing distributions of files, demographic fields, and integration patterns.
                    """)
                    create_dashboard_charts(results)

                with tab2:
                    # Summary Stats
                    st.subheader("Summary")
                    stats_cols = st.columns(4)
                    stats_cols[0].metric("Files Analyzed", results['summary']['files_analyzed'])
                    stats_cols[1].metric("Demographic Fields", results['summary']['demographic_fields_found'])
                    stats_cols[2].metric("Integration Patterns", results['summary']['integration_patterns_found'])
                    stats_cols[3].metric("Unique Fields", len(results['summary']['unique_demographic_fields']))

                    # Demographic Fields Summary Table
                    st.subheader("Demographic Fields Summary")
                    demographic_files = [f for f in results['summary']['file_details'] if f['demographic_fields_found'] > 0]
                    if demographic_files:
                        cols = st.columns([0.5, 2, 1, 2])
                        cols[0].markdown("**#**")
                        cols[1].markdown("**File Analyzed**")
                        cols[2].markdown("**Fields Found**")
                        cols[3].markdown("**Fields**")

                        for idx, file_detail in enumerate(demographic_files, 1):
                            file_path = file_detail['file_path']
                            unique_fields = []
                            if file_path in results['demographic_data']:
                                unique_fields = list(results['demographic_data'][file_path].keys())

                            cols = st.columns([0.5, 2, 1, 2])
                            cols[0].text(str(idx))
                            cols[1].text(os.path.basename(file_path))
                            cols[2].text(str(file_detail['demographic_fields_found']))
                            cols[3].text(', '.join(unique_fields))

                    # Integration Patterns Summary Table
                    st.subheader("Integration Patterns Summary")
                    integration_files = [f for f in results['summary']['file_details'] if f['integration_patterns_found'] > 0]
                    if integration_files:
                        cols = st.columns([0.5, 2, 1, 2])
                        cols[0].markdown("**#**")
                        cols[1].markdown("**File Name**")
                        cols[2].markdown("**Patterns Found**")
                        cols[3].markdown("**Pattern Details**")

                        for idx, file_detail in enumerate(integration_files, 1):
                            file_path = file_detail['file_path']
                            pattern_details = set()
                            for pattern in results['integration_patterns']:
                                if pattern['file_path'] == file_path:
                                    pattern_details.add(f"{pattern['pattern_type']}: {pattern['sub_type']}")

                            cols = st.columns([0.5, 2, 1, 2])
                            cols[0].text(str(idx))
                            cols[1].text(os.path.basename(file_path))
                            cols[2].text(str(file_detail['integration_patterns_found']))
                            cols[3].text(', '.join(pattern_details))

                with tab3:
                    st.header("Available Reports")

                    # Get all report files and filter by app_name
                    report_files = [
                        f for f in os.listdir()
                        if f.endswith('.html')
                        and 'CodeLens' in f
                        and f.startswith(app_name)
                    ]

                    # Sort files by timestamp in descending order
                    report_files.sort(key=parse_timestamp_from_filename, reverse=True)

                    if report_files:
                        # Create a table with five columns
                        cols = st.columns([1, 3, 2, 2, 2])
                        cols[0].markdown("**S.No**")
                        cols[1].markdown("**File Name**")
                        cols[2].markdown("**Date**")
                        cols[3].markdown("**Time**")
                        cols[4].markdown("**Download**")

                        # List all reports
                        for idx, report_file in enumerate(report_files, 1):
                            cols = st.columns([1, 3, 2, 2, 2])

                            # Serial number column
                            cols[0].text(f"{idx}")

                            # File name column without .html extension
                            display_name = report_file.replace('.html', '')
                            cols[1].text(display_name)

                            # Extract timestamp and format date and time separately
                            timestamp = parse_timestamp_from_filename(report_file)
                            # Date in DD-MMM-YYYY format
                            cols[2].text(timestamp.strftime('%d-%b-%Y'))
                            # Time in 12-hour format with AM/PM
                            cols[3].text(timestamp.strftime('%I:%M:%S %p'))

                            # Download button column (last)
                            cols[4].markdown(
                                get_file_download_link(report_file),
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("No reports available for this application.")

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")

        finally:
            if temp_dir:
                import shutil
                shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()