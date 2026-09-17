import os
os.environ["WBT_LINUX"] = "MUSL"
import numpy as np
import rasterio

# Set input folder paths
folder_path_G = '/workspace/data/AllMapsInOneFolder/decompressed/geokeyed/Green'
folder_path = '/workspace/data/AllMapsInOneFolder/decompressed/geokeyed/'

# Create output folder
output_AverageG_folder = os.path.join(folder_path, 'AverageG')

# Ensure output folder exists
os.makedirs(output_AverageG_folder, exist_ok=True)

# Use os.listdir to get all files in the directory
files_in_directory = os.listdir(folder_path_G)

# Filter out the files to only have files with .tif extension
tif_files = [file for file in files_in_directory if file.endswith('.tif')]

# Now you can iterate over the tif files
for tif_file in tif_files:
    file_path = os.path.join(folder_path_G, tif_file)
    # Open the tif file and convert it to numpy array
    with rasterio.open(file_path) as src:
        img_array = src.read(1)
        
        print(f"Processing file: {file_path}")
        print(f"Original shape: {img_array.shape}, dtype: {img_array.dtype}")

        # Check if the array is empty
        if img_array.size == 0:
            print(f"Warning: {file_path} is empty. Skipping.")
            continue

        # Handle nodata values (-32768)
        img_array = np.where(img_array == -32768, np.nan, img_array)

        # Calculate the average of the numpy array, ignoring NaNs
        average = np.nanmean(img_array)

        # Create a new numpy array with the same shape as the original but filled with the average value
        average_array = np.full(img_array.shape, average)

        # Copy the metadata from the source file
        metadata = src.meta.copy()

        # Update the metadata to reflect the number of bands and the data type
        metadata.update({
            'count': 1,
            'dtype': str(average_array.dtype),
            'crs': 'EPSG:3021',
            'nodata': -32768  # Set nodata value in metadata
        })

        # Write the average array out as a new tif file
        output_file_path = os.path.join(output_AverageG_folder, tif_file)
        with rasterio.open(output_file_path, 'w', **metadata) as dst:
            dst.write(average_array, 1)

        print(f"Output file written to: {output_file_path}")