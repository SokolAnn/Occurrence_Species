import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from io import BytesIO
import requests

# Page config
st.set_page_config(
    page_title="Lion Conservation Monitor 🦁",
    page_icon="🦁",
    layout="wide"
)

# Function to load data from GitHub
@st.cache_data
def load_data():
    try:
        # Use the raw GitHub URL
        excel_url = "https://raw.githubusercontent.com/SokolAnn/Occurrence_Species/main/occurrence_filtered_final.xlsx"
        response = requests.get(excel_url)
        df = pd.read_excel(BytesIO(response.content))
        df = df.rename(columns={'lon_keep': 'longitude', 'lat_keep': 'latitude'})
        return df.dropna(subset=['longitude', 'latitude'])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar filters
st.sidebar.title("🔍 Filters")

# Quick search
search_term = st.sidebar.text_input("Quick Search")

# Taxonomy filters
st.sidebar.subheader("🧬 Taxonomy")
phylum_filter = st.sidebar.selectbox("Phylum", ["All"] + sorted(df["phylum"].unique().tolist()))
class_filter = st.sidebar.selectbox("Class", ["All"] + sorted(df["class"].unique().tolist()))
species_filter = st.sidebar.selectbox("Species", ["All"] + sorted(df["species"].unique().tolist()))

# Location filters
st.sidebar.subheader("🌍 Location")
continent_filter = st.sidebar.selectbox("Continent", ["All"] + sorted(df["continent"].unique().tolist()))
country_filter = st.sidebar.selectbox("Country", ["All"] + sorted(df["countryCode"].unique().tolist()))
state_filter = st.sidebar.selectbox("State", ["All"] + sorted(df["state"].unique().tolist()))

# Status filter
st.sidebar.subheader("🏷️ Status")
iucn_filter = st.sidebar.selectbox("IUCN Status", ["All"] + sorted(df["iucnRedListCategory"].unique().tolist()))

# Apply filters
filtered_df = df.copy()

if search_term:
    mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
    filtered_df = filtered_df[mask]

if phylum_filter != "All":
    filtered_df = filtered_df[filtered_df["phylum"] == phylum_filter]
if class_filter != "All":
    filtered_df = filtered_df[filtered_df["class"] == class_filter]
if species_filter != "All":
    filtered_df = filtered_df[filtered_df["species"] == species_filter]
if continent_filter != "All":
    filtered_df = filtered_df[filtered_df["continent"] == continent_filter]
if country_filter != "All":
    filtered_df = filtered_df[filtered_df["countryCode"] == country_filter]
if state_filter != "All":
    filtered_df = filtered_df[filtered_df["state"] == state_filter]
if iucn_filter != "All":
    filtered_df = filtered_df[filtered_df["iucnRedListCategory"] == iucn_filter]

# Main content
st.title("Lion Conservation Monitor 🦁")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Species 🦁", len(filtered_df["species"].unique()))
with col2:
    st.metric("Observations 📍", len(filtered_df))
with col3:
    st.metric("Countries 🌍", len(filtered_df["countryCode"].unique()))
with col4:
    most_common_status = filtered_df["iucnRedListCategory"].mode()[0] if not filtered_df.empty else "N/A"
    st.metric("Most Common Status ⚠️", most_common_status)

# Tabs
tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📊 Data", "ℹ️ Info"])

with tab1:
    # Create map
    m = folium.Map(location=[0, 0], zoom_start=2)
    
    # Add markers
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=6,
            popup=f"""
                <strong>🦁 {row["species"]}</strong><br>
                🧬 {row["phylum"]} - {row["class"]}<br>
                📍 {row["county"]}, {row["state"]}, {row["countryCode"]}<br>
                🌱 Landcover: {row["landcover"]}<br>
                ⚠️ IUCN: {row["iucnRedListCategory"]}
            """,
            color={"VU": "yellow", "EN": "orange", "CR": "red"}.get(row["iucnRedListCategory"], "blue"),
            fill=True,
            fill_opacity=0.7
        ).add_to(m)
    
    folium_static(m)

with tab2:
    st.dataframe(filtered_df)
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data",
        data=csv,
        file_name="wildlife-data.csv",
        mime="text/csv"
    )

with tab3:
    st.header("About This Dataset")
    st.subheader("🦁 Wildlife Occurrence Data")
    st.write("This dataset contains wildlife occurrence records with the following information:")
    st.markdown("""
    - 🧬 Taxonomic classification from Phylum to Species
    - 🌍 Geographic location including continent, country, state, and county
    - 🏷️ IUCN conservation status
    - 📍 Precise coordinates of sightings
    - 🌱 Landcover type
    """)
    
    st.subheader("📍 How to Use")
    st.markdown("""
    - Use the quick search to find specific records
    - Apply filters to narrow down the data
    - View locations on the map
    - Download filtered data for further analysis
    """)