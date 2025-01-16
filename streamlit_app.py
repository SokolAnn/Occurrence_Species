import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import folium_static
import plotly.express as px
from PIL import Image

# Set page config
st.set_page_config(
    page_title="Threatened Species Explorer 🦁",
    page_icon="🦁",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .stSelectbox {margin-bottom: 1rem;}
    .stButton>button {
        background-color: #605ca8;
        color: white;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

def get_unique_values(df, column):
    """Get unique values from a column, properly handling mixed types and NaN values"""
    # Get unique values and convert to list
    unique_vals = df[column].unique()
    # Convert all values to strings, handling NaN values
    unique_vals = [str(x) for x in unique_vals if pd.notna(x)]
    # Sort the list
    return sorted(unique_vals)

@st.cache_data
def load_data():
    """Load and preprocess the wildlife data"""
    df = pd.read_excel("occurrence_filtered_final.xlsx")
    df = df.rename(columns={'lon_keep': 'longitude', 'lat_keep': 'latitude'})
    
    # Ensure coordinates are numeric
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    
    # Convert categorical columns to string type, handling NaN values
    string_columns = ['phylum', 'class', 'species', 'continent', 'countryCode', 
                     'state', 'county', 'landcover', 'iucnRedListCategory']
    
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)
            # Replace 'nan' with empty string
            df[col] = df[col].replace('nan', '')
    
    # Remove rows with invalid coordinates
    df = df.dropna(subset=['longitude', 'latitude'])
    
    # Filter out invalid coordinates
    df = df[
        (df['latitude'] >= -90) & (df['latitude'] <= 90) &
        (df['longitude'] >= -180) & (df['longitude'] <= 180)
    ]
    
    return df

# Sidebar filters
def create_filters(df):
    with st.sidebar:
        st.title("🔍 Filters")
        
        # Quick search
        search = st.text_input("Quick Search", placeholder="Search any field...")
        
        # Taxonomy section
        st.header("🧬 Taxonomy")
        phylum = st.selectbox("Phylum", ["All"] + get_unique_values(df, 'phylum'))
        class_ = st.selectbox("Class", ["All"] + get_unique_values(df, 'class'))
        species = st.selectbox("Species", ["All"] + get_unique_values(df, 'species'))
        
        # Location section
        st.header("🌍 Location")
        continent = st.selectbox("Continent", ["All"] + get_unique_values(df, 'continent'))
        country = st.selectbox("Country", ["All"] + get_unique_values(df, 'countryCode'))
        state = st.selectbox("State", ["All"] + get_unique_values(df, 'state'))
        county = st.selectbox("County", ["All"] + get_unique_values(df, 'county'))
        landcover = st.selectbox("Landcover", ["All"] + get_unique_values(df, 'landcover'))
        
        # Status section
        st.header("🏷️ Status")
        iucn = st.selectbox("IUCN Status", ["All"] + get_unique_values(df, 'iucnRedListCategory'))
        
        # Reset button
        if st.button("🔄 Reset All"):
            st.experimental_rerun()
            
    return search, phylum, class_, species, continent, country, state, county, landcover, iucn

def filter_data(df, search, phylum, class_, species, continent, country, state, county, landcover, iucn):
    """Apply filters to the dataframe"""
    if search:
        search = search.lower()
        df = df[
            df['species'].str.lower().str.contains(search, na=False) |
            df['phylum'].str.lower().str.contains(search, na=False) |
            df['class'].str.lower().str.contains(search, na=False) |
            df['state'].str.lower().str.contains(search, na=False) |
            df['countryCode'].str.lower().str.contains(search, na=False) |
            df['county'].str.lower().str.contains(search, na=False) |
            df['landcover'].str.lower().str.contains(search, na=False) |
            df['iucnRedListCategory'].str.lower().str.contains(search, na=False)
        ]
    
    if phylum != "All": df = df[df['phylum'] == phylum]
    if class_ != "All": df = df[df['class'] == class_]
    if species != "All": df = df[df['species'] == species]
    if continent != "All": df = df[df['continent'] == continent]
    if country != "All": df = df[df['countryCode'] == country]
    if state != "All": df = df[df['state'] == state]
    if county != "All": df = df[df['county'] == county]
    if landcover != "All": df = df[df['landcover'] == landcover]
    if iucn != "All": df = df[df['iucnRedListCategory'] == iucn]
    
    return df

def create_map(df):
    """Create a folium map with the filtered data"""
    # If dataset is too large, sample it
    MAX_POINTS = 1000
    if len(df) > MAX_POINTS:
        st.warning(f"Showing a sample of {MAX_POINTS} points out of {len(df)} total points for better performance.")
        df = df.sample(n=MAX_POINTS, random_state=42)
    
    # Calculate center of the map based on data points
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    # Create the base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4,
                  tiles='CartoDB positron', control_scale=True)
    
    # Create color dictionary for IUCN categories
    colors = {
        'LC': '#2ecc71',     # Safe green
        'NT': '#f1c40f',     # Warning yellow
        'VU': '#e67e22',     # Vulnerable orange
        'EN': '#e74c3c',     # Endangered red
        'CR': '#9b59b6'      # Critical purple
    }
    
    # Create marker cluster for better performance with many points
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)
    
    # Add markers for each point
    for idx, row in df.iterrows():
        try:
            # Create popup content
            popup_text = f"""
                <div style='font-family: Arial; font-size: 12px;'>
                    <strong style='font-size: 14px;'>🦁 {row['species']}</strong><br>
                    🧬 {row['phylum']} - {row['class']}<br>
                    📍 {row['county']}, {row['state']}, {row['countryCode']}<br>
                    🌱 Landcover: {row['landcover']}<br>
                    ⚠️ IUCN: {row['iucnRedListCategory']}
                </div>
            """
            
            # Create the circle marker
            folium.CircleMarker(
                location=[float(row['latitude']), float(row['longitude'])],
                radius=6,
                popup=folium.Popup(popup_text, max_width=300),
                color=colors.get(row['iucnRedListCategory'].strip(), '#95a5a6'),
                fill=True,
                fillOpacity=0.7,
                weight=2
            ).add_to(marker_cluster)
        except Exception as e:
            continue
    
    # Add a legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
                padding: 10px; border-radius: 5px; border: 2px solid grey; font-family: Arial">
        <h4 style="margin-bottom: 10px;">IUCN Status</h4>
        <div><span style="color: #2ecc71;">●</span> Least Concern (LC)</div>
        <div><span style="color: #f1c40f;">●</span> Near Threatened (NT)</div>
        <div><span style="color: #e67e22;">●</span> Vulnerable (VU)</div>
        <div><span style="color: #e74c3c;">●</span> Endangered (EN)</div>
        <div><span style="color: #9b59b6;">●</span> Critically Endangered (CR)</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    try:
        # Load data
        df = load_data()
        
        # Create filters
        filters = create_filters(df)
        
        # Apply filters
        filtered_df = filter_data(df, *filters)
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📊 Data", "ℹ️ Info"])
        
        with tab1:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Species 🦁", len(filtered_df['species'].unique()))
            with col2:
                st.metric("Observations 📍", len(filtered_df))
            with col3:
                st.metric("Countries 🌍", len(filtered_df['countryCode'].unique()))
            with col4:
                most_common_status = filtered_df['iucnRedListCategory'].mode()[0]
                st.metric("Most Common Status ⚠️", most_common_status)
            
            # Map
            st.write("### Interactive Map")
            m = create_map(filtered_df)
            folium_static(m, width=1200, height=600)
        
        with tab2:
            st.write("### Filtered Data")
            
            # Download button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data",
                data=csv,
                file_name="wildlife-data.csv",
                mime="text/csv"
            )
            
            # Display dataframe
            st.dataframe(filtered_df, use_container_width=True)
        
        with tab3:
            st.write("### About This Dataset")
            st.write("#### 🦁 Wildlife Occurrence Data")
            st.write("This dataset contains wildlife occurrence records with the following information:")
            
            st.markdown("""
            * 🧬 Taxonomic classification from Phylum to Species
            * 🌍 Geographic location including continent, country, state, and county
            * 🏷️ IUCN conservation status
            * 📍 Precise coordinates of sightings
            * 🌱 Landcover type
            """)
            
            st.write("#### 📍 How to Use")
            st.markdown("""
            * Use the quick search to find specific records
            * Apply filters to narrow down the data
            * View locations on the map
            * Download filtered data for further analysis
            """)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()