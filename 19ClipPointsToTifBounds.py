import os
import glob
import geopandas as gpd
import rasterio as rio
from shapely.geometry import box

"""
This script clips points from a shapefile to the bounds of raster files
and saves the clipped points to new shapefiles.

Usage:
- Use this script when you have a set of raster files and you want to extract points 
  from a shapefile that fall within the spatial extent of each raster.
- The script outputs a new shapefile for each raster, containing only the points that 
  lie within the bounds of that raster.
"""

# Gather all the raster files to be used for clipping the point file
allfiles = glob.glob('/workspace/data/AllMapsInOneFolder/decompressed/geokeyed/Red/*.tif')

# Load the point vector file (shapefile) using GeoPandas
pointfile_path = '/workspace/data/AllMapsInOneFolder/Points/PointsMoreArable.shp'

# Debugging: Check if the point file exists
print(f"Checking if point file exists: {pointfile_path}")
if not os.path.exists(pointfile_path):
    raise FileNotFoundError(f"Point file not found: {pointfile_path}")
else:
    print(f"Point file found: {pointfile_path}")

# Read the point file
pointfile = gpd.read_file(pointfile_path)

# Ensure the output directory exists
output_dir = '/workspace/data/AllMapsInOneFolder/Points/MoreArableClipped'
os.makedirs(output_dir, exist_ok=True)

# Check if the input GeoDataFrame contains point geometries
if not all(pointfile.geometry.type == 'Point'):
    raise ValueError("The input shapefile does not contain point geometries.")

# Iterate over each raster file
for file in allfiles:
    print('Current file:', file)
    
    # Extract the base name (without extension) from the file path
    name = os.path.splitext(os.path.basename(file))[0]
    
    # Open the raster file using Rasterio to get its bounding box
    with rio.open(file) as src:
        bounds = src.bounds
        print(f"Bounds for {file}: {bounds}")
        
        # Create a bounding box polygon from the raster bounds
        bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
        
        # Clip the points to the bounding box of the raster
        clipped_points = pointfile[pointfile.geometry.within(bbox)]
        
        # Check if the clipped_points DataFrame is empty
        if clipped_points.empty:
            print(f"No points found within the bounds of {file}. Skipping.")
            continue
        
        # Define the output path for the clipped shapefile
        output_path = os.path.join(output_dir, f"{name}.shp")
        
        # Save the clipped points to a new shapefile
        clipped_points.to_file(output_path)
        print(f"Clipped points saved to {output_path}")