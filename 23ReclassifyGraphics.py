#Lorenzo modify this script so it reclassi the graphics of all files in the 
#output_dir = "/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps"



import os
import numpy as np
from osgeo import gdal

# Specify the in-/output directory
input_dir_1 = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps'
output_dir_1 = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext'

# Ensure output directory exists
os.makedirs(output_dir_1, exist_ok=True)

def reclassify_raster(input_raster, output_raster):
    # Open the input raster
    src_ds = gdal.Open(input_raster)
    if src_ds is None:
        print(f"Unable to open {input_raster}")
        return

    # Read the raster data as a numpy array
    band = src_ds.GetRasterBand(1)
    data = band.ReadAsArray()

    # Reclassify class 2 to 0
    data[data == 2] = 0

    # Create the output raster
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_raster, src_ds.RasterXSize, src_ds.RasterYSize, 1, band.DataType)
    out_ds.SetGeoTransform(src_ds.GetGeoTransform())
    out_ds.SetProjection(src_ds.GetProjection())
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(data)
    out_band.FlushCache()

    # Close the datasets
    src_ds = None
    out_ds = None

# Iterate over the files in the input directory
for file_name in os.listdir(input_dir_1):
    file_path_in = os.path.join(input_dir_1, file_name)
    # Check if the file is a TIFF
    if file_name.endswith('.tif'):
        base_name = os.path.splitext(file_name)[0]
        
        # Construct the output file path
        file_path_out = os.path.join(output_dir_1, f"{base_name}.tif")
        
        # Reclassify the raster
        print(f"Starting reclassification for {file_name}")
        try:
            reclassify_raster(file_path_in, file_path_out)
            print(f"Reclassification completed for {file_name}")
        except Exception as e:
            print(f"Error during reclassification for {file_name}: {e}")
        
        # Print finished message
        print(f"Finished processing {file_name}")

# Print completion message
print("All files processed.")