import pandas as pd
import geopandas as gpd
import osmnx as ox
from pyrosm import OSM
from scipy.stats import entropy
import warnings

# Suppress the pyrosm ChainedAssignment warning to keep output clean
warnings.filterwarnings("ignore", category=FutureWarning)

# --- CONFIGURATION ---
PBF_FILES = {
    "Amsterdam": "noord-holland-260108.osm.pbf",
    "Utrecht": "utrecht-260108.osm.pbf"
}


# Updated queries to be more specific for the geocoder
DISTRICTS = [
    ("Amsterdam", "Nieuw-West, Amsterdam"),
    ("Amsterdam", "Noord, Amsterdam"),
    ("Amsterdam", "Oost, Amsterdam"),
    ("Amsterdam", "West, Amsterdam"),
    ("Amsterdam", "Centrum, Amsterdam"),
    ("Amsterdam", "Zuid, Amsterdam"),
    ("Utrecht", "Binnenstad, Utrecht"),
    ("Utrecht", "Leidsche Rijn, Utrecht")
]

def calculate_district_cyclability(city_name, district_query):
    print(f"--- Analyzing {district_query} ---")
    
    # 1. GET BOUNDARY & PROJECT TO DUTCH RD NEW (EPSG:28992)
    # This ensures area is in square meters and length is in meters
    boundary_gdf = ox.geocode_to_gdf(district_query)
    
    boundary_gdf = boundary_gdf.to_crs(epsg=28992)
    district_geom = boundary_gdf.geometry.iloc[0]
    area_km2 = district_geom.area / 1_000_000
    
    # 2. INITIALIZE LOCAL OSM PARSER
    # pyrosm works in lat/lon, so use the original boundary for clipping
    boundary_latlon = boundary_gdf.to_crs(epsg=4326).geometry.iloc[0]
    osm = OSM(PBF_FILES[city_name], bounding_box=boundary_latlon)

    # --- VARIABLE 1: STREET NETWORK (Connectivity) ---
    net_edges = osm.get_network(network_type="cycling")
    
    if net_edges is not None:
        # Clip and Project to Dutch RD New for length calculation
        net_edges = net_edges.to_crs(epsg=28992)
        net_clipped = net_edges[net_edges.intersects(district_geom)]
        network_connectivity = (net_clipped.length.sum() / 1000) / area_km2
    else:
        network_connectivity = 0
        print('kapot')

    # --- VARIABLE 2 & 3: LAND USE & ACCESSIBILITY ---
    custom_filter = {"amenity": True, "shop": True, "leisure": True, "office": True}
    pois = osm.get_pois(custom_filter=custom_filter)
    
    if pois is not None:
        pois = pois.to_crs(epsg=28992)
        pois_clipped = pois[pois.intersects(district_geom)].copy()
        
        # Accessibility
        poi_density = len(pois_clipped) / area_km2

        # Diversity (Entropy)
        if not pois_clipped.empty:
            pois_clipped['category'] = pois_clipped['amenity'].fillna(pois_clipped['shop'])
            counts = pois_clipped['category'].value_counts()
            land_use_diversity = entropy(counts)
        else:
            land_use_diversity = 0
            print('kapot2')
    else:
        poi_density = 0
        land_use_diversity = 0
        print('kapot3')

    return {
        "District": district_query,
        "City": city_name,
        "Net_Connectivity": network_connectivity,
        "Land_Use_Diversity": land_use_diversity,
        "Dest_Accessibility": poi_density
    }

# --- EXECUTION & NORMALIZATION ---
results_list = []
for city, dist in DISTRICTS:
    results_list.append(calculate_district_cyclability(city, dist))
df = pd.DataFrame(results_list)

# Normalize and calculate index
for col in ["Net_Connectivity", "Land_Use_Diversity", "Dest_Accessibility"]:
    df[f"{col}_norm"] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())

w1, w2, w3 = 0.4, 0.3, 0.3
df['Cyclability_Index'] = (df['Net_Connectivity_norm']*w1 + 
                           df['Land_Use_Diversity_norm']*w2 + 
                           df['Dest_Accessibility_norm']*w3)

print("\n", df[['District', 'City', 'Cyclability_Index', 'Net_Connectivity', 'Land_Use_Diversity', 'Dest_Accessibility']])