import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Health Data Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI Polish
st.markdown("""
    <style>
        /* Main Background and Text */
        .reportview-container {
            background: #fdfdfd;
        }
        /* Metrics Styling */
        div[data-testid="stMetric"] {
            background-color: #f0f2f6;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricLabel"] {
            color: #555;
            font-size: 0.9rem;
        }
        div[data-testid="stMetricValue"] {
            color: #2E86AB; /* Primary Teal */
            font-weight: 700;
        }
        /* Header Styling */
        h1, h2, h3 {
            color: #2c3e50;
            font-family: 'Segoe UI', sans-serif;
        }
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
        /* Plotly Chart Background */
        .js-plotly-plot .plotly .modebar {
            opacity: 0.5;
        }
    </style>
""", unsafe_allow_html=True)

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
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    st.markdown("---")
    
    # A. Region Filter (Multiselect)
    all_regions = sorted(df['Region'].unique())
    st.subheader("📍 Geography")
    selected_regions = st.multiselect(
        "Select Regions:",
        options=all_regions,
        default=all_regions[:3]  # Default to top 3
    )

    # B. Category Filter (Selectbox)
    st.subheader("📊 Data Type")
    chart_categories = ["Basic Antigen", "Summary Indicator"]
    selected_category = st.selectbox(
        "Select Category:",
        options=chart_categories,
        index=0
    )
    
    st.markdown("---")
    st.caption("v1.2 | Health Informatics")

# -----------------------------------------------------------------------------
# 4. DATA FILTERING LOGIC
# -----------------------------------------------------------------------------
# Filter by selected regions
df_filtered = df[df['Region'].isin(selected_regions)]

# Split Data
df_kpi = df_filtered[df_filtered['Category'] == "Demographic"]
df_charts = df_filtered[df_filtered['Category'] == selected_category]

# -----------------------------------------------------------------------------
# 5. DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

# Title and Intro
st.title("🇵🇭 Philippine Vaccination Coverage (2022)")
st.markdown(f"""
    <div style='background-color: #e8f4f8; padding: 15px; border-radius: 10px; border-left: 5px solid #2E86AB; margin-bottom: 20px;'>
        Analysis of immunization coverage for children aged 12-23 months. 
        Currently viewing data for: <b>{selected_category}</b>
    </div>
""", unsafe_allow_html=True)

# --- SECTION 1: KEY METRICS (KPIs) ---
st.markdown("### 📈 Key Performance Indicators")

if not df_kpi.empty:
    total_children = df_kpi['Coverage_Rate'].sum()
    avg_coverage = df_charts['Coverage_Rate'].mean()
    
    # Using 3 columns for better spacing (Middle one for gap if needed, or add a 3rd metric)
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(
            label="Total Children Target",
            value=f"{total_children:,.0f}k",
            delta="Target Population",
            delta_color="off" # Grey delta
        )
    
    with kpi2:
        st.metric(
            label=f"Avg. Coverage Rate",
            value=f"{avg_coverage:.2f}%",
            delta=f"Based on {len(selected_regions)} Regions"
        )
        
    with kpi3:
         # Placeholder for a potential 3rd metric, or just visual balance
         max_val = df_charts['Coverage_Rate'].max()
         st.metric(
            label="Highest Recorded Rate",
            value=f"{max_val:.2f}%"
         )

else:
    st.warning("No demographic data available for the selected filters.")

st.markdown("---")

# --- SECTION 2: COMPARATIVE CHARTS ---

col1, col2 = st.columns([1, 1])

# CHART 1: Bar Chart
with col1:
    st.subheader(f"Regional Comparison")
    df_bar = df_charts.groupby('Region')['Coverage_Rate'].mean().reset_index().sort_values("Coverage_Rate", ascending=False)
    
    fig_bar = px.bar(
        df_bar,
        x='Region',
        y='Coverage_Rate',
        color='Coverage_Rate', # Gradient coloring based on value
        color_continuous_scale='Teal', # Professional Teal scale
        text_auto='.1f',
        title=f"Average Coverage by Region",
        labels={'Coverage_Rate': 'Rate (%)'}
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        yaxis=dict(showgrid=True, gridcolor='#eee'),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# CHART 2: Heatmap
with col2:
    st.subheader("Coverage Intensity Matrix")
    
    heatmap_data = df_charts.pivot_table(
        index='Region', 
        columns='Vaccine', 
        values='Coverage_Rate'
    )
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Vaccine", y="Region", color="Rate (%)"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale="Blues", # Softer Blue scale
        aspect="auto"
    )
    fig_heatmap.update_layout(
        title="Heatmap: Vaccine vs. Region",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# --- SECTION 3: REGIONAL LOLLIPOP CHARTS ---
st.markdown("### 🔍 Detailed Regional Breakdown")
st.caption("Granular performance view per vaccine type.")

if not selected_regions:
    st.info("👈 Please select at least one region in the sidebar to see the detailed breakdown.")
else:
    # Use an expander or container to organize multiple charts if list is long
    for region_name in selected_regions:
        with st.container():
            # Filter data for this specific region
            region_data = df_charts[df_charts['Region'] == region_name].copy()
            region_data = region_data.sort_values(by="Coverage_Rate", ascending=True)

            # Create the Lollipop Chart
            fig_pop = go.Figure()

            # 1. Draw the lines (Stick) - Light Grey
            for i, row in region_data.iterrows():
                fig_pop.add_shape(
                    type="line",
                    x0=0, y0=row['Vaccine'],
                    x1=row['Coverage_Rate'], y1=row['Vaccine'],
                    line=dict(color="#cfd8dc", width=2)
                )

            # 2. Draw the dots (Candy) - Deep Teal
            fig_pop.add_trace(go.Scatter(
                x=region_data['Coverage_Rate'],
                y=region_data['Vaccine'],
                mode='markers+text',
                marker=dict(color='#2E86AB', size=14, line=dict(width=2, color='white')), # Teal with white border
                text=region_data['Coverage_Rate'].astype(str) + '%',
                textposition="middle right",
                name=region_name,
                hoverinfo='x+y'
            ))

            fig_pop.update_layout(
                title=dict(text=f"<b>{region_name}</b> Performance", font=dict(size=18, color='#333')),
                xaxis_title="Coverage Rate (%)",
                yaxis_title="",
                showlegend=False,
                height=400,
                plot_bgcolor="white",
                xaxis=dict(
                    range=[0, max(100, region_data['Coverage_Rate'].max() + 15)],
                    showgrid=True,
                    gridcolor='#f0f0f0'
                ),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            st.plotly_chart(fig_pop, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. FOOTER, DOWNLOADS & ATTRIBUTION
# -----------------------------------------------------------------------------
st.markdown("---")

# Convert dataframe to CSV
csv_data = df.to_csv(index=False).encode('utf-8')

f1, f2 = st.columns([1, 4])

with f1:
    st.download_button(
        label="📥 Download Data CSV",
        data=csv_data,
        file_name="vaccination_data.csv",
        mime="text/csv",
        use_container_width=True
    )

with f2:
    st.markdown(
        """
        <div style='text-align: right; color: #666; font-size: 0.85em;'>
        <b>Data Source:</b> <a href="https://openstat.psa.gov.ph/" target="_blank" style="color:#2E86AB; text-decoration:none;">OpenStat PSA</a><br>
        <i>Dashboard created for Health Informatics (ITE3) Finals.</i>
        </div>
        """,
        unsafe_allow_html=True
    )
