import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # Added for Lollipop Chart

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Health Data Dashboard",
    page_icon="💉",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. DATA LOADING & PREPROCESSING
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 3. SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.header("Filter Options")

# A. Region Filter (Multiselect)
all_regions = sorted(df['Region'].unique())
selected_regions = st.sidebar.multiselect(
    "Select Regions:",
    options=all_regions,
    default=all_regions[:3]  # Default to top 3 for cleaner start
)

# B. Category Filter (Selectbox)
chart_categories = ["Basic Antigen", "Summary Indicator"]
selected_category = st.sidebar.selectbox(
    "Select Category for Charts:",
    options=chart_categories,
    index=0
)

# -----------------------------------------------------------------------------
# 4. DATA FILTERING LOGIC
# -----------------------------------------------------------------------------
# Filter by selected regions
df_filtered = df[df['Region'].isin(selected_regions)]

# Split Data:
# 1. Demographic Data (For KPIs)
df_kpi = df_filtered[df_filtered['Category'] == "Demographic"]

# 2. Chart Data (Based on selected category)
df_charts = df_filtered[df_filtered['Category'] == selected_category]

# -----------------------------------------------------------------------------
# 5. DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

# Title and Intro
st.title("Philippine Vaccination Coverage 2022 Dashboard")
st.markdown("Analysis of immunization coverage for children aged 12-23 months. (2022)")

# --- SECTION 1: KEY METRICS (KPIs) ---
st.markdown("### 📊 Key Demographics")

if not df_kpi.empty:
    total_children = df_kpi['Coverage_Rate'].sum()
    
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(
            label="Total Children Target (in Thousands)",
            value=f"{total_children:,.0f}k",
            delta="Target Population"
        )
    
    with kpi2:
        avg_coverage = df_charts['Coverage_Rate'].mean()
        st.metric(
            label=f"Avg. Coverage ({selected_category})",
            value=f"{avg_coverage:.2f}%"
        )
else:
    st.warning("No demographic data available for the selected filters.")

st.markdown("---")

# --- SECTION 2: COMPARATIVE CHARTS ---

col1, col2 = st.columns(2)

# CHART 1: Bar Chart
with col1:
    st.subheader(f"Average Rate by Region")
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

# CHART 2: Heatmap
with col2:
    st.subheader("Coverage Intensity Heatmap")
    
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

st.markdown("---")

# --- SECTION 3: REGIONAL LOLLIPOP CHARTS (NEW) ---
st.markdown("### Detailed Regional Breakdown")
st.caption("Detailed performance of each vaccine type for the selected regions.")

if not selected_regions:
    st.info("Please select at least one region in the sidebar to see the detailed breakdown.")
else:
    # Loop through each selected region to create a separate chart
    for region_name in selected_regions:
        # Filter data for this specific region
        region_data = df_charts[df_charts['Region'] == region_name].copy()
        
        # Sort data by Coverage Rate so the chart looks organized (ascending)
        region_data = region_data.sort_values(by="Coverage_Rate", ascending=True)

        # Create the Lollipop Chart using Graph Objects
        fig_pop = go.Figure()

        # 1. Draw the lines (the stick)
        # We iterate through the rows to draw a line from 0 to the value
        for i, row in region_data.iterrows():
            fig_pop.add_shape(
                type="line",
                x0=0, y0=row['Vaccine'],
                x1=row['Coverage_Rate'], y1=row['Vaccine'],
                line=dict(color="gray", width=1)
            )

        # 2. Draw the dots (the candy)
        fig_pop.add_trace(go.Scatter(
            x=region_data['Coverage_Rate'],
            y=region_data['Vaccine'],
            mode='markers+text',
            marker=dict(color="#F7B0EC", size=12), # Streamlit Red color
            text=region_data['Coverage_Rate'].astype(str) + '%',
            textposition="middle right",
            name=region_name,
            hoverinfo='x+y'
        ))

        # Layout adjustments
        fig_pop.update_layout(
            title=f"<b>{region_name}</b>: {selected_category} Coverage",
            xaxis_title="Coverage Rate (%)",
            yaxis_title="", # Hide y-axis title as it's self-explanatory
            showlegend=False,
            height=500, # Fixed height for consistency
            xaxis=dict(range=[0, max(100, region_data['Coverage_Rate'].max() + 10)]) # Ensure X axis fits 0-100+
        )
        
        st.plotly_chart(fig_pop, use_container_width=True)


# -----------------------------------------------------------------------------
# 6. FOOTER, DOWNLOADS & ATTRIBUTION
# -----------------------------------------------------------------------------
st.markdown("---")

# Convert dataframe to CSV for download
csv_data = df.to_csv(index=False).encode('utf-8')

f1, f2 = st.columns([1, 4])

with f1:
    st.download_button(
        label="📥 Download Data",
        data=csv_data,
        file_name="vaccination_data.csv",
        mime="text/csv",
    )

with f2:
    st.markdown(
        """
        **Data Source:** [OpenStat PSA - Vaccination by Region, Year and Type of Vaccination of Children Age 12-23 months](https://openstat.psa.gov.ph/)  
        *Dashboard created for Health Informatics (ITE3) Finals.*
        """
    )
