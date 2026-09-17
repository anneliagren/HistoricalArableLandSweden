import os
import glob
from osgeo import gdal, osr

# Set input file paths
intiff1 = "/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/North/LandUseNoGraphicsNorth.tif"
intiff2 = "/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/MidNorth/LandUseNoGraphicsMidNorth.tif"
intiff3 = "/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/MidSouth/LandUseNoGraphicsMidSouth.tif"
intiff4 = "/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/South/LandUseNoGraphicsSouth.tif"

# Set paths
other_layer = '/workspace/data/NMD2023_basskikt_v0_1/NMD2023bas_v0_1.tif'
output_base_dir = '/workspace/data/Mosaics'

# Create the output base directory if it doesn't exist
os.makedirs(output_base_dir, exist_ok=True)

# Open the base layer to get exact pixel grid parameters
base_ds = gdal.Open(other_layer)
base_gt = base_ds.GetGeoTransform()
base_srs = base_ds.GetProjection()

# Get exact pixel grid parameters from base layer
pixel_width = base_gt[1]   # X pixel size
pixel_height = base_gt[5]  # Y pixel size (usually negative)
origin_x = base_gt[0]      # X coordinate of upper-left corner
origin_y = base_gt[3]      # Y coordinate of upper-left corner

# Calculate exact extent from base layer
width = base_ds.RasterXSize
height = base_ds.RasterYSize
extent = [
    origin_x,                           # xmin
    origin_y + height * pixel_height,  # ymin
    origin_x + width * pixel_width,    # xmax  
    origin_y                           # ymax
]

print(f"Base layer grid parameters:")
print(f"  Origin: ({origin_x:.2f}, {origin_y:.2f})")
print(f"  Pixel size: {pixel_width:.2f} x {pixel_height:.2f}")
print(f"  Dimensions: {width} x {height}")
print(f"  Extent: {extent}")

# Define target CRS (use base layer's CRS)
target_srs = osr.SpatialReference()
target_srs.ImportFromWkt(base_srs)

# Create list of input files for processing
input_files = [intiff1, intiff2, intiff3, intiff4]
region_names = ['North', 'MidNorth', 'MidSouth', 'South']

# Process each input file
for i, input_tif in enumerate(input_files):
    region = region_names[i]
    output_folder = os.path.join(output_base_dir, region)
    os.makedirs(output_folder, exist_ok=True)
    
    # Create output filename
    output_tif = os.path.join(output_folder, os.path.basename(input_tif))
    
    print(f"Processing {region}: {os.path.basename(input_tif)}...")
    
    # Warp to exact same pixel grid as base layer
    warp_options = gdal.WarpOptions(
        dstSRS=target_srs,
        outputBounds=extent,
        xRes=abs(pixel_width),   # Use exact pixel width from base
        yRes=abs(pixel_height),  # Use exact pixel height from base
        targetAlignedPixels=True,  # Align pixels to target grid
        resampleAlg=gdal.GRA_Mode,
        outputType=gdal.GDT_Byte,
        creationOptions=['COMPRESS=LZW']
    )
    
    gdal.Warp(output_tif, input_tif, options=warp_options)
    
    # Verify alignment by checking geotransform
    output_ds = gdal.Open(output_tif)
    output_gt = output_ds.GetGeoTransform()
    
    print(f"  Base layer geotransform: {base_gt}")
    print(f"  Output geotransform:     {output_gt}")
    
    # Check if they match (within floating point precision)
    if abs(base_gt[0] - output_gt[0]) < 1e-6 and abs(base_gt[3] - output_gt[3]) < 1e-6:
        print(f"  ✓ Perfect pixel alignment achieved!")
    else:
        print(f"  ⚠ Warning: Pixel alignment may not be perfect")
    
    output_ds = None
    print(f"  Completed: {output_tif}")

base_ds = None
print("All files processed successfully with exact pixel alignment!")