import streamlit as st
import pandas as pd
import plotly.express as px

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Health Data Dashboard: Immunization Coverage for Children Aged 12-23 Months",
    page_icon="💉",
    layout="wide"
)


# 2. DATA LOADING & PREPROCESSING

@st.cache_data
def load_data():
    # Load the dataset
    df = pd.read_csv("vaccination_data.csv")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("The file 'vaccination_data.csv' was not found. Please ensure it is in the same directory as app.py.")
    st.stop()


# 3. SIDEBAR FILTERS

st.sidebar.header("Filter Options")

# A. Region Filter (Multiselect)
# sort unique regions for better UX
all_regions = sorted(df['Region'].unique())
selected_regions = st.sidebar.multiselect(
    "Select Regions:",
    options=all_regions,
    default=all_regions[:5]  # Default to first 5 to avoid overcrowding initially
)

# B. Category Filter (Selectbox)

chart_categories = ["Basic Antigen", "Summary Indicator"]
selected_category = st.sidebar.selectbox(
    "Select Category for Charts:",
    options=chart_categories,
    index=0
)


# 4. DATA FILTERING LOGIC

# Filter 1: Filter by selected regions
df_filtered = df[df['Region'].isin(selected_regions)]

# Split Data:
# 1. Demographic Data (For KPIs)
df_kpi = df_filtered[df_filtered['Category'] == "Demographic"]

# 2. Chart Data (Based on selected category)
df_charts = df_filtered[df_filtered['Category'] == selected_category]


# 5. DASHBOARD LAYOUT


# Title and Intro
st.title("Philippine Vaccination Coverage 2022 Dashboard")
st.markdown("Analysis of immunization coverage for children aged 12-23 months. (2022)")

# --- SECTION 1: KEY METRICS (KPIs) ---
st.markdown("### 📊 Key Demographics")
# Calculate Total Children (Target Population)
# Note: The data source says these values are "in thousands".
# sum the values for the selected regions.
if not df_kpi.empty:
    total_children = df_kpi['Coverage_Rate'].sum()
    
    # Create columns for metrics (centering it looks better)
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(
            label="Total Children Target (in Thousands)",
            value=f"{total_children:,.0f}k",
            delta="Target Population"
        )
    
    with kpi2:
        # Dynamic Metric: Average Coverage for the selected category
        avg_coverage = df_charts['Coverage_Rate'].mean()
        st.metric(
            label=f"Avg. Coverage ({selected_category})",
            value=f"{avg_coverage:.2f}%"
        )
else:
    st.warning("No demographic data available for the selected filters.")

st.markdown("---")

# --- SECTION 2: CHARTS ---

# Create two columns for the charts
col1, col2 = st.columns(2)

# CHART 1: Bar Chart (Average Vaccination Rate by Region)
with col1:
    st.subheader(f"Average Rate by Region")
    # Group by Region to get the average rate
    df_bar = df_charts.groupby('Region')['Coverage_Rate'].mean().reset_index()
    
    fig_bar = px.bar(
        df_bar,
        x='Region',
        y='Coverage_Rate',
        color='Region',
        text_auto='.1f',
        title=f"Avg. {selected_category} Coverage",
        labels={'Coverage_Rate': 'Coverage Rate (%)'}
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# CHART 2: Heatmap (Region vs Vaccine Type)
with col2:
    st.subheader("Coverage Intensity Heatmap")
    
    # Pivot the data for the heatmap: Rows=Region, Cols=Vaccine, Values=Rate
    # pivot_table to handle any potential duplicates cleanly
    heatmap_data = df_charts.pivot_table(
        index='Region', 
        columns='Vaccine', 
        values='Coverage_Rate'
    )
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Vaccine Type", y="Region", color="Rate (%)"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale="Viridis",
        aspect="auto" 
    )
    fig_heatmap.update_layout(title="Region vs. Vaccine Intensity")
    st.plotly_chart(fig_heatmap, use_container_width=True)



# 6. FOOTER, DOWNLOADS & ATTRIBUTION
st.markdown("---")

# Convert dataframe to CSV for download
csv_data = df.to_csv(index=False).encode('utf-8')

# Create columns to align the button and text if preferred, or just list them
f1, f2 = st.columns([1, 4])

with f1:
    # Download Button
    st.download_button(
        label="📥 Download Data",
        data=csv_data,
        file_name="vaccination_data.csv",
        mime="text/csv",
    )

with f2:
    # Attribution with Link
    st.markdown(
        """
        **Data Source:** [OpenStat PSA - Vaccination by Region, Year and Type of Vaccination of Children Age 12-23 months](https://openstat.psa.gov.ph/)  
        *Dashboard created for Health Informatics (ITE3) Finals.*
        """

    )

