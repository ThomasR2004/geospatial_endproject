import osmnx as ox
import geopandas as gpd

def get_city_neighbourhoods(city_name, country="Netherlands"):
    city_gdf = ox.geocode_to_gdf(f"{city_name}, {country}")
    city_geom = city_gdf.geometry.iloc[0]

    tags = {
    "boundary": "administrative",
    "admin_level": ["9", "10"]
    }

    areas = ox.features_from_polygon(city_geom, tags)

    areas = areas[
        (areas.geometry.type.isin(["Polygon", "MultiPolygon"])) &
        (areas["name"].notna()) &
        (areas.within(city_geom))
    ].copy()

    areas["city"] = city_name
    return areas[["name", "geometry", "city"]].reset_index(drop=True)



Rotterdam_neighbourhoods = get_city_neighbourhoods("Rotterdam")




import matplotlib.pyplot as plt
import osmnx as ox

def plot_city_subareas(city_name, subareas_gdf, country="Netherlands"):
    # Get city boundary
    city_gdf = ox.geocode_to_gdf(f"{city_name}, {country}")
    
    # Project everything to a metric CRS
    city_gdf = city_gdf.to_crs(epsg=28992)
    subareas_gdf = subareas_gdf.to_crs(epsg=28992)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Plot city boundary
    city_gdf.boundary.plot(
        ax=ax,
        linewidth=2,
        edgecolor="black",
        label="City boundary"
    )
    
    # Plot subareas
    subareas_gdf.assign(dummy=1).plot(
        ax=ax,
        column="dummy",
        categorical=True,
        legend=False,
        alpha=0.6,
        edgecolor="black"
    )

    # Label subareas (optional but useful for debugging)
    for idx, row in subareas_gdf.iterrows():
        centroid = row.geometry.centroid
        ax.text(
            centroid.x,
            centroid.y,
            row["name"],
            fontsize=7,
            ha="center"
        )
    
    ax.set_title(f"Administrative subareas of {city_name}", fontsize=14)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

plot_city_subareas("Rotterdam", Rotterdam_neighbourhoods)