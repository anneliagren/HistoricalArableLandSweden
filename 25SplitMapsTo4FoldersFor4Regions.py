import os
import shutil
import rasterio

# Define directories
input_folder = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized'
output_folderN = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/North'
output_folderMN = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/MidNorth'
output_folderMS = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/MidSouth'
output_folderS = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/South'

# Ensure output directories exist
os.makedirs(output_folderN, exist_ok=True)
os.makedirs(output_folderMN, exist_ok=True)
os.makedirs(output_folderMS, exist_ok=True)
os.makedirs(output_folderS, exist_ok=True)

# Get list of all .tif files in the input folder
all_files = [f for f in os.listdir(input_folder) if f.endswith('.tif') and os.path.isfile(os.path.join(input_folder, f))]

# Function to get the latitude of the center of the raster
def get_latitude(file_path):
    with rasterio.open(file_path) as src:
        bounds = src.bounds
        center_latitude = (bounds.top + bounds.bottom) / 2
        return center_latitude

# Classify files based on latitude
north_files = []
midnorth_files = []
midsouth_files = []
south_files = []

print("Classifying files based on latitude...")

for file_name in all_files:
    file_path = os.path.join(input_folder, file_name)
    try:
        latitude = get_latitude(file_path)
        print(f"File: {file_name}, Latitude: {latitude}")
        
        if latitude > 7117500:  # Threshold for North in EPSG:3021
            north_files.append(file_name)
            print(f"Classified {file_name} as North")
        elif latitude < 6562500:  # Threshold for South in EPSG:3021
            south_files.append(file_name)
            print(f"Classified {file_name} as South")
        elif 6842500 <= latitude <= 7117500:  # Threshold for MidNorth in EPSG:3021
            midnorth_files.append(file_name)
            print(f"Classified {file_name} as MidNorth")
        else:  # Threshold for MidSouth in EPSG:3021
            midsouth_files.append(file_name)
            print(f"Classified {file_name} as MidSouth")
    except Exception as e:
        print(f"Error processing {file_name}: {e}")

# Move files to corresponding folders
print("Moving files to corresponding folders...")

for file_name in north_files:
    shutil.move(os.path.join(input_folder, file_name), output_folderN)
    print(f"Moved {file_name} to {output_folderN}")

for file_name in midnorth_files:
    shutil.move(os.path.join(input_folder, file_name), output_folderMN)
    print(f"Moved {file_name} to {output_folderMN}")

for file_name in midsouth_files:
    shutil.move(os.path.join(input_folder, file_name), output_folderMS)
    print(f"Moved {file_name} to {output_folderMS}")

for file_name in south_files:
    shutil.move(os.path.join(input_folder, file_name), output_folderS)
    print(f"Moved {file_name} to {output_folderS}")

print("File classification and moving completed.")