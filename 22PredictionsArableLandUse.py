import os
import numpy as np
from osgeo import gdal_array
import rasterio as rio
import pandas as pd
import xgboost as xgb
import time

# Start time measurement
start_time = time.time()

# Set directories
base_dir = '/workspace/data/AllMapsInOneFolder/decompressed/geokeyed/'
output_dir = '/workspace/data/AllMapsInOneFolder/PredictionsArable/'

# Load XGBoost model
try:
    model_file_path = '/workspace/data/XGBMoreArable/xgboost_modelArable.json'
    xgboost_modelArable = xgb.Booster()
    xgboost_modelArable.load_model(model_file_path)
    print(f"Model loaded successfully from {model_file_path}")
except Exception as e:
    print(f"Failed to load model: {e}")
    exit(1)


# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Define band order expected by model
correct_order = ['Red', 'Green', 'Blue', 'Intensity', 'Hue', 'Saturation', 'B_R', 'B_G', 'G_R', 'MinFG3', 
                'MedianFR19', 'GaussR10', 'StDevFR19', 'StDevFI49', 'MedianB_R5', 'AverageG', 'AverageH', 
                'AverageS', 'AverageB', 'AverageI', 'AverageR']

# Get reference folder and files
ref_folder = os.path.join(base_dir, correct_order[0])  # Use 'Red' as reference
tif_files = sorted([f for f in os.listdir(ref_folder) if f.endswith('.tif')])
total_files = len(tif_files)

print(f"Found {total_files} files to process")
processed_files = 0

# Process each file
for tif_name in tif_files:
    processed_files += 1
    print(f"\nProcessing file {processed_files}/{total_files}: {tif_name}")
    
    output_file = os.path.join(output_dir, tif_name)
    if os.path.exists(output_file):
        print(f"Output file exists, skipping: {tif_name}")
        continue

    try:
        # Read first band to get dimensions
        ref_path = os.path.join(ref_folder, tif_name)
        with rio.open(ref_path) as src:
            profile = src.profile
            tif_height, tif_width = src.height, src.width

        # Load all bands in correct order
        bands_list = []
        no_data_mask = None
        
        for band_name in correct_order:
            band_path = os.path.join(base_dir, band_name, tif_name)
            print(f"Loading band: {band_name}")
            band = gdal_array.LoadFile(band_path)
            bands_list.append(band)
            
            if no_data_mask is None:
                no_data_mask = (band == -32768)
            else:
                no_data_mask = no_data_mask | (band == -32768)

        # Process bands
        bands_array = np.array(bands_list)
        bands_reshaped = bands_array.reshape(len(correct_order), tif_height * tif_width).T
        xgb_data = pd.DataFrame(bands_reshaped, columns=correct_order)
        d_data = xgb.DMatrix(xgb_data, feature_names=correct_order)
        
        # Predict and reshape
        predictions = xgboost_modelArable.predict(d_data)
        pred = predictions.reshape(tif_height, tif_width)
        
        if no_data_mask is not None:
            pred[no_data_mask] = -32768

        # Save prediction
        profile.update(dtype=rio.int16, count=1, nodata=-32768)
        with rio.open(output_file, 'w', **profile) as dst:
            dst.write(pred, 1)
        
        print(f"Successfully processed: {tif_name}")

    except Exception as e:
        print(f"Error processing {tif_name}: {str(e)}")
        continue

print(f"\nProcessing complete. Total time: {time.time() - start_time:.2f} seconds")
print(f"Successfully processed {processed_files} files out of {total_files}")