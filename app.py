import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Health Data Dashboard",
    page_icon="💉",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. CUSTOM STYLING & THEME (BACKGROUND COLOR)
# -----------------------------------------------------------------------------
# User requested background: #2A3D45 (Dark Gunmetal)
# inject CSS to change the background and ensure text is white/readable.
st.markdown(
    """
    <style>
    /* Main Background */
    .stApp {
        background-color: #2A3D45;
        color: white;
    }
    
    /* Sidebar Background (Optional: making it slightly darker or same) */
    [data-testid="stSidebar"] {
        background-color: #203038;
        color: white;
    }

    /* Text Colors for Headers and Metrics */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stMetricLabel, .stMetricValue {
        color: white !important;
    }
    
    /* Adjusting Metric Cards to look good on dark */
    [data-testid="stMetricValue"] {
        color: #FAE3E3 !important; /* Using one of your palette colors for numbers */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Custom Palette: Light Pink, Peach, Rosy Brown
CUSTOM_PALETTE = ["#FAE3E3", "#F7D4BC", "#CFA5B4"]

# Custom Heatmap Gradient
CUSTOM_HEATMAP_SCALE = [
    [0.0, "#FAE3E3"],
    [0.5, "#F7D4BC"],
    [1.0, "#CFA5B4"]
]


# 3. DATA LOADING
@st.cache_data
def load_data():
    df = pd.read_csv("vaccination_data.csv")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("The file 'vaccination_data.csv' was not found.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.header("Filter Options")

all_regions = sorted(df['Region'].unique())
selected_regions = st.sidebar.multiselect(
    "Select Regions:",
    options=all_regions,
    default=all_regions[:3]
)

chart_categories = ["Basic Antigen", "Summary Indicator"]
selected_category = st.sidebar.selectbox(
    "Select Category for Charts:",
    options=chart_categories,
    index=0
)

# -----------------------------------------------------------------------------
# 5. DATA FILTERING
# -----------------------------------------------------------------------------
df_filtered = df[df['Region'].isin(selected_regions)]
df_kpi = df_filtered[df_filtered['Category'] == "Demographic"]
df_charts = df_filtered[df_filtered['Category'] == selected_category]

# -----------------------------------------------------------------------------
# 6. DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

st.title("Philippine Vaccination Coverage 2022 Dashboard")
st.markdown("Analysis of immunization coverage for children aged 12-23 months. (2022)")

# --- SECTION 1: KEY METRICS ---
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

# Function to style plotly charts for dark background
def update_chart_layout(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),      # White text
        xaxis=dict(showgrid=False, color='white'),
        yaxis=dict(showgrid=True, gridcolor='#444', color='white') # Subtle grid
    )
    return fig

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
        labels={'Coverage_Rate': 'Coverage Rate (%)'},
        color_discrete_sequence=CUSTOM_PALETTE
    )
    fig_bar.update_layout(showlegend=False)
    fig_bar = update_chart_layout(fig_bar) # Apply Dark Theme Styling
    st.plotly_chart(fig_bar, use_container_width=True)

# CHART 2: Heatmap
with col2:
    st.subheader("Coverage Intensity Heatmap")
    heatmap_data = df_charts.pivot_table(index='Region', columns='Vaccine', values='Coverage_Rate')
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Vaccine Type", y="Region", color="Rate (%)"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale=CUSTOM_HEATMAP_SCALE,
        aspect="auto"
    )
    fig_heatmap.update_layout(title="Region vs. Vaccine Intensity")
    fig_heatmap = update_chart_layout(fig_heatmap) # Apply Dark Theme Styling
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# --- SECTION 3: REGIONAL LOLLIPOP CHARTS ---
st.markdown("### 🍭 Detailed Regional Breakdown")
st.caption("Detailed performance of each vaccine type for the selected regions.")

if not selected_regions:
    st.info("Please select at least one region.")
else:
    for region_name in selected_regions:
        region_data = df_charts[df_charts['Region'] == region_name].copy()
        region_data = region_data.sort_values(by="Coverage_Rate", ascending=True)

        fig_pop = go.Figure()

        # Draw lines (Stick) - Light Gray for visibility on dark
        for i, row in region_data.iterrows():
            fig_pop.add_shape(
                type="line",
                x0=0, y0=row['Vaccine'],
                x1=row['Coverage_Rate'], y1=row['Vaccine'],
                line=dict(color="lightgray", width=1) 
            )

        # Draw dots (Candy)
        fig_pop.add_trace(go.Scatter(
            x=region_data['Coverage_Rate'],
            y=region_data['Vaccine'],
            mode='markers+text',
            marker=dict(color='#CFA5B4', size=12), 
            text=region_data['Coverage_Rate'].astype(str) + '%',
            textposition="middle right",
            textfont=dict(color='white'),
            name=region_name,
            hoverinfo='x+y'
        ))

        fig_pop.update_layout(
            title=f"<b>{region_name}</b>: {selected_category} Coverage",
            xaxis_title="Coverage Rate (%)",
            yaxis_title="",
            showlegend=False,
            height=500,
            xaxis=dict(range=[0, max(100, region_data['Coverage_Rate'].max() + 15)])
        )
        fig_pop = update_chart_layout(fig_pop) # Apply Dark Theme Styling
        st.plotly_chart(fig_pop, use_container_width=True)

# -----------------------------------------------------------------------------
# 7. FOOTER, DOWNLOADS & ATTRIBUTION
# -----------------------------------------------------------------------------
st.markdown("---")

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
