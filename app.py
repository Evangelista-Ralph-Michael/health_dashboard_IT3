import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Health Data Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. CSS STYLING (THE FIX)
# -----------------------------------------------------------------------------
# This CSS forces the app into a Clean Medical Light Theme, overriding Dark Mode
st.markdown("""
    <style>
        /* 1. Force Main Background to White */
        .stApp {
            background-color: #FFFFFF;
        }

        /* 2. Force Sidebar Background to Light Grey */
        section[data-testid="stSidebar"] {
            background-color: #F7F9FB;
            border-right: 1px solid #E0E0E0;
        }

        /* 3. Fix Text Colors (Force Dark Text) */
        h1, h2, h3, h4, h5, h6, p, li, div {
            color: #212529 !important;
        }
        
        /* 4. Fix Sidebar Input Labels (Make them visible) */
        .stMultiSelect label, .stSelectbox label {
            color: #333333 !important;
            font-weight: 600;
        }
        
        /* 5. Style the KPI Cards */
        div[data-testid="stMetric"] {
            background-color: #F0F4F8; /* Soft Blue-Grey */
            border: 1px solid #D1D9E6;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        div[data-testid="stMetricLabel"] {
            color: #555555 !important;
            font-size: 0.9rem;
        }
        
        div[data-testid="stMetricValue"] {
            color: #2E86AB !important; /* Medical Teal */
            font-weight: 700;
        }

        /* 6. Style the Blue Info Banner */
        .info-box {
            background-color: #E1F5FE;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #0288D1;
            margin-bottom: 20px;
            color: #01579B !important;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Load the dataset
    df = pd.read_csv("vaccination_data.csv")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("The file 'vaccination_data.csv' was not found.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=50) # Placeholder Medical Icon
    st.title("Dashboard Controls")
    
    # A. Region Filter
    all_regions = sorted(df['Region'].unique())
    st.subheader("📍 Geography")
    selected_regions = st.multiselect(
        "Select Regions:",
        options=all_regions,
        default=all_regions[:3]
    )

    # B. Category Filter
    st.subheader("📊 Data Type")
    chart_categories = ["Basic Antigen", "Summary Indicator"]
    selected_category = st.selectbox(
        "Select Category:",
        options=chart_categories,
        index=0
    )
    
    st.markdown("---")
    st.caption("Health Informatics Finals")

# -----------------------------------------------------------------------------
# 5. DATA LOGIC
# -----------------------------------------------------------------------------
df_filtered = df[df['Region'].isin(selected_regions)]
df_kpi = df_filtered[df_filtered['Category'] == "Demographic"]
df_charts = df_filtered[df_filtered['Category'] == selected_category]

# -----------------------------------------------------------------------------
# 6. MAIN DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

# Title
st.title("🇵🇭 Philippine Vaccination Coverage (2022)")

# Custom HTML Info Banner (Styled by CSS above)
st.markdown(f"""
    <div class="info-box">
        Analysis of immunization coverage for children aged 12-23 months.<br>
        Currently viewing data for: <b>{selected_category}</b>
    </div>
""", unsafe_allow_html=True)

# --- KPIs ---
st.subheader("📈 Key Performance Indicators")

if not df_kpi.empty:
    total_children = df_kpi['Coverage_Rate'].sum()
    avg_coverage = df_charts['Coverage_Rate'].mean()
    
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(label="Target Population (Thousands)", value=f"{total_children:,.0f}k")
    with kpi2:
        st.metric(label="Avg. Coverage Rate", value=f"{avg_coverage:.2f}%")
    with kpi3:
         max_val = df_charts['Coverage_Rate'].max()
         st.metric(label="Highest Recorded Rate", value=f"{max_val:.2f}%")
else:
    st.warning("No demographic data available for the selected filters.")

st.markdown("---")

# --- CHARTS ---
col1, col2 = st.columns([1, 1])

# CHART 1: Bar Chart
with col1:
    st.subheader(f"Regional Comparison")
    df_bar = df_charts.groupby('Region')['Coverage_Rate'].mean().reset_index().sort_values("Coverage_Rate", ascending=False)
    
    fig_bar = px.bar(
        df_bar,
        x='Region',
        y='Coverage_Rate',
        color='Coverage_Rate',
        color_continuous_scale='Teal',
        text_auto='.1f',
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", # Transparent background
        paper_bgcolor="rgba(0,0,0,0)", 
        font=dict(color="black"), # Force text black
        coloraxis_showscale=False,
        yaxis=dict(showgrid=True, gridcolor='#eee'),
        margin=dict(l=0, r=0, t=30, b=0)
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
        color_continuous_scale="Blues",
        aspect="auto"
    )
    fig_heatmap.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="black"), # Force text black
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# --- LOLLIPOP CHARTS ---
st.subheader("🔍 Detailed Regional Breakdown")

if not selected_regions:
    st.info("👈 Please select at least one region in the sidebar.")
else:
    for region_name in selected_regions:
        with st.container():
            region_data = df_charts[df_charts['Region'] == region_name].copy()
            region_data = region_data.sort_values(by="Coverage_Rate", ascending=True)

            fig_pop = go.Figure()

            # Sticks (Grey)
            for i, row in region_data.iterrows():
                fig_pop.add_shape(
                    type="line",
                    x0=0, y0=row['Vaccine'],
                    x1=row['Coverage_Rate'], y1=row['Vaccine'],
                    line=dict(color="#B0BEC5", width=2)
                )

            # Dots (Teal)
            fig_pop.add_trace(go.Scatter(
                x=region_data['Coverage_Rate'],
                y=region_data['Vaccine'],
                mode='markers+text',
                marker=dict(color='#0288D1', size=14, line=dict(width=2, color='white')),
                text=region_data['Coverage_Rate'].astype(str) + '%',
                textposition="middle right",
                name=region_name,
                hoverinfo='x+y'
            ))

            fig_pop.update_layout(
                title=dict(text=f"<b>{region_name}</b> Performance", font=dict(size=18, color='#333')),
                xaxis_title="Coverage Rate (%)",
                xaxis=dict(showgrid=True, gridcolor='#f0f0f0', range=[0, 115]),
                yaxis_title="",
                showlegend=False,
                height=350,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="black"),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig_pop, use_container_width=True)

# -----------------------------------------------------------------------------
# 7. DOWNLOADS
# -----------------------------------------------------------------------------
st.markdown("---")
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Data CSV",
    data=csv_data,
    file_name="vaccination_data.csv",
    mime="text/csv",
)
